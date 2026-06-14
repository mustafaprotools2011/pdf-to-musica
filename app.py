from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st

from pdf_to_musica.converter import (
    AudiverisConversionError,
    AudiverisNotFoundError,
    ConversionOptions,
    audiveris_available,
    convert_pdf_to_mxl,
)

st.set_page_config(page_title="PDF to Musica", page_icon="🎼", layout="centered")
st.title("🎼 PDF to Musica")
st.caption("Convert sheet-music PDFs into editable compressed MusicXML .mxl files.")

st.info(
    "This app uses Audiveris OMR. It converts printed music notation in a PDF into MusicXML/MXL. "
    "It does not generate new music."
)

uploaded = st.file_uploader("Sheet-music PDF", type=["pdf"])
audiveris_command = st.text_input("Audiveris command/path", value="audiveris")
timeout = st.number_input("Timeout seconds", min_value=60, max_value=3600, value=600, step=60)

if audiveris_command and not audiveris_available(audiveris_command):
    st.warning("Audiveris was not found from this app environment. Conversion will fail until it is installed or a valid path is provided.")

if uploaded and st.button("Convert to MXL", type="primary"):
    with st.spinner("Running optical music recognition..."):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pdf_path = tmp_path / uploaded.name
            pdf_path.write_bytes(uploaded.getvalue())
            try:
                result = convert_pdf_to_mxl(
                    pdf_path,
                    output_dir=tmp_path / "out",
                    options=ConversionOptions(audiveris_command=audiveris_command, timeout_seconds=int(timeout)),
                )
            except (AudiverisNotFoundError, AudiverisConversionError, FileNotFoundError, ValueError) as exc:
                st.error(str(exc))
                st.stop()

            mxl_bytes = result.mxl_path.read_bytes()
            st.success("MXL file generated successfully")
            st.download_button(
                "Download .mxl",
                mxl_bytes,
                file_name=result.mxl_path.name,
                mime="application/vnd.recordare.musicxml",
            )
            with st.expander("Audiveris log"):
                st.text(result.stdout or "No stdout")
                if result.stderr:
                    st.text(result.stderr)

st.markdown("---")
st.markdown("**Best input:** clean, high-resolution sheet-music PDFs. Scanned images may need manual correction after export.")
