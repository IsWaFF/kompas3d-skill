"""Extract embedded images (task figures) and text from an assignment PDF.
Usage (host python venv with pypdf+pillow):  python pdf_images.py file.pdf outdir [page ...]
Pages are 1-based; without pages, extracts all.
"""
import os
import sys

import pypdf

if len(sys.argv) < 3:
    sys.exit(__doc__)
pdf, out = sys.argv[1], sys.argv[2]
pages = [int(p) for p in sys.argv[3:]]
os.makedirs(out, exist_ok=True)
r = pypdf.PdfReader(pdf)
for n, page in enumerate(r.pages, 1):
    if pages and n not in pages:
        continue
    with open(os.path.join(out, f'p{n}.txt'), 'w') as f:
        f.write(page.extract_text() or '')
    for i, im in enumerate(page.images):
        fn = os.path.join(out, f'p{n}_{i}_{im.name}')
        with open(fn, 'wb') as f:
            f.write(im.data)
        print(fn, im.image.size)
