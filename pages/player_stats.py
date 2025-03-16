import streamlit as st
from helpers.methods import *
from helpers.data_manager import get_data_manager

st.header("Player Lookup")
player_name = st.selectbox(
    "Choose a player to view records for",
    get_data_manager().get_data("Commander Info")["Player"].unique()
)
color_id_for_record = st.selectbox(
    "Choose a color combination to see the player's record against it",
    c.COLOR_NAME_TO_SYM.keys()
)
st.write(f"Record against {color_id_for_record}: {get_player_record_against_color(player_name, c.COLOR_NAME_TO_SYM[color_id_for_record], True, True)}")
st.write(f"Record against {color_id_for_record}: {get_player_placements_against_color(player_name, c.COLOR_NAME_TO_SYM[color_id_for_record], True)}")

#TODO: Pie chart of placements against that color