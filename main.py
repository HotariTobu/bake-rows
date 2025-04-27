import streamlit as st
import polars as pl
from pathlib import Path

from lib import StateFactory

with StateFactory() as sf:
    files, set_files = sf.state({})
    selected, set_selected = sf.state("")

    def side_button_clicked(id: str):
        set_selected(id)

    def file_uploaded(file):
        id = file.file_id
        set_files(files | {id: file})
        set_selected(id)

    with st.sidebar:
        for id, file in files.items():
            if st.button(label=file.name, key=id):
                side_button_clicked(id)

        st.file_uploader(
            label="Upload CSV or Excel files",
            type=["csv", "xlsx", "xls"],
            on_change=lambda: file_uploaded(st.session_state["current_file"]),
            key="current_file",
        )

    if selected in files:
        st.title(body=files[selected].name)
