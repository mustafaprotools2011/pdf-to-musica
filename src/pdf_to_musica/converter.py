from __future__ import annotations

import hashlib
import math
import re
import struct
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pypdf import PdfReader


@dataclass(frozen=True)
class ConversionOptions:
    """Controls how PDF text becomes music."""

    bpm: int = 120
    max_notes: int = 96
    scale: tuple[int, ...] = (0, 2, 4, 7, 9)  # major pentatonic: C D E G A
    root_midi_pitch: int = 60  # middle C
    sample_rate: int = 44_100


@dataclass(frozen=True)
class Note:
    pitch: int
    duration: float
    velocity: int


@dataclass(frozen=True)
class ConversionResult:
    extracted_text: str
    note_count: int
    midi_path: Path
    wav_path: Path
    summary_path: Path


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a PDF")

    reader = PdfReader(str(path))
    chunks = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(chunks)
    return re.sub(r"\s+", " ", text).strip()


def text_to_notes(text: str, max_notes: int = 96, options: ConversionOptions | None = None) -> list[Note]:
    options = options or ConversionOptions(max_notes=max_notes)
    tokens = re.findall(r"[A-Za-zÀ-ÿ0-9']+", text)
    tokens = tokens[: max(1, min(max_notes, options.max_notes))]
    notes: list[Note] = []

    for token in tokens:
        digest = hashlib.sha256(token.lower().encode("utf-8")).digest()
        scale_degree = digest[0] % len(options.scale)
        octave = (digest[1] % 3) - 1
        pitch = options.root_midi_pitch + options.scale[scale_degree] + octave * 12
        pitch = max(48, min(84, pitch))
        duration = [0.25, 0.5, 0.75, 1.0][digest[2] % 4]
        velocity = 64 + digest[3] % 48
        notes.append(Note(pitch=pitch, duration=duration, velocity=velocity))

    return notes


def convert_pdf_to_music(
    pdf_path: str | Path,
    output_dir: str | Path = "outputs",
    options: ConversionOptions | None = None,
) -> ConversionResult:
    options = options or ConversionOptions()
    text = extract_text_from_pdf(pdf_path)
    if not text:
        raise ValueError("No readable text found in this PDF. Try a text-based PDF or OCR it first.")

    notes = text_to_notes(text, max_notes=options.max_notes, options=options)
    if not notes:
        raise ValueError("No readable text found in this PDF. Try a text-based PDF or OCR it first.")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(pdf_path).stem.replace(" ", "-")
    midi_path = out_dir / f"{stem}.mid"
    wav_path = out_dir / f"{stem}.wav"
    summary_path = out_dir / f"{stem}-summary.md"

    write_midi(notes, midi_path, bpm=options.bpm)
    write_wav(notes, wav_path, bpm=options.bpm, sample_rate=options.sample_rate)
    summary_path.write_text(_summary(text, notes, midi_path, wav_path, options), encoding="utf-8")

    return ConversionResult(
        extracted_text=text,
        note_count=len(notes),
        midi_path=midi_path,
        wav_path=wav_path,
        summary_path=summary_path,
    )


def write_midi(notes: list[Note], path: Path, bpm: int = 120) -> None:
    ticks_per_quarter = 480
    tempo = int(60_000_000 / bpm)
    events = bytearray()
    events.extend(_varlen(0) + b"\xff\x51\x03" + tempo.to_bytes(3, "big"))
    events.extend(_varlen(0) + b"\xc0\x00")  # acoustic grand piano

    for note in notes:
        ticks = max(1, int(note.duration * ticks_per_quarter))
        events.extend(_varlen(0) + bytes([0x90, note.pitch, note.velocity]))
        events.extend(_varlen(ticks) + bytes([0x80, note.pitch, 0]))

    events.extend(_varlen(0) + b"\xff\x2f\x00")
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, ticks_per_quarter)
    track = b"MTrk" + struct.pack(">I", len(events)) + bytes(events)
    path.write_bytes(header + track)


def write_wav(notes: list[Note], path: Path, bpm: int = 120, sample_rate: int = 44_100) -> None:
    beat_seconds = 60 / bpm
    chunks: list[np.ndarray] = []
    for note in notes:
        seconds = max(0.08, note.duration * beat_seconds)
        n = int(sample_rate * seconds)
        t = np.linspace(0, seconds, n, endpoint=False)
        frequency = 440.0 * (2 ** ((note.pitch - 69) / 12))
        envelope = np.linspace(1.0, 0.15, n)
        signal = 0.28 * np.sin(2 * math.pi * frequency * t) * envelope
        chunks.append(signal)

    audio = np.concatenate(chunks) if chunks else np.zeros(sample_rate // 4)
    audio = np.clip(audio, -1, 1)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def _varlen(value: int) -> bytes:
    buffer = value & 0x7F
    value >>= 7
    bytes_out = []
    while value:
        bytes_out.insert(0, (buffer | 0x80))
        buffer = value & 0x7F
        value >>= 7
    bytes_out.insert(0, buffer)
    return bytes(bytes_out)


def _summary(text: str, notes: list[Note], midi_path: Path, wav_path: Path, options: ConversionOptions) -> str:
    preview = text[:500] + ("…" if len(text) > 500 else "")
    return (
        "# PDF to Musica Conversion\n\n"
        f"- Notes generated: {len(notes)}\n"
        f"- BPM: {options.bpm}\n"
        f"- MIDI: `{midi_path.name}`\n"
        f"- WAV: `{wav_path.name}`\n\n"
        "## Text preview\n\n"
        f"{preview}\n"
    )
