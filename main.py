import streamlit as st
import polars as pl
from pathlib import Path

from lib import StateFactory

IMPORT_DIALOG_STATE_KEY = "import_dialog_opened"


def load_file(file) -> pl.DataFrame:
    p = Path(file.name)
    suf = p.suffix.lower()

    match suf:
        case ".csv":
            return pl.read_csv(file)
        case ".xlsx" | ".xls":
            return pl.read_excel(file)
        case _:
            raise ValueError(f"Unsupported file type: {suf}")


with StateFactory() as sf:
    selected, set_selected = sf.state("")
    file_dict, set_file_dict = sf.state({})
    output_df_dict, set_output_df_dict = sf.state({})

    def side_button_clicked(id: str):
        set_selected(id)

        # To force a rerun when dialog is closed
        st.rerun()

    def file_uploaded(file):
        st.session_state[IMPORT_DIALOG_STATE_KEY] = False

        id = file.file_id
        set_selected(id)
        set_file_dict(file_dict | {id: file})

    def import_canceled():
        st.session_state[IMPORT_DIALOG_STATE_KEY] = False

        set_selected("")

    def scored(df: pl.DataFrame):
        set_output_df_dict(output_df_dict | {id: df})

    @st.dialog("Import Data", width="large")
    def import_dialog(file):
        st.session_state[IMPORT_DIALOG_STATE_KEY] = True

        input_df: pl.DataFrame
        with st.spinner("Loading data...", show_time=True):
            input_df = load_file(file)

        col1, col2 = st.columns(2)
        with col1:
            text_col = st.selectbox(
                label="Select Text Column", options=input_df.columns
            )
        with col2:
            count_col = st.selectbox(
                label="Select Count Column", options=input_df.columns
            )

        st.dataframe(input_df, height=200)

        if not st.button("Import"):
            return

        if text_col == count_col:
            st.error("Text and Count columns cannot be the same")
            return

        texts = input_df[text_col]
        if texts.dtype != pl.String:
            st.error("Text column must be of type String")
            return

        counts = input_df[count_col]
        if counts.dtype != pl.Int64:
            st.error("Count column must be of type Int64")
            return

        with st.spinner("Processing data...", show_time=True):
            output_df = pl.DataFrame({text_col: texts, count_col: counts})

        scored(output_df)

        st.rerun()

    with st.sidebar:
        for id, file in file_dict.items():
            if st.button(label=file.name, key=id):
                side_button_clicked(id)

        st.file_uploader(
            label="Upload CSV or Excel file_dict",
            type=["csv", "xlsx", "xls"],
            on_change=lambda: file_uploaded(st.session_state["current_file"]),
            key="current_file",
        )

    if selected:
        if selected in output_df_dict:
            st.header(body=file_dict[selected].name)
            df = output_df_dict[selected]
            st.dataframe(df)

        elif st.session_state[IMPORT_DIALOG_STATE_KEY]:
            import_canceled()

        else:
            import_dialog(file_dict[selected])
