import hmac
import pandas as pd
import plotly.express as px
import streamlit as st
from helpers.data_manager import get_data_manager
from helpers.methods import get_opponents_played, get_pair_game_counts, get_recent_games

# ---- Login ----
if not st.session_state.get("admin_authenticated", False):
    st.title("Admin Login")
    with st.form("admin_login"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")

    if submitted:
        if hmac.compare_digest(password, st.secrets["admin_password"]):
            st.session_state["admin_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# ---- Admin Page ----
st.title("Admin")
if st.button("Log Out"):
    st.session_state["admin_authenticated"] = False
    st.rerun()

placements_by_game = get_data_manager().get_data("Placements by Game")

# ---- Opponent Coverage ----
with st.expander("Opponent Coverage", expanded=True):
    entrants = sorted(get_data_manager().get_data("Commander Info")["Player"].unique())
    opponents_played = get_opponents_played(placements_by_game)

    if len(entrants) < 2:
        st.write("Not enough entrants to track opponent coverage.")
    else:
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

# ---- Most Frequent Pairings ----
with st.expander("Most Frequent Pairings", expanded=True):
    pair_counts = get_pair_game_counts(placements_by_game)

    if not pair_counts:
        st.write("No games recorded yet!")
    else:
        games_played = {}
        for _, row in placements_by_game.iterrows():
            for col in ["First Place", "Second Place", "Third Place", "Fourth Place"]:
                if row[col]:
                    games_played[row[col]] = games_played.get(row[col], 0) + 1

        pairs = pd.DataFrame(
            [
                {
                    "Pair": f"{a} & {b}",
                    "Games Together": count,
                    "Games A": games_played[a],
                    "Games B": games_played[b],
                    "Avg % Together": (count / games_played[a] + count / games_played[b]) / 2,
                }
                for (a, b), count in pair_counts.items()
            ]
        )
        top_n = st.slider("Pairs to show", min_value=5, max_value=min(50, len(pairs)), value=min(15, len(pairs))) if len(pairs) > 5 else len(pairs)
        pairs = pairs.sort_values(["Games Together", "Avg % Together"], ascending=False).head(top_n)
        pairs["Label"] = pairs.apply(
            lambda x: f"{x['Games Together']}/{x['Games A']} · {x['Games Together']}/{x['Games B']} games · {x['Avg % Together']:.0%} avg", axis=1
        )

        fig = px.bar(
            pairs,
            x="Games Together",
            y="Pair",
            orientation="h",
            text="Label",
            custom_data=["Avg % Together"],
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x} games together<br>%{customdata[0]:.1%} avg of their games<extra></extra>",
        )
        fig.update_layout(
            yaxis=dict(categoryorder="array", categoryarray=pairs["Pair"].tolist()[::-1], title=None),
            xaxis=dict(title="Games Played Together", range=[0, pairs["Games Together"].max() * 1.3]),
            height=max(300, 32 * len(pairs) + 100),
            bargap=0.25,
        )
        st.plotly_chart(fig)
        st.caption("Avg % = the average, across both players, of the share of their games they played together.")

# ---- Recently Played Games ----
with st.expander("Recently Played Games", expanded=True):
    recent_games = get_recent_games(placements_by_game, limit=50)
    if not recent_games.empty:
        recent_games = recent_games.copy()
        recent_games["Date"] = recent_games["Timestamp"].dt.strftime("%b %d, %Y")
        st.dataframe(
            recent_games[["Date", "First Place", "Second Place", "Third Place", "Fourth Place"]],
            hide_index=True,
        )
    else:
        st.write("No games recorded yet!")
