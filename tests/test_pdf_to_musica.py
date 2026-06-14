from pathlib import Path
from unittest.mock import Mock

import pytest

from pdf_to_musica.converter import AudiverisNotFoundError, ConversionOptions, convert_pdf_to_mxl


def test_convert_pdf_to_mxl_invokes_audiveris_with_safe_paths_and_returns_mxl(tmp_path: Path):
    pdf_path = tmp_path / "score.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake test score")

    def fake_runner(command, *, cwd=None, timeout=None):
        assert "-batch" in command
        assert "-export" in command
        assert command[-1].endswith("input.pdf")
        assert str(pdf_path) not in command
        out_dir = Path(command[command.index("-output") + 1])
        assert out_dir.name == "audiveris-output"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "input.mxl").write_bytes(b"PK\x03\x04fake compressed musicxml")
        return Mock(returncode=0, stdout="exported", stderr="")

    result = convert_pdf_to_mxl(
        pdf_path,
        output_dir=tmp_path / "out",
        options=ConversionOptions(audiveris_command="audiveris", timeout_seconds=30),
        runner=fake_runner,
    )

    assert result.mxl_path == tmp_path / "out" / "score.mxl"
    assert result.mxl_path.exists()
    assert result.mxl_path.read_bytes().startswith(b"PK")
    assert result.source_pdf == pdf_path
    assert result.engine == "Audiveris"


def test_convert_pdf_to_mxl_handles_arabic_uploaded_filename_by_copying_to_ascii_path(tmp_path: Path):
    pdf_path = tmp_path / "نشيد الأطفال 4-4 - Full Score.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake test score")
    seen_command = None

    def fake_runner(command, *, cwd=None, timeout=None):
        nonlocal seen_command
        seen_command = command
        assert command[-1].endswith("input.pdf")
        assert "نشيد" not in " ".join(command)
        out_dir = Path(command[command.index("-output") + 1])
        (out_dir / "input.mxl").write_bytes(b"PK\x03\x04fake compressed musicxml")
        return Mock(returncode=0, stdout="exported", stderr="")

    result = convert_pdf_to_mxl(
        pdf_path,
        output_dir=tmp_path / "out",
        options=ConversionOptions(audiveris_command="audiveris", timeout_seconds=30),
        runner=fake_runner,
    )

    assert seen_command is not None
    assert result.mxl_path.exists()
    assert result.mxl_path.name == "نشيد الأطفال 4-4 - Full Score.mxl"


def test_convert_pdf_to_mxl_raises_clear_error_when_audiveris_missing(tmp_path: Path):
    pdf_path = tmp_path / "score.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake test score")

    def missing_runner(command, *, cwd=None, timeout=None):
        raise FileNotFoundError("audiveris")

    with pytest.raises(AudiverisNotFoundError, match="Audiveris is required"):
        convert_pdf_to_mxl(pdf_path, output_dir=tmp_path / "out", runner=missing_runner)


def test_convert_pdf_to_mxl_requires_pdf_extension(tmp_path: Path):
    image_path = tmp_path / "score.png"
    image_path.write_bytes(b"not pdf")

    with pytest.raises(ValueError, match="Input file must be a PDF"):
        convert_pdf_to_mxl(image_path, output_dir=tmp_path / "out")
