# PDF to Musica 🎼

Convert **sheet music PDFs** into **MusicXML compressed `.mxl` files**.

This project is not an AI music generator. It is an Optical Music Recognition (OMR) wrapper: it takes a PDF that contains printed music notation and exports editable MusicXML/MXL using [Audiveris](https://github.com/Audiveris/audiveris).

## MVP

- Upload a sheet-music PDF
- Run Audiveris OMR
- Export `.mxl` / MusicXML
- Download the converted file
- CLI for batch conversion
- Streamlit web UI
- Tests and GitHub Actions

## Requirement

Install Audiveris first and make the `audiveris` command available in PATH.

Audiveris: https://github.com/Audiveris/audiveris

On many systems you also need Java installed.

## Quick start

```bash
uv run --extra dev pytest -q
uv run streamlit run app.py
```

## CLI

```bash
uv run pdf-to-musica path/to/sheet-music.pdf --output-dir outputs
```

If Audiveris is not in PATH:

```bash
uv run pdf-to-musica score.pdf --audiveris-command "C:/path/to/audiveris/bin/audiveris.bat"
```

## Deploy fast

For production, deploy this as a small web app on a VM/container where Audiveris + Java are installed. Streamlit Cloud may not be ideal because system-level Audiveris installation is required.

Recommended cheap deployment:

- Hetzner / DigitalOcean small VM
- Docker image with Java + Audiveris + this app
- Caddy/Nginx reverse proxy

## Monetization

- Free: 1–3 PDF conversions/day
- Pro: $9/month for batch conversion and larger scores
- Studio: $29/month for high-priority conversion and API access
- B2B: API for music schools, publishers, and notation apps

## Accuracy note

PDF-to-MXL conversion quality depends on scan quality and score complexity. Clean digital PDFs convert best. Scanned/blurred sheets may require manual correction after export.
