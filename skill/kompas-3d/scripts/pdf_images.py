"""Extract embedded images (task figures) and text from an assignment PDF.
Usage (host python venv with pypdf+pillow):  python pdf_images.py file.pdf outdir [page ...]
Pages are 1-based; without pages, extracts all.
"""
import sys, os
import pypdf

pdf, out = sys.argv[1], sys.argv[2]
pages = [int(p) for p in sys.argv[3:]]
os.makedirs(out, exist_ok=True)
r = pypdf.PdfReader(pdf)
for n, page in enumerate(r.pages, 1):
    if pages and n not in pages:
        continue
    open(os.path.join(out, f'p{n}.txt'), 'w').write(page.extract_text() or '')
    for i, im in enumerate(page.images):
        fn = os.path.join(out, f'p{n}_{i}_{im.name}')
        open(fn, 'wb').write(im.data)
        print(fn, im.image.size)
