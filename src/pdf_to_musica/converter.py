from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol


class CompletedProcessLike(Protocol):
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[..., CompletedProcessLike]


class AudiverisNotFoundError(RuntimeError):
    """Raised when the Audiveris OMR executable is missing."""


class AudiverisConversionError(RuntimeError):
    """Raised when Audiveris runs but does not produce an MXL file."""


@dataclass(frozen=True)
class ConversionOptions:
    """Controls PDF sheet-music to MXL conversion."""

    audiveris_command: str = field(default_factory=lambda: default_audiveris_command())
    timeout_seconds: int = 600


@dataclass(frozen=True)
class ConversionResult:
    source_pdf: Path
    mxl_path: Path
    engine: str
    stdout: str = ""
    stderr: str = ""


def convert_pdf_to_mxl(
    pdf_path: str | Path,
    output_dir: str | Path = "outputs",
    options: ConversionOptions | None = None,
    runner: Runner | None = None,
) -> ConversionResult:
    """Convert a sheet-music PDF to compressed MusicXML (.mxl) via Audiveris.

    Audiveris performs Optical Music Recognition (OMR). This function wraps its
    CLI, validates inputs, finds the generated `.mxl`, and returns its path.
    """

    options = options or ConversionOptions()
    source_pdf = Path(pdf_path)
    if not source_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {source_pdf}")
    if source_pdf.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a PDF")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    command = [
        options.audiveris_command,
        "-batch",
        "-export",
        "-output",
        str(out_dir),
        str(source_pdf),
    ]

    run = runner or _default_runner
    try:
        completed = run(command, cwd=source_pdf.parent, timeout=options.timeout_seconds)
    except FileNotFoundError as exc:
        raise AudiverisNotFoundError(
            "Audiveris is required to convert sheet music PDFs to MusicXML/MXL. "
            "Install Audiveris and make the 'audiveris' command available in PATH, "
            "or pass --audiveris-command with the full executable path."
        ) from exc

    stdout = getattr(completed, "stdout", "") or ""
    stderr = getattr(completed, "stderr", "") or ""
    returncode = getattr(completed, "returncode", 1)
    if returncode != 0:
        raise AudiverisConversionError(
            f"Audiveris failed with exit code {returncode}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )

    mxl_path = _find_generated_mxl(out_dir, source_pdf.stem)
    if not mxl_path:
        raise AudiverisConversionError(
            "Audiveris finished but no .mxl file was produced. "
            "Check that the PDF contains readable music notation.\n"
            f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )

    return ConversionResult(
        source_pdf=source_pdf,
        mxl_path=mxl_path,
        engine="Audiveris",
        stdout=stdout,
        stderr=stderr,
    )


def default_audiveris_command() -> str:
    """Return the best Audiveris command for this machine.

    Winget installs Audiveris on Windows at C:/Program Files/Audiveris/Audiveris.exe,
    but it does not always update PATH for the already-running Hermes/Streamlit process.
    Prefer that known executable when present; otherwise fall back to the PATH command.
    """

    windows_install = Path("C:/Program Files/Audiveris/Audiveris.exe")
    if windows_install.exists():
        return str(windows_install)
    return "audiveris"


def audiveris_available(command: str | None = None) -> bool:
    """Return True if the Audiveris command appears available."""

    command = command or default_audiveris_command()
    if Path(command).exists():
        return True
    return shutil.which(command) is not None


def _default_runner(command: list[str], *, cwd: Path | None = None, timeout: int | None = None):
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
        text=True,
        capture_output=True,
        check=False,
    )


def _find_generated_mxl(output_dir: Path, source_stem: str) -> Path | None:
    candidates = sorted(output_dir.rglob("*.mxl"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return None

    normalized_stem = source_stem.lower().replace(" ", "")
    for candidate in candidates:
        if normalized_stem in candidate.stem.lower().replace(" ", ""):
            return candidate
    return candidates[0]
