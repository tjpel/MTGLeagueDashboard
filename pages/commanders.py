import streamlit as st
import scrython
import time
import os
from helpers.data_manager import get_data_manager

import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

st.title("Who has What Commander?")
st.write("You can use this page to find commander info by player! This may take a second to collect images.")

if os.path.exists("data/commanders_with_images.csv"):
    commanders_by_player = get_data_manager().get_data("Commander Info")

    images = []
    for name in commanders_by_player["Commander"]:
        time.sleep(0.01)
        try:
            card = scrython.cards.Named(fuzzy=name)
            images.append(card.image_uris()["art_crop"])
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            images.append(None)

    commanders_by_player["Image"] = images
else:
    commanders_by_player = get_data_manager().get_data("Commander with Images")


st.dataframe(
    commanders_by_player[["Image", "Commander", "Player"]],
    column_config={"Image": st.column_config.ImageColumn()},
    use_container_width = True,
    hide_index=True,
    row_height = 175,
    height = 5987
)