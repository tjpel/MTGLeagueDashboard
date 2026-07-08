import streamlit as st
import os

st.header("Access *The League Times* Official Archives")

available_seasons = []
for filename in os.listdir("imgs/"):
    if filename.startswith("season_") and os.path.isdir(os.path.join("imgs/", filename)):
        available_seasons.append(filename)

available_issues = {
    season: [
        issue for issue in os.listdir(os.path.join("imgs/", season)) if issue.endswith(".png")
    ]
    for season in available_seasons
}        

selected_season = st.selectbox(
    label="Season",
    options=[("Season " + season[7:]) for season in available_seasons]

)

selected_season_path = "season_" + selected_season.split(" ")[1]

selected_issue =st.selectbox(
    label="Issue",
    options=[("Issue " + issue[6:7]) for season in available_seasons for issue in available_issues[season]]
)

selected_issue_path = "issue_" + selected_issue[6] + ".png"

st.image(
    image=os.path.join("imgs/", selected_season_path, selected_issue_path)
)