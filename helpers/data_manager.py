from googleapiclient.discovery import build
import pandas as pd
import tomllib

import helpers.constants as c

data_manager = None

class SheetsAPI():
    SPREADSHEET_ID = '1LfM6l1_GJa_YnLOHmfb_jz2YaaABL7-_-l7gFgsUBeQ'
    PLACEMENTS_RANGE = 'Form Responses 1!A1:E200'
    api_key = None

    def __init__(self):
        with open(".streamlit/secrets.toml", "rb") as file:
            secrets = tomllib.load(file)

        self.api_key = secrets['sheets_api']

    def authenticate_sheets(api_key):
        return build('sheets', 'v4', developerKey=api_key).spreadsheets()

    def get_placements():
        sheets = authenticate_sheets(api_key)
        result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=PLACEMENTS_RANGE).execute()
        values = [value for value in result.get('values', []) if (value != [])]

        return pd.DataFrame(values[1:],columns=values[0])


class DataManager():

    data = {}
    sheets = None

    def __init__(self):
        self.sheets = SheetsAPI()
        #TODO: Turn this into api (sheets.get_placements())
        self.data["Placements by Game"] = pd.read_csv("player_standings_ex.csv")

        player_cmd = pd.read_csv("data/player-cmd.csv")
        player_cmd["Color Identity Textual"] = player_cmd["Color Identity"].apply(lambda x: c.COLOR_SYM_TO_NAME.get(x, x))
        self.data["Commander Info"] = player_cmd

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
        placements_by_player["Average Placement"] = placements_by_player["Total Points"] / placements_by_player["Games Played"]
        self.data["Placements by Player"] = placements_by_player

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
    
