import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import helpers.constants as c
from helpers.data_manager import get_data_manager, refresh_data
from helpers.methods import *

PLACEMENT_ORDER = ["First Place", "Second Place", "Third Place", "Fourth Place"]
refresh_data()

#--------------------SITE--------------------------------------------------
st.title("Midwest Vintage Toys Themed Commander League Season 6")
st.caption("Created by Thomas Pelowitz")

st.header("Current Standings")
standings = get_data_manager().get_data("Placements by Player")
if not standings.empty:

    commander_info = get_data_manager().get_data("Commander Info").set_index('Player')[["Commander"]]
    standings = standings.join(commander_info, on="Player", validate="1:1")
    standings[PLACEMENT_ORDER] = standings.apply(lambda x: pd.Series(get_overall_placements(x.name)), axis=1)
    standings = standings[["Commander","Average Placement", "Games Played"] + PLACEMENT_ORDER]
    standings = standings.sort_values(by=["Average Placement", "Games Played", "First Place", "Second Place", "Third Place"], ascending=[True, False, False, False, False])
    
    # Add checkbox to filter players with more than 10 games
    filter_active_players = st.checkbox("Show only players with 10 or more games completed", value=False)
    
    # Apply filter if checkbox is checked
    if filter_active_players:
        standings = standings[standings["Games Played"] >= 10]
    
    st.dataframe(standings, column_config={
        "Average Placement": st.column_config.NumberColumn("Average Placement", format="%.3f")
    })
else:
    st.write("Standings will be available once games begin!")

st.header("Commander Information")
st.write("See information about Commanders and ...")
commander_col = st.selectbox(
    "Pick One",
    [
        "Color Identity",
        "CMC",
        "First Printing Set",
        "First Printing Year"
    ]
)

temp_vc = get_data_manager().get_data("Commander Info")[[commander_col]].value_counts().reset_index()
temp_vc.columns = [commander_col, "Count"]
temp_vc[commander_col] = temp_vc[commander_col].astype(str)

fig = px.bar(
    temp_vc, 
    x=commander_col, 
    y="Count",
    color="Count"
)
fig.update_layout(bargap=0.1)  # Reduce gap between bars for extra width

st.plotly_chart(fig)