import streamlit as st
import polars as pl
from pathlib import Path
from io import BytesIO

from lib import StateFactory
from score import score_sentences

IMPORT_DIALOG_STATE_KEY = "import-dialog-opened"
EDITED_DF_STATE_KEY = "edited-df"

SCORE_COL_NAME = "Score"
REMOVE_COL_NAME = "Remove"


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

        top_percent = st.slider(
            label="Top Percent",
            min_value=0,
            max_value=100,
            value=5,
            step=1,
            format="%d%%",
        )

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
            scores = score_sentences(texts, counts, top_percent)
            output_df = (
                pl.DataFrame(
                    {text_col: texts, count_col: counts, SCORE_COL_NAME: scores}
                )
                .sort(by=text_col)
                .sort(by=SCORE_COL_NAME, descending=True)
                .with_columns(pl.lit(False).alias(REMOVE_COL_NAME))
            )

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
            filename = file_dict[selected].name

            st.header(body=filename)

            if st.button(label="Prepare Download"):
                edited_df: pl.DataFrame = st.session_state[EDITED_DF_STATE_KEY]
                filtered_df = edited_df.filter(~pl.col(REMOVE_COL_NAME)).drop(
                    [SCORE_COL_NAME, REMOVE_COL_NAME]
                )

                buf = BytesIO()
                filtered_df.write_excel(buf)

                st.download_button(
                    label="Download Excel",
                    data=buf,
                    file_name=f"{Path(filename).stem}_edited.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    icon=":material/download:",
                )

            df: pl.DataFrame = output_df_dict[selected]
            disabled_cols = list(df.columns)
            disabled_cols.remove(REMOVE_COL_NAME)
            st.session_state[EDITED_DF_STATE_KEY] = st.data_editor(
                data=df, disabled=disabled_cols
            )

        elif st.session_state[IMPORT_DIALOG_STATE_KEY]:
            import_canceled()

        else:
            import_dialog(file_dict[selected])
