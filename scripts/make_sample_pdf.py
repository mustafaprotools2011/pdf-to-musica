from pathlib import Path
from reportlab.pdfgen import canvas

out = Path('sample-strategy.pdf')
pdf = canvas.Canvas(str(out))
pdf.drawString(72, 720, 'PDF to Musica MVP strategy: upload, convert text to melody, download WAV and MIDI.')
pdf.drawString(72, 700, 'Launch quickly, monetize with premium styles, and share generated music online.')
pdf.save()
print(out)
