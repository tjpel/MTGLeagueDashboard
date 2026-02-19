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
            # image_uris can be a method (older scrython) or a dict (newer/env-dependent); DFCs use card_faces
            raw_uris = getattr(card, "image_uris", None)
            uris = raw_uris() if callable(raw_uris) else raw_uris
            if not uris and getattr(card, "card_faces", None):
                face0 = card.card_faces[0]
                raw_uris = face0.get("image_uris") if isinstance(face0, dict) else getattr(face0, "image_uris", None)
                uris = raw_uris() if callable(raw_uris) else raw_uris
            images.append(uris.get("art_crop") if isinstance(uris, dict) else None)
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