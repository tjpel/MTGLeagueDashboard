from googleapiclient.discovery import build
import pandas as pd
import tomllib
import streamlit as st

import helpers.constants as c

data_manager = None

# Scryfall rate limits: https://scryfall.com/docs/api/rate-limits
SCRYFALL_USER_AGENT = "LeagueSeason3/1.0"
SCRYFALL_MIN_INTERVAL = 0.55  # /cards/named allows 2 req/s; small margin on top
SCRYFALL_BACKOFF_SECONDS = 60  # pause after a 429, as Scryfall's error message requests
_scryfall_last_request = 0.0
_scryfall_backoff_until = 0.0

class SheetsAPI():
    SPREADSHEET_ID = '1YhdFnWXgWRSAE30sj0DtoKTUAPhreoN_NYTowyqLqAg'
    HEADER = 'Form Responses 1!A1:E1'
    PLACEMENTS_RANGE = 'Form Responses 1!A2:E10000'
    api_key = None

    def __init__(self):
        """
        with open(".streamlit/secrets.toml", "rb") as file:
            secrets = tomllib.load(file)
        """

        self.api_key = st.secrets['sheets_api']

    def authenticate_sheets(self, api_key):
        return build('sheets', 'v4', developerKey=api_key).spreadsheets()

    def get_placements(self):
        print("Fetching placements from spreadsheet...")
        sheets = self.authenticate_sheets(self.api_key)

        header_result = sheets.values().get(spreadsheetId=self.SPREADSHEET_ID, range=self.HEADER).execute()
        headers = header_result.get('values', [[]])[0]

        result = sheets.values().get(spreadsheetId=self.SPREADSHEET_ID, range=self.PLACEMENTS_RANGE).execute()
        values = [value for value in result.get('values', []) if value != []]
        print(f"Raw values count: {len(values)}")
        print(values[:3])

        if not values:
            return pd.DataFrame(columns=headers)

        n_cols = len(headers)
        rows = []
        for row in values:
            padded = (list(row) + [""] * n_cols)[:n_cols]
            rows.append(padded)

        out = pd.DataFrame(rows, columns=headers)
        print(out.head())
        return out


class DataManager():

    data = {}
    sheets = None

    def __init__(self):
        self.sheets = SheetsAPI()
        self.data["Placements by Game"] = self.sheets.get_placements()

        player_cmd = pd.read_csv(r"data/player-cmd.csv")
        player_cmd["Color Identity Textual"] = player_cmd["Color Identity"].apply(lambda x: c.COLOR_SYM_TO_NAME.get(x, x))
        self.data["Commander Info"] = player_cmd

        import os
        csv_path = "data/commanders_with_images.csv"
        player_cmd = self.data["Commander Info"]
        if os.path.exists(csv_path):
            cmd_w_img = pd.read_csv(csv_path)
            cache = cmd_w_img[["Commander", "Image"]].drop_duplicates("Commander") if "Image" in cmd_w_img.columns else cmd_w_img[["Commander"]].drop_duplicates("Commander").assign(Image=None)
            merged = player_cmd.merge(cache, on="Commander", how="left")
            need_fetch = (merged["Image"].isna() | (merged["Image"].astype(str).str.strip().eq(""))).any()
            if need_fetch:
                merged = self._fetch_and_merge_commander_images(player_cmd, cmd_w_img, csv_path)
            self.data["Commander with Images"] = merged
        else:
            self.data["Commander with Images"] = self._fetch_and_merge_commander_images(player_cmd, None, csv_path)

        player_stats = {}
        for _, row in self.data["Placements by Game"].iterrows():
            for column in ['First Place', 'Second Place', 'Third Place', 'Fourth Place']:
                player = row[column]
                if player not in player_stats:
                    player_stats[player] = {'Total Points': 0, 'Games Played': 0}
                
                # Add the placement and increment the games played
                player_stats[player]['Total Points'] += c.PLACEMENT[column]
                player_stats[player]['Games Played'] += 1

        placements_by_player = pd.DataFrame(data=player_stats).T
        if not placements_by_player.empty:
            placements_by_player["Average Placement"] = placements_by_player["Total Points"] / placements_by_player["Games Played"]
            placements_by_player = placements_by_player.merge(player_cmd, left_on=placements_by_player.index, right_on="Player")[
                ["Player", "Total Points", "Games Played", "Average Placement"]
            ].set_index("Player", drop=True)
        self.data["Placements by Player"] = placements_by_player

    def _fetch_and_merge_commander_images(self, player_cmd, existing_df, csv_path):
        import asyncio
        import time
        try:
            import scrython
        except ImportError:
            out = player_cmd.copy()
            out["Image"] = None
            out.to_csv(csv_path, index=False)
            return out
        # Scrython (aiohttp) needs an event loop; Streamlit runs in a thread that has none
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        commanders_to_fetch = list(player_cmd["Commander"].unique())
        if existing_df is not None and "Image" in existing_df.columns:
            filled = existing_df["Image"].notna() & existing_df["Image"].astype(str).str.strip().ne("")
            have = set(existing_df.loc[filled, "Commander"].unique())
            commanders_to_fetch = [x for x in commanders_to_fetch if x not in have]
        if not commanders_to_fetch:
            if existing_df is not None:
                return player_cmd.merge(
                    existing_df[["Commander", "Image"]].drop_duplicates("Commander"),
                    on="Commander",
                    how="left",
                )
            out = player_cmd.copy()
            out["Image"] = None
            return out
        global _scryfall_backoff_until, _scryfall_last_request
        # Scryfall asks clients to identify themselves via User-Agent
        if hasattr(scrython, "set_user_agent"):
            scrython.set_user_agent(SCRYFALL_USER_AGENT)
        image_by_commander = {}
        for name in commanders_to_fetch:
            # After a 429, stop hitting Scryfall until the backoff window passes;
            # unfetched commanders stay blank and are retried on a later load
            if time.time() < _scryfall_backoff_until:
                print(f"Scryfall backoff active; skipping remaining {len(commanders_to_fetch) - len(image_by_commander)} commander(s)")
                break
            # /cards/named is limited to 2 requests/second
            wait = SCRYFALL_MIN_INTERVAL - (time.time() - _scryfall_last_request)
            if wait > 0:
                time.sleep(wait)
            _scryfall_last_request = time.time()
            try:
                card = scrython.cards.Named(fuzzy=name)
                raw_uris = getattr(card, "image_uris", None)
                uris = raw_uris() if callable(raw_uris) else raw_uris
                if not uris and getattr(card, "card_faces", None):
                    face0 = card.card_faces[0]
                    raw_uris = face0.get("image_uris") if isinstance(face0, dict) else getattr(face0, "image_uris", None)
                    uris = raw_uris() if callable(raw_uris) else raw_uris
                image_by_commander[name] = uris.get("art_crop") if isinstance(uris, dict) else None
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                if getattr(e, "status", None) == 429 or "rate-limit" in str(e).lower():
                    _scryfall_backoff_until = time.time() + SCRYFALL_BACKOFF_SECONDS
                    break
                image_by_commander[name] = None
        if existing_df is not None:
            cache = existing_df[["Commander", "Image"]].drop_duplicates("Commander")
            url_map = cache.set_index("Commander")["Image"].to_dict()
            url_map.update(image_by_commander)
            out = player_cmd.copy()
            out["Image"] = out["Commander"].map(url_map)
        else:
            out = player_cmd.copy()
            out["Image"] = out["Commander"].map(image_by_commander)
        out.to_csv(csv_path, index=False)
        return out

    def get_data(self, data_identifier):
        return self.data.get(data_identifier, None).copy()

    def set_data(self, new_data, data_identifier):
        if data_identifier in self.data.keys():
            self.data[data_identifier] = new_data

def get_data_manager():
    global data_manager

    if not data_manager:
        data_manager = DataManager()

    return data_manager

def refresh_data():
    global data_manager

    data_manager = DataManager()