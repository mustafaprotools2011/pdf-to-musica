from __future__ import annotations

import argparse
from pathlib import Path

from .converter import ConversionOptions, convert_pdf_to_music


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert a PDF into MIDI and WAV music.")
    parser.add_argument("pdf", type=Path, help="Path to a text-based PDF")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="Directory for generated files")
    parser.add_argument("--bpm", type=int, default=120, help="Tempo in beats per minute")
    parser.add_argument("--max-notes", type=int, default=96, help="Maximum notes to generate")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = convert_pdf_to_music(
        args.pdf,
        output_dir=args.output_dir,
        options=ConversionOptions(bpm=args.bpm, max_notes=args.max_notes),
    )
    print(f"Generated {result.note_count} notes")
    print(f"MIDI: {result.midi_path}")
    print(f"WAV: {result.wav_path}")
    print(f"Summary: {result.summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
