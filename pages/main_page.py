import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import helpers.constants as c
from helpers.data_manager import get_data_manager
from helpers.methods import *

PLACEMENT_ORDER = ["First Place", "Second Place", "Third Place", "Fourth Place"]

#--------------------SITE--------------------------------------------------
st.title("Midwest Vintage Toys Themed Commander League Season 4")
st.caption("Created by Thomas Pelowitz")
st.title("WARNING: This page is currently full of 'junk' data as we wait for the season to start! The 'Commander Information' section at the bottom is correct.")

st.header("Cute vs. Brute")
team_viz = st.selectbox(
    "Visualization",
    [
        "Pie",
        #"Box",
    ]
)
cute_placements = get_subgroup_placement("Cute", "Team", True, False)
brute_placements = get_subgroup_placement("Brute", "Team", True, False)
match team_viz:
    case "Pie":
        cute_total = (2 * cute_placements[1]) + (3 * cute_placements[2]) + (4 * cute_placements[3])
        cute_avg = cute_total / sum(cute_placements)
        brute_total = (2 * brute_placements[1]) + (3 * brute_placements[2]) + (4 * brute_placements[3])
        brute_avg = brute_total / sum(brute_placements)
        temp_df = pd.DataFrame({"Team": ["Cute", "Brute"], "Average Placement": [cute_avg, brute_avg]})
        temp_df["Performance"] = 1 / temp_df["Average Placement"]
        fig = px.pie(temp_df, values="Performance", names="Team", color="Team", color_discrete_map=c.CUTE_BRUTE_COLORS)
        fig.update_traces(textposition='inside', textinfo='label')
        st.plotly_chart(fig)
        st.caption('Pie pieces sized by "Performance", or 1 / Average Team Placement. This is done to account for lower placements being better.')
    case "Box":
        cute_df = pd.DataFrame({
            'Placement': (
                [1] * cute_placements[0] +
                [2] * cute_placements[1] +
                [3] * cute_placements[2] +
                [4] * cute_placements[3]
            ),
            'Team': ['Cute'] * sum(cute_placements)
        })
        brute_df = pd.DataFrame({
            'Placement': (
                [1] * brute_placements[0] +
                [2] * brute_placements[1] +
                [3] * brute_placements[2] +
                [4] * brute_placements[3]
            ),
            'Team': ['Brute'] * sum(brute_placements)
        })

        # Convert to DataFrame
        temp_df = pd.concat([cute_df, brute_df], ignore_index=True)

        # Create box plot
        fig = px.box(temp_df, x='Team', y='Placement', points='all', color='Team', color_discrete_map=c.CUTE_BRUTE_COLORS)
        fig.update_yaxes(autorange='reversed', title='Placement')  # 1st is better than 4th
        st.plotly_chart(fig)

st.header("Current Standings")
#TODO add commander?
standings = get_data_manager().get_data("Placements by Player").sort_values(by="Average Placement")
commander_info = get_data_manager().get_data("Commander Info").set_index('Player')[["Commander"]]
standings = standings.join(commander_info, on="Player", validate="1:1")
standings[PLACEMENT_ORDER] = standings.apply(lambda x: pd.Series(get_overall_placements(x.name)), axis=1)
standings = standings[["Commander", "Team", "Average Placement", "Games Played"] + PLACEMENT_ORDER]
st.dataframe(standings, column_config={
    "Average Placement": st.column_config.NumberColumn("Average Placement", format="%.3f")
})

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

temp_vc = get_data_manager().get_data("Commander Info")[[commander_col, "Team"]].value_counts().reset_index()
temp_vc.columns = [commander_col, "Team", "Count"]
temp_vc[commander_col] = temp_vc[commander_col].astype(str)
temp_vc["Team"] = temp_vc["Team"].astype(str)

pivot_df = temp_vc.pivot(index=commander_col, columns='Team', values='Count').fillna(0)

# Create bars manually
fig = go.Figure()

for team in pivot_df.columns:
    fig.add_trace(go.Bar(
        x=pivot_df.index,
        y=pivot_df[team],
        name=team,
        marker_color=c.CUTE_BRUTE_COLORS.get(team, None)  # safe fallback
    ))

fig.update_layout(
    barmode='stack',
    title=f'Distribution of {commander_col} Among Commanders',
    xaxis_title=commander_col,
    yaxis_title='Count',
    height=500
)
st.plotly_chart(fig)