from __future__ import annotations

import argparse
from pathlib import Path

from .converter import ConversionOptions, convert_pdf_to_mxl, default_audiveris_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert sheet-music PDF files to compressed MusicXML .mxl files.")
    parser.add_argument("pdf", type=Path, help="Path to a sheet-music PDF")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="Directory for generated .mxl files")
    parser.add_argument(
        "--audiveris-command",
        default=default_audiveris_command(),
        help="Audiveris executable name/path. Example: C:/Program Files/Audiveris/Audiveris.exe",
    )
    parser.add_argument("--timeout", type=int, default=600, help="Audiveris timeout in seconds")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = convert_pdf_to_mxl(
        args.pdf,
        output_dir=args.output_dir,
        options=ConversionOptions(audiveris_command=args.audiveris_command, timeout_seconds=args.timeout),
    )
    print(f"Generated MXL: {result.mxl_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
