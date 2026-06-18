import streamlit as st
import pandas as pd
import plotly.express as px
import helpers.constants as c
from helpers.methods import get_overall_placements
from helpers.data_manager import get_data_manager

PLACEMENT_ORDER = ["First Place", "Second Place", "Third Place", "Fourth Place"]

st.header("Player Lookup")
player_name = st.selectbox(
    "Choose a player to view records for",
    get_data_manager().get_data("Commander Info").sort_values(by="Player")["Player"].unique(),
)

# ---- Overall placement breakdown ----
overall_placements = get_overall_placements(player_name)
if sum(overall_placements) > 0:
    overall_placements_df = pd.DataFrame(
        data={"Placements": ["First", "Second", "Third", "Fourth"], "Value": overall_placements}
    )
    fig = px.pie(
        overall_placements_df,
        values="Value",
        names="Placements",
        template="plotly_dark",
    )
    fig.update_traces(textinfo="percent+label", textposition="inside", showlegend=False)
    st.plotly_chart(fig)
else:
    st.write("This player hasn't played any games yet!")

# ---- Recent Form ----
st.subheader("Recent Form")
placements_by_game = get_data_manager().get_data("Placements by Game")

player_games = []
for _, row in placements_by_game.iterrows():
    if player_name in row.values:
        col = row[row == player_name].index[0]
        player_games.append(
            {
                "Date": row["Timestamp"],
                "Placement Label": col,
                "Placement": c.PLACEMENT[col],
            }
        )

if player_games:
    games_df = pd.DataFrame(player_games)
    games_df["Date"] = pd.to_datetime(games_df["Date"], errors="coerce")
    games_df = games_df.sort_values("Date")

    overall_avg = games_df["Placement"].mean()
    recent_avg = games_df.tail(3)["Placement"].mean()
    delta = overall_avg - recent_avg  # positive = recent is better than overall

    col1, col2 = st.columns(2)
    col1.metric(
        "Last 3 Games Avg",
        f"{recent_avg:.2f}",
        delta=f"{delta:+.2f} vs overall",
        delta_color="inverse",
    )
    col2.metric("Overall Avg", f"{overall_avg:.2f}")

    fig = px.line(
        games_df,
        x="Date",
        y="Placement",
        markers=True,
        title="Placement History (lower is better)",
        labels={"Placement": "Placement"},
        template="plotly_dark",
    )
    fig.update_layout(yaxis=dict(range=[4.2, 0.8], tickvals=[1, 2, 3, 4]))
    st.plotly_chart(fig)
elif sum(overall_placements) == 0:
    pass  # already told the user above
else:
    st.write("Not enough data to show recent form.")
