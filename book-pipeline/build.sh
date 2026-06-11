#!/usr/bin/env bash
# ============================================================================
# Build a print PDF and an EPUB from the Markdown manuscript.
#
#   ./build.sh          build both PDF and EPUB
#   ./build.sh pdf      build the print PDF only
#   ./build.sh epub     build the EPUB only
#
# Requires: pandoc (EPUB + Markdown->Typst) and typst (print PDF).
# Authoring happens in manuscript/*.md. Nothing here edits your text.
# ============================================================================
set -euo pipefail

cd "$(dirname "$0")"
OUT="output"
mkdir -p "$OUT"

# Chapters build in filename order, so prefix them 01-, 02-, 03-...
shopt -s nullglob
CHAPTERS=(manuscript/*.md)
if [ ${#CHAPTERS[@]} -eq 0 ]; then
  echo "No chapters found in manuscript/. Add 01-something.md and retry." >&2
  exit 1
fi

target="${1:-all}"

build_pdf() {
  command -v typst >/dev/null || { echo "typst not installed." >&2; exit 1; }
  echo "PDF  : converting Markdown to Typst..."
  # Body only (no -s): the template in templates/book.typ supplies the page
  # setup, fonts, running heads, title page, and chapter styling.
  pandoc "${CHAPTERS[@]}" -t typst -o "$OUT/body.typ"
  echo "PDF  : typesetting print interior..."
  # --root . lets the template include "/output/body.typ" from the project root.
  typst compile --root . templates/book.typ "$OUT/book.pdf"
  echo "PDF  : wrote $OUT/book.pdf"
}

build_epub() {
  command -v pandoc >/dev/null || { echo "pandoc not installed." >&2; exit 1; }
  echo "EPUB : building..."
  pandoc metadata.yaml "${CHAPTERS[@]}" \
    --toc --toc-depth=1 \
    --split-level=1 \
    -o "$OUT/book.epub"
  echo "EPUB : wrote $OUT/book.epub"
}

case "$target" in
  pdf)  build_pdf ;;
  epub) build_epub ;;
  all)  build_pdf; build_epub ;;
  *)    echo "Usage: ./build.sh [pdf|epub|all]" >&2; exit 1 ;;
esac

echo "Done."
