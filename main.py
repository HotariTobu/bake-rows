import streamlit as st
import polars as pl
from pathlib import Path

if "files" not in st.session_state:
    st.session_state.files = {}

if "selected" not in st.session_state:
    st.session_state.selected = None

files = st.session_state.files
selected = st.session_state.selected

with st.sidebar:
    for id, file in files.items():
        if st.button(file.name, key=id):
            st.session_state.selected = id
            st.rerun()

    file = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx", "xls"])
    if file is not None:
        if file.file_id not in files:
            st.session_state.files[file.file_id] = file
            st.rerun()

if selected is None:
    exit()

st.title(files[selected].name)
