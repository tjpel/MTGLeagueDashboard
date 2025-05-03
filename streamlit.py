import streamlit as st
PLACEMENT_ORDER = ["First Place", "Second Place", "Third Place", "Fourth Place"]

#--------------------DEFINE PAGES------------------------------------------
pages = st.navigation([
    st.Page(
        "pages/main_page.py",
        title="Overview",
        icon=":material/group:"
    ),
    st.Page(
        "pages/player_stats.py",
        title="Stats by Player",
        icon=":material/person:"
    ),
    st.Page(
        "pages/commanders.py",
        title="Commanders",
        icon=":material/frame_person:"
    ),
    st.Page(
        "pages/page_info.py",
        title="About this Site",
        icon=":material/info:"
    ),
])
pages.run()