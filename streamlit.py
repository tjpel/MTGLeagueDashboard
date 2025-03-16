import pandas as pd
import plotly.express as px
import streamlit as st
import helpers.constants as c
from helpers.data_manager import get_data_manager

#--------------------SITE--------------------------------------------------------------
st.title("Midwest Vintage Toys Themed Commander League Season 4")
st.caption("Created by Thomas Pelowitz")

st.header("Commander Information")
st.write("See information about Commanders and ...")
commander_col = st.selectbox(
    "Pick One",
    [
        "Color Identity",
        "CMC",
        "First Printing Set",
        "Year of First Printing"
    ]
)

temp_vc = get_data_manager().get_data("Commander Info")[commander_col].value_counts().reset_index()
temp_vc.columns = [commander_col, "Count"]
fig = px.bar(temp_vc, x=commander_col, y='Count', title=f'Distribution of {commander_col} Among Commanders')
st.plotly_chart(fig)