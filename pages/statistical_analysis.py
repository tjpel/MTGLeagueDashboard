import pandas as pd
import plotly.express as px
import streamlit as st
from scipy import stats
from helpers.data_manager import get_data_manager


def get_analysis_df():
    """Merge Placements by Player with Commander Info for analysis (player-level)."""
    placements = get_data_manager().get_data("Placements by Player")
    commander_info = get_data_manager().get_data("Commander Info")
    if placements.empty or commander_info.empty:
        return pd.DataFrame()
    placements = placements.reset_index()
    return placements.merge(
        commander_info,
        on="Player",
        how="inner",
    )


st.header("Statistical Analysis")
st.caption(
    "Analyzing what correlates with or is significantly associated with "
    "**lower** average placement (better performance)."
)

df = get_analysis_df()
if df.empty:
    st.warning("No placement or commander data available yet. Record some games to see statistics here.")
    st.stop()

games_max = df["Games Played"].max()
games_max_safe = max(1, int(games_max) if pd.notna(games_max) else 1)
total_games = int(df["Games Played"].sum()) if df["Games Played"].notna().all() else 0

min_games = st.slider(
    "Minimum games played (filter players for stability)",
    min_value=1,
    max_value=games_max_safe,
    value=1,
)
df = df[df["Games Played"] >= min_games].copy()

if len(df) < 2:
    st.info(
        "Very few or no games recorded yet, or too few players after filtering. "
        "Results will become more meaningful as more games are played. Lower the minimum games filter or add more data."
    )
    st.stop()

if total_games < 4:
    st.caption("Early in the season — statistics will become more meaningful as more games are recorded.")

# Ensure numeric for First Printing Year
df["First Printing Year"] = pd.to_numeric(df["First Printing Year"], errors="coerce")

n_players = len(df)
st.write(f"**{n_players}** players included (min {min_games} games). "
         "Results are exploratory when sample size is small.")

# ----- Section 1: Numeric correlations -----
st.subheader("1. Numeric predictors vs average placement")

numeric_vars = ["CMC", "Games Played", "First Printing Year"]
df_numeric = df[["Average Placement"] + numeric_vars].dropna()

if len(df_numeric) < 2:
    st.write("Not enough non-missing numeric data for correlation.")
else:
    rows = []
    for var in numeric_vars:
        x = df_numeric[var]
        y = df_numeric["Average Placement"]
        valid = x.notna() & y.notna()
        if valid.sum() < 2:
            rows.append({"Variable": var, "Spearman r": None, "P-value": None})
            continue
        x_vals = x[valid]
        y_vals = y[valid]
        if x_vals.nunique() < 2 or y_vals.nunique() < 2:
            rows.append({"Variable": var, "Spearman r": None, "P-value": None})
            continue
        r, p = stats.spearmanr(x_vals, y_vals)
        rows.append({"Variable": var, "Spearman r": round(r, 4), "P-value": round(p, 4)})

    corr_table = pd.DataFrame(rows)
    st.dataframe(corr_table, column_config={
        "Spearman r": st.column_config.NumberColumn("Spearman r", format="%.4f"),
        "P-value": st.column_config.NumberColumn("P-value", format="%.4f"),
    }, hide_index=True)
    st.caption(
        "Negative r: higher value of the variable is associated with **better** (lower) average placement."
    )

    for var in numeric_vars:
        plot_df = df_numeric[[var, "Average Placement"]].dropna()
        if len(plot_df) < 2:
            continue
        fig = px.scatter(plot_df, x=var, y="Average Placement", trendline="ols")
        fig.update_layout(
            title=f"{var} vs Average Placement (lower is better)",
            yaxis_title="Average Placement",
        )
        st.plotly_chart(fig)

# ----- Section 2: Color identity -----
st.subheader("2. Color identity and average placement")

color_col = "Color Identity Textual"
df_color = df[[color_col, "Average Placement"]].dropna()
if df_color[color_col].nunique() < 2:
    st.write("Need at least two color identities for comparison.")
else:
    by_color = (
        df_color.groupby(color_col, as_index=True)["Average Placement"]
        .agg(Mean_placement="mean", Median_placement="median", Count="count")
        .reset_index()
    )
    by_color = by_color.rename(columns={
        "Mean_placement": "Mean placement",
        "Median_placement": "Median placement",
    })
    st.dataframe(by_color, column_config={
        "Mean placement": st.column_config.NumberColumn("Mean placement", format="%.3f"),
        "Median placement": st.column_config.NumberColumn("Median placement", format="%.3f"),
    }, hide_index=True)

    groups = [df_color.loc[df_color[color_col] == g, "Average Placement"].values for g in by_color[color_col]]
    if all(len(g) >= 1 for g in groups):
        kw_stat, kw_p = stats.kruskal(*groups)
        st.metric("Kruskal–Wallis H", f"{kw_stat:.3f}")
        st.metric("P-value", f"{kw_p:.4f}")
        st.caption(f"P-value interpretation: Since the p-value is {kw_p:.4f}, there is a {(100 * kw_p):.2f}% chance that the differences observed in average placement is due to random chance alone (that is to say, there is no impact of color identity on average placement).")

    fig = px.box(
        df_color,
        x=color_col,
        y="Average Placement",
        title="Average placement by color identity (lower is better)",
    )
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig)
