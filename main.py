import streamlit as st
import polars as pl
from pathlib import Path

files = []

with st.sidebar:
    for file in files:
        st.write(file)

    file = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx", "xls"])
    files.append(file)
