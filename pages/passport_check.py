import streamlit as st
from helpers.data_manager import get_data_manager
from helpers.methods import get_opponents_played

st.title("Passport Check")
st.caption("Track who each player has played with so far this season.")

placements_by_game = get_data_manager().get_data("Placements by Game")
entrants = sorted(get_data_manager().get_data("Commander Info")["Player"].unique())
opponents_played = get_opponents_played(placements_by_game)

if len(entrants) < 2:
    st.write("Not enough entrants to track opponent coverage.")
    st.stop()

total_opponents = len(entrants) - 1
coverage = {
    player: len(opponents_played.get(player, set()) & set(entrants)) / total_opponents
    for player in entrants
}
average_completion = sum(coverage.values()) / len(entrants)
completed_count = sum(1 for rate in coverage.values() if rate == 1)

st.progress(average_completion, text=f"Average completion rate: {average_completion:.1%}")
st.progress(
    completed_count / len(entrants),
    text=f"Played with everyone: {completed_count} of {len(entrants)} participants ({completed_count / len(entrants):.1%})",
)

selected_player = st.selectbox("Player", entrants)
played = sorted(opponents_played.get(selected_player, set()) & set(entrants))
not_played = [p for p in entrants if p != selected_player and p not in played]

st.write(f"**{selected_player}** has played with {len(played)} of {total_opponents} players ({coverage[selected_player]:.1%}).")
played_col, not_played_col = st.columns(2)
with played_col:
    st.subheader(f"Played With ({len(played)})")
    st.dataframe({"Player": played}, hide_index=True)
with not_played_col:
    st.subheader(f"Not Played With ({len(not_played)})")
    st.dataframe({"Player": not_played}, hide_index=True)
