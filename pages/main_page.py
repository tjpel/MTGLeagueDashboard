import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import helpers.constants as c
from helpers.data_manager import get_data_manager, refresh_data
from helpers.methods import get_overall_placements

PLACEMENT_ORDER = ["First Place", "Second Place", "Third Place", "Fourth Place"]
refresh_data()

st.title("Midwest Vintage Toys Themed Commander League Season 7")
st.caption("Created by Thomas Pelowitz")

# ---- Standings ----
st.header("Current Standings")
standings = get_data_manager().get_data("Placements by Player")
if not standings.empty:
    commander_info = get_data_manager().get_data("Commander Info").set_index("Player")[["Commander"]]
    standings = standings.join(commander_info, on="Player", validate="1:1")
    standings[PLACEMENT_ORDER] = standings.apply(
        lambda x: pd.Series(get_overall_placements(x.name)), axis=1
    )

    # Consistency score (std dev of placements; lower = more consistent)
    placements_by_game = get_data_manager().get_data("Placements by Game")
    player_placement_vals: dict[str, list] = {}
    for _, row in placements_by_game.iterrows():
        for col in PLACEMENT_ORDER:
            player = row[col]
            if player:
                player_placement_vals.setdefault(player, []).append(c.PLACEMENT[col])

    standings["Consistency"] = standings.index.map(
        lambda p: np.std(player_placement_vals[p], ddof=1)
        if p in player_placement_vals and len(player_placement_vals[p]) >= 2
        else None
    )

    standings = standings[
        ["Commander", "Average Placement", "Consistency", "Games Played"] + PLACEMENT_ORDER
    ]
    standings = standings.sort_values(
        by=["Average Placement", "Games Played", "First Place", "Second Place", "Third Place"],
        ascending=[True, False, False, False, False],
    )

    filter_active_players = st.checkbox("Show only players with 10 or more games completed", value=False)
    if filter_active_players:
        standings = standings[standings["Games Played"] >= 10]

    st.dataframe(
        standings,
        column_config={
            "Average Placement": st.column_config.NumberColumn("Average Placement", format="%.3f"),
            "Consistency": st.column_config.NumberColumn("Consistency", format="%.2f"),
        },
    )
    st.caption("Consistency = standard deviation of placements (lower = more consistent performance).")
else:
    st.write("Standings will be available once games begin!")

# ---- Recently Played Games ----
st.header("Recently Played Games")
recent_games = get_data_manager().get_data("Placements by Game").head(15)
if not recent_games.empty:
    recent_games = recent_games.copy()
    recent_games["Timestamp"] = pd.to_datetime(recent_games["Timestamp"], errors="coerce")
    recent_games = recent_games.sort_values("Timestamp", ascending=False).head(10)
    recent_games["Date"] = recent_games["Timestamp"].dt.strftime("%b %d, %Y")
    st.dataframe(
        recent_games[["Date"] + PLACEMENT_ORDER],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.write("No games recorded yet!")

# ---- Commander Information ----
st.header("Commander Information")
commander_col = st.selectbox(
    "Pick One",
    ["CMC", "First Printing Set", "First Printing Year", "UB", "Non-Standard Set"],
)

temp_vc = (
    get_data_manager()
    .get_data("Commander Info")[[commander_col]]
    .value_counts()
    .reset_index()
)
temp_vc.columns = [commander_col, "Count"]
temp_vc[commander_col] = temp_vc[commander_col].astype(str)

fig = px.bar(temp_vc, x=commander_col, y="Count", color="Count", template="plotly_dark")
fig.update_layout(bargap=0.1)
st.plotly_chart(fig)
