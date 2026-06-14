# PDF to Musica 🎼

Turn any text-based PDF into deterministic music. Upload a PDF, extract its words, convert those words into a melody, then download both MIDI and WAV files.

## MVP

- PDF text extraction
- Deterministic text → melody engine
- MIDI export
- Synthesized WAV preview/download
- Streamlit web app
- CLI for automation
- Pytest test suite

## Quick start

```bash
uv run --extra dev pytest -q
uv run python scripts/make_sample_pdf.py
uv run pdf-to-musica sample-strategy.pdf --output-dir outputs --bpm 110 --max-notes 32
uv run streamlit run app.py
```

## CLI

```bash
pdf-to-musica path/to/file.pdf --output-dir outputs --bpm 120 --max-notes 96
```

## Deploy fast

### Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io/.
3. Select the repo and set entrypoint to `app.py`.
4. Deploy.

### Hugging Face Spaces

1. Create a new Space with Streamlit SDK.
2. Push this repo.
3. Space will run `app.py`.

## Monetization

- Free: 3 conversions/day, watermark in summary.
- Pro: $5/month for longer PDFs, more notes, and no watermark.
- Creator pack: $15/month for premium instruments, batch conversion, commercial license.
- B2B: API for educators, content creators, and accessibility/music learning tools.

## Next revenue features

- Stripe checkout + account limits.
- Better instruments via SoundFont or hosted audio model.
- OCR for scanned PDFs.
- Shareable public track pages.
- Batch PDF conversion for agencies.

## Tech notes

The current engine is deterministic: the same PDF text and settings produce the same melody. It intentionally avoids expensive AI inference so the MVP can run almost free on Streamlit/HF.
