from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st

from pdf_to_musica.converter import ConversionOptions, convert_pdf_to_music

st.set_page_config(page_title="PDF to Musica", page_icon="🎼", layout="centered")
st.title("🎼 PDF to Musica")
st.caption("Upload a PDF strategy, essay, or story and turn its words into MIDI + WAV music.")

uploaded = st.file_uploader("PDF file", type=["pdf"])
col1, col2 = st.columns(2)
with col1:
    bpm = st.slider("BPM", min_value=60, max_value=180, value=120, step=5)
with col2:
    max_notes = st.slider("Max notes", min_value=16, max_value=256, value=96, step=16)

if uploaded and st.button("Generate music", type="primary"):
    with st.spinner("Reading PDF and composing..."):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pdf_path = tmp_path / uploaded.name
            pdf_path.write_bytes(uploaded.getvalue())
            try:
                result = convert_pdf_to_music(
                    pdf_path,
                    output_dir=tmp_path / "out",
                    options=ConversionOptions(bpm=bpm, max_notes=max_notes),
                )
            except Exception as exc:  # Streamlit should show clear user-safe error.
                st.error(str(exc))
                st.stop()

            st.success(f"Generated {result.note_count} notes")
            st.audio(result.wav_path.read_bytes(), format="audio/wav")
            st.download_button("Download WAV", result.wav_path.read_bytes(), file_name=result.wav_path.name)
            st.download_button("Download MIDI", result.midi_path.read_bytes(), file_name=result.midi_path.name)
            st.download_button("Download summary", result.summary_path.read_text(encoding="utf-8"), file_name=result.summary_path.name)
            with st.expander("Extracted text preview"):
                st.write(result.extracted_text[:1500])

st.markdown("---")
st.markdown("**Launch idea:** free 3 conversions/day, paid $5/month for longer PDFs and premium instruments.")
