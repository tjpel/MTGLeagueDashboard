import pandas as pd
import helpers.constants as c
from helpers.data_manager import get_data_manager

def stringify_record(record: list) -> str:
    return f"{record[0]}:{record[1]}"

def is_subsequence(sub, main):
    it = iter(main)
    return all(char in it for char in sub)

def get_overall_placements(player):
    record = [0, 0, 0, 0]
    placements_by_game = get_data_manager().get_data("Placements by Game")
    for index, row in placements_by_game.iterrows():
        if player in row.values:
            col_1 = row[row == player].index[0]

            record[c.PLACEMENT[col_1]-1] += 1
    
    return record

def get_1v1_record(player1, player2, stringify = True):
    record = [0, 0]
    placements_by_game = get_data_manager().get_data("Placements by Game")
    for index, row in placements_by_game.iterrows():
        if (player1 in row.values) and (player2 in row.values):
            col_1 = row[row == player1].index[0]
            col_2 = row[row == player2].index[0]

            if c.PLACEMENT[col_1] < c.PLACEMENT[col_2]:
                record[0] += 1
            else:
                record[1] += 1
    
    if not stringify:
        return record
    else:
        return stringify_record(record)

def get_1v1_placements(player1, player2):
    record = [0, 0, 0, 0]
    placements_by_game = get_data_manager().get_data("Placements by Game")
    for index, row in placements_by_game.iterrows():
        if (player1 in row.values) and (player2 in row.values):
            col_1 = row[row == player1].index[0]

            record[c.PLACEMENT[col_1]-1] += 1
    
    return record

def get_player_subgroup(subgroup: str, descriminator: str, exact: bool, negate: bool = False) -> list:
    player_cmd = get_data_manager().get_data("Commander Info")
    if exact:
        if negate:
            return player_cmd[player_cmd[descriminator] != subgroup]["Player"].tolist()
        else:
            return player_cmd[player_cmd[descriminator] == subgroup]["Player"].tolist()
    else:
        if negate:
            return player_cmd[player_cmd[descriminator].apply(lambda row: not is_subsequence(subgroup, row))]["Player"].tolist()
        else:
            return player_cmd[player_cmd[descriminator].apply(lambda row: is_subsequence(subgroup, row))]["Player"].tolist()

def get_recent_games(games_df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    if games_df is None or games_df.empty:
        return pd.DataFrame(columns=games_df.columns if isinstance(games_df, pd.DataFrame) else [])

    recent_games = games_df.copy().reset_index(drop=True)
    recent_games["Timestamp"] = pd.to_datetime(recent_games["Timestamp"], errors="coerce")
    recent_games["_source_order"] = recent_games.index

    recent_games = recent_games.sort_values(
        by=["Timestamp", "_source_order"],
        ascending=[False, False],
        na_position="last",
    )

    return recent_games.head(limit).drop(columns=["_source_order"])

def get_opponents_played(games_df: pd.DataFrame) -> dict[str, set]:
    opponents = {}
    for _, row in games_df.iterrows():
        players = [row[col] for col in ["First Place", "Second Place", "Third Place", "Fourth Place"] if row[col]]
        for player in players:
            opponents.setdefault(player, set()).update(p for p in players if p != player)

    return opponents

def get_pair_game_counts(games_df: pd.DataFrame) -> dict[tuple, int]:
    pair_counts = {}
    for _, row in games_df.iterrows():
        players = sorted({row[col] for col in ["First Place", "Second Place", "Third Place", "Fourth Place"] if row[col]})
        for i, player1 in enumerate(players):
            for player2 in players[i + 1:]:
                pair_counts[(player1, player2)] = pair_counts.get((player1, player2), 0) + 1

    return pair_counts


def get_player_record_against_subgroup(player, player_group, group_name, exact, stringify):
    subgroup_players = get_player_subgroup(player_group, group_name, exact)

    overall_record = [0, 0]
    for player2 in subgroup_players:
        v_player_record = get_1v1_record(player, player2, False)
        overall_record = [x + y for x, y in zip(overall_record, v_player_record)]

    if not stringify:
        return overall_record
    else:
        return stringify_record(overall_record)

def get_player_placement_against_subgroup(player, player_group, group_name, exact, stringify):
    subgroup_players = get_player_subgroup(player_group, group_name, exact)

    overall_placements = [0, 0, 0, 0]
    for player2 in subgroup_players:
        v_player_placement = get_1v1_placements(player, player2)
        overall_placements = [x + y for x, y in zip(overall_placements, v_player_placement)]

    if not stringify:
        return overall_placements
    else:
        return stringify_record(overall_placements)

def get_subgroup_placement(group_of_interest, group_name, exact, stringify):
    subgroup_players = get_player_subgroup(group_of_interest, group_name, exact)
    not_subgroup_players = get_player_subgroup(group_of_interest, group_name, exact, True)

    overall_placements = [0, 0, 0, 0]
    for s_player in subgroup_players:
        for n_s_player in not_subgroup_players:
            v_player_placement = get_1v1_placements(s_player, n_s_player)
            overall_placements = [x + y for x, y in zip(overall_placements, v_player_placement)]

    if not stringify:
        return overall_placements
    else:
        return stringify_record(overall_placements)