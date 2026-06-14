from __future__ import annotations

import shutil
import subprocess
import tempfile
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

    run = runner or _default_runner
    with tempfile.TemporaryDirectory(prefix="pdf-to-musica-") as temp_dir_name:
        work_dir = Path(temp_dir_name)
        safe_pdf = work_dir / "input.pdf"
        safe_output_dir = work_dir / "audiveris-output"
        safe_output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_pdf, safe_pdf)

        command = [
            options.audiveris_command,
            "-batch",
            "-export",
            "-output",
            str(safe_output_dir),
            str(safe_pdf),
        ]

        try:
            completed = run(command, cwd=work_dir, timeout=options.timeout_seconds)
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

        generated_mxl = _find_generated_mxl(safe_output_dir, safe_pdf.stem)
        if not generated_mxl:
            raise AudiverisConversionError(
                "Audiveris finished but no .mxl file was produced. "
                "Check that the PDF contains readable music notation.\n"
                f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            )

        final_mxl_path = _unique_output_path(out_dir / f"{source_pdf.stem}.mxl")
        shutil.copyfile(generated_mxl, final_mxl_path)

    return ConversionResult(
        source_pdf=source_pdf,
        mxl_path=final_mxl_path,
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


def _unique_output_path(path: Path) -> Path:
    """Return a non-existing output path by appending -N when needed."""

    if not path.exists():
        return path
    for index in range(2, 10_000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Could not find a free output filename near {path}")


def _find_generated_mxl(output_dir: Path, source_stem: str) -> Path | None:
    candidates = sorted(output_dir.rglob("*.mxl"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return None

    normalized_stem = source_stem.lower().replace(" ", "")
    for candidate in candidates:
        if normalized_stem in candidate.stem.lower().replace(" ", ""):
            return candidate
    return candidates[0]
