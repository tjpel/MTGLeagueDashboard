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
    return placements.merge(commander_info, on="Player", how="inner")


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
        "Results will become more meaningful as more games are played."
    )
    st.stop()

if total_games < 4:
    st.caption("Early in the season — statistics will become more meaningful as more games are recorded.")

df["First Printing Year"] = pd.to_numeric(df["First Printing Year"], errors="coerce")

n_players = len(df)
st.write(
    f"**{n_players}** players included (min {min_games} games). "
    "Results are exploratory when sample size is small."
)

# ---- Numeric correlations ----
st.subheader("Numeric Predictors vs Average Placement")

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
        x_vals, y_vals = x[valid], y[valid]
        if x_vals.nunique() < 2 or y_vals.nunique() < 2:
            rows.append({"Variable": var, "Spearman r": None, "P-value": None})
            continue
        r, p = stats.spearmanr(x_vals, y_vals)
        rows.append({"Variable": var, "Spearman r": round(r, 4), "P-value": round(p, 4)})

    corr_table = pd.DataFrame(rows)
    st.dataframe(
        corr_table,
        column_config={
            "Spearman r": st.column_config.NumberColumn("Spearman r", format="%.4f"),
            "P-value": st.column_config.NumberColumn("P-value", format="%.4f"),
        },
        hide_index=True,
    )
    st.caption(
        "Negative r: higher value of the variable is associated with **better** (lower) average placement."
    )

    for var in numeric_vars:
        plot_df = df_numeric[[var, "Average Placement"]].dropna()
        if len(plot_df) < 2:
            continue
        fig = px.scatter(
            plot_df,
            x=var,
            y="Average Placement",
            trendline="ols",
            template="plotly_dark",
        )
        fig.update_layout(
            title=f"{var} vs Average Placement (lower is better)",
            yaxis_title="Average Placement",
        )
        st.plotly_chart(fig)

# ---- Binary predictors ----
st.subheader("Binary Predictors vs Average Placement")

binary_vars = ["UB", "Non-Standard Set"]
available_binary = [v for v in binary_vars if v in df.columns]

if not available_binary:
    st.write("No binary predictor columns found in data.")
else:
    for var in available_binary:
        df_bin = df[[var, "Average Placement"]].dropna()
        df_bin = df_bin[df_bin[var].isin(["Y", "N"])]
        if df_bin[var].nunique() < 2:
            st.write(f"Not enough variation in **{var}** for comparison yet.")
            continue

        summary = (
            df_bin.groupby(var)["Average Placement"]
            .agg(Mean="mean", Median="median", Count="count")
            .reset_index()
            .rename(columns={"Mean": "Mean Placement", "Median": "Median Placement"})
        )

        st.write(f"**{var}**")
        st.dataframe(
            summary,
            column_config={
                "Mean Placement": st.column_config.NumberColumn(format="%.3f"),
                "Median Placement": st.column_config.NumberColumn(format="%.3f"),
            },
            hide_index=True,
        )

        y_vals = df_bin.loc[df_bin[var] == "Y", "Average Placement"]
        n_vals = df_bin.loc[df_bin[var] == "N", "Average Placement"]
        if len(y_vals) >= 1 and len(n_vals) >= 1 and (len(y_vals) + len(n_vals)) >= 3:
            _, p_val = stats.mannwhitneyu(y_vals, n_vals, alternative="two-sided")
            st.caption(
                f"Mann-Whitney U p-value: {p_val:.4f} — {100*p_val:.1f}% chance the "
                "difference is due to random variation."
            )

        fig = px.bar(
            summary,
            x=var,
            y="Mean Placement",
            color=var,
            title=f"Mean Placement by {var} (lower is better)",
            template="plotly_dark",
        )
        fig.update_layout(yaxis=dict(range=[0, 4]), showlegend=False)
        st.plotly_chart(fig)
