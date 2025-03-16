import helpers.constants as c
from helpers.data_manager import get_data_manager

def stringify_record(record: list) -> str:
    return f"{record[0]}:{record[1]}"

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

            record[c.PLACEMENT[col_1]] += 1
    
    return record

def get_color_players(color: str, exact: bool) -> list:
    player_cmd = get_data_manager().get_data("Commander Info")
    if exact:
        return player_cmd[player_cmd['Color Identity'] == color]["Player"].tolist()
    else:
        return player_cmd[player_cmd['Color Identity'].str.contains(color, case=False, na=False)]["Player"].tolist()

def get_player_record_against_color(player, color, exact, stringify):
    color_players = get_color_players(color, exact)

    overall_record = [0, 0]
    for player2 in color_players:
        v_player_record = get_1v1_record(player, player2, False)
        overall_record[0] += v_player_record[0]
        overall_record[1] += v_player_record[1]

    if not stringify:
        return overall_record
    else:
        return stringify_record(overall_record)

def get_player_placements_against_color(player, color, exact):
    color_players = get_color_players(color, exact)

    overall_placements = [0, 0, 0, 0]
    for player2 in color_players:
        v_player_placement = get_1v1_placements(player, player2)
        overall_placements = [x + y for x, y in zip(overall_placements, v_player_placement)]

    return overall_placements
