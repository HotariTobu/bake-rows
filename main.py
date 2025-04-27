import streamlit as st
import polars as pl
from pathlib import Path

se = st.session_state

if "files" not in se:
    se.files = {}

if "selected" not in se:
    se.selected = None

with st.sidebar:
    for id, file in se.files.items():
        if st.button(file.name, key=id):
            se.selected = id
            st.rerun()

    file = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx", "xls"])
    if file is not None:
        if file.file_id not in se.files:
            se.files[file.file_id] = file
            st.rerun()

if se.selected is None:
    exit()

st.title(se.files[se.selected].name)
