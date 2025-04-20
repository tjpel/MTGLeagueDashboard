import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from helpers.methods import *
from helpers.data_manager import get_data_manager


st.header("Player Lookup")
player_name = st.selectbox(
    "Choose a player to view records for",
    get_data_manager().get_data("Commander Info").sort_values(by="Player")["Player"].unique()
)
overall_placements = get_overall_placements(player_name)
if sum(overall_placements) > 0:
    overall_placements_df = pd.DataFrame(data={
        "Placements": ["First", "Second", "Third", "Fourth"],
        "Value": overall_placements}
    )
    fig = px.pie(overall_placements_df, values="Value", names="Placements")
    fig.update_traces(textinfo='percent+label', textposition='inside', showlegend=False)
    st.plotly_chart(fig)
else:
    st.write("This player hasn't played any games yet!")

stats_subgroup = st.selectbox(
    "Choose a category to see how you match up against it!",
    [
        "Color Identity",
        "Cute or Brute",
    ]
)

match stats_subgroup:
    case "Color Identity":
        exact_radio = st.radio(
            "Should I match the color exactly?",
            [
                "Match color exactly",
                "Decks that include this color"
            ]
        )

        if exact_radio == "Match color exactly":
            exact = True
        else:
            exact = False

        color_id_for_record = st.selectbox(
            "Choose a color combination to see the player's record against it",
            c.COLOR_NAME_TO_SYM.keys()
        )

        color_record = get_player_record_against_subgroup(player_name, c.COLOR_NAME_TO_SYM[color_id_for_record], "Color Identity", exact, False)
        if color_record != [0, 0]:
            #TODO: Add context to pop-ups
            fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])

            color_record = get_player_record_against_subgroup(player_name, c.COLOR_NAME_TO_SYM[color_id_for_record], "Color Identity", exact, False)
            color_w_l = pd.DataFrame(data={"Record": ["Win", "Loss"], "Value": color_record})
            w_l_fig = go.Pie(labels=color_w_l["Record"], values=color_w_l["Value"], hole=.3, textinfo='label+percent')
            fig.add_trace(w_l_fig, row=1, col=1)

            color_placement = get_player_placement_against_subgroup(player_name, c.COLOR_NAME_TO_SYM[color_id_for_record], "Color Identity", exact, False)
            color_placement_df = pd.DataFrame(data={"Placement": ["First", "Second", "Third", "Fourth"], "Value": color_placement})
            placement_fig = go.Pie(labels=color_placement_df["Placement"], values=color_placement_df["Value"], hole=.3, textinfo='label+percent')
            fig.add_trace(placement_fig, row=1, col=2)

            fig.update_traces(showlegend=False)

            st.plotly_chart(fig)
        else:
            st.write("This player hasn't played any games against those colors!")

    case "Cute or Brute":
        team_for_record = st.selectbox(
            "Choose a team to see the player's record against it",
            ["Cute", "Brute"]
        )

        team_record = get_player_record_against_subgroup(player_name, team_for_record, "Team", True, False)
        if team_record != [0, 0]:
            #TODO: Add context to pop-ups
            fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])

            team_w_l = pd.DataFrame(data={"Record": ["Win", "Loss"], "Value": team_record})
            w_l_fig = go.Pie(labels=team_w_l["Record"], values=team_w_l["Value"], hole=.3, textinfo='label+percent')
            fig.add_trace(w_l_fig, row=1, col=1)

            team_placement = get_player_placement_against_subgroup(player_name, team_for_record, "Team", True, False)
            team_placement_df = pd.DataFrame(data={"Placement": ["First", "Second", "Third", "Fourth"], "Value": team_placement})
            placement_fig = go.Pie(labels=team_placement_df["Placement"], values=team_placement_df["Value"], hole=.3, textinfo='label+percent')
            fig.add_trace(placement_fig, row=1, col=2)

            fig.update_traces(showlegend=False)

            st.plotly_chart(fig)
        else:
            st.write("This player hasn't played any games against that team!")



