from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from pdf_to_musica.converter import ConversionOptions, convert_pdf_to_music, text_to_notes


def make_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, text)
    pdf.save()


def test_text_to_notes_is_deterministic_and_respects_limits():
    text = "Launch fast. Make revenue. Ship music."

    first = text_to_notes(text, max_notes=12)
    second = text_to_notes(text, max_notes=12)

    assert first == second
    assert 1 <= len(first) <= 12
    assert all(48 <= note.pitch <= 84 for note in first)
    assert all(note.duration > 0 for note in first)


def test_convert_pdf_to_music_creates_midi_wav_and_summary(tmp_path: Path):
    pdf_path = tmp_path / "strategy.pdf"
    make_pdf(pdf_path, "This PDF strategy should become a bright musical theme.")

    result = convert_pdf_to_music(
        pdf_path,
        output_dir=tmp_path / "out",
        options=ConversionOptions(max_notes=16, bpm=100),
    )

    assert result.midi_path.exists()
    assert result.wav_path.exists()
    assert result.summary_path.exists()
    assert result.note_count > 0
    assert result.extracted_text.startswith("This PDF strategy")
    assert result.midi_path.read_bytes()[:4] == b"MThd"
    assert result.wav_path.read_bytes()[:4] == b"RIFF"
    assert "PDF to Musica" in result.summary_path.read_text(encoding="utf-8")


def test_empty_pdf_text_raises_clear_error(tmp_path: Path):
    pdf_path = tmp_path / "empty.pdf"
    make_pdf(pdf_path, "")

    with pytest.raises(ValueError, match="No readable text"):
        convert_pdf_to_music(pdf_path, output_dir=tmp_path / "out")
