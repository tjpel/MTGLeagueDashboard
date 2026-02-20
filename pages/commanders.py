import streamlit as st
from helpers.data_manager import get_data_manager

st.title("Who has What Commander?")
st.write("You can use this page to find commander info by player.")

commanders_by_player = get_data_manager().get_data("Commander with Images")


st.dataframe(
    commanders_by_player[["Image", "Commander", "Player"]],
    column_config={"Image": st.column_config.ImageColumn()},
    use_container_width = True,
    hide_index=True,
    row_height = 175,
    height = 5987
)