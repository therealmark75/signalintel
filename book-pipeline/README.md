# Book Pipeline

A free, local replacement for paid book-formatting tools (Atticus, Vellum). You
write in Markdown; one command produces a print-ready PDF and a store-ready
EPUB. No subscription, no lock-in, the files never leave your machine.

## What it gives you

- **Print PDF**: a real trade-paperback interior. 6x9 trim, mirrored margins,
  justified text with hyphenation, a title page, a copyright page, chapter
  openings, small-caps running heads, centered page numbers that skip the front
  matter, and a star ornament for scene breaks.
- **EPUB**: a valid EPUB 3 (Kindle, Apple Books, Kobo) split into one file per
  chapter, with a table of contents and metadata.

## What you need

Two free tools:

| Tool | Does | Install |
|---|---|---|
| [Pandoc](https://pandoc.org) | Markdown to EPUB, and Markdown to Typst | `brew install pandoc` (Mac), `apt install pandoc` (Linux) |
| [Typst](https://typst.app) | typesets the print PDF | `brew install typst`, or download the binary from GitHub releases |

## Daily workflow

1. Write your book in `manuscript/`, one Markdown file per chapter. Prefix files
   with numbers so they order correctly: `01-intro.md`, `02-chapter.md`, and so
   on. Start each file with a single `# Chapter Title` line.
2. Run the build:

   ```bash
   ./build.sh          # both PDF and EPUB
   ./build.sh pdf      # print PDF only
   ./build.sh epub     # EPUB only
   ```

3. Find the results in `output/` (`book.pdf`, `book.epub`). That folder is
   git-ignored; the manuscript and templates are the source of truth.

## Writing in Markdown

Everything you need for prose maps to clean output:

| You write | You get |
|---|---|
| `# Title` | a new chapter (new page, eyebrow, centered title) |
| `## Heading` | a bold sub-section heading |
| `*word*` | italic |
| `**word**` | bold |
| `> quoted line` | an indented, italic block quotation |
| `---` on its own line | a centered star scene-break |
| `[text](url)` | a link (live in EPUB) |
| `[^1]` footnotes | footnotes |

## Customizing the print look

Open `templates/book.typ` and edit the `CONFIG` block at the top:

- `title`, `subtitle`, `author` for the title page.
- `trim` for the page size. 6x9 is the common paperback; `(width: 5in, height:
  8in)` and `(width: 5.5in, height: 8.5in)` are also standard.
- `body-font`: `"Libertinus Serif"` (default) or `"New Computer Modern"`, both
  bundled with Typst. Any font installed on your system works too.
- `body-size` and `indent`.

Margins, running heads, the chapter-opening style, and the scene-break ornament
are defined just below CONFIG and are commented so you can adjust them.

## EPUB metadata and cover

Edit `metadata.yaml` for everything the stores display: title, author,
description (your back-cover blurb), language, subjects. To add a cover,
drop a `1600x2560` px image in the folder and uncomment the `cover-image:`
line.

## Known limitations (the honest list)

This covers prose books well. It does not yet do:

- **Automatic drop caps** on chapter openings. Doing this reliably on
  Pandoc-generated content is fiddly; it was removed rather than shipped broken.
- **Complex tables and figures** in the print PDF. Pandoc's standalone Typst
  template defines extra helpers for these; only `blockquote` and
  `horizontalrule` are wired up here. Prose-with-occasional-quote is the target.
- **EPUB validation**: run `epubcheck output/book.epub` before publishing if you
  want a guarantee the retailer will accept it.

These are the gap between this and a polished commercial tool. For a text-driven
book, the output is genuinely retail-grade; for heavy design work, a paid tool
still earns its price.

## How this maps to the paid product

The paid tools bundle an editor, a theme picker, and this formatting engine
behind one subscription. Here the "editor" is any Markdown editor you already
like, the "themes" are a short, readable Typst file you own outright, and the
engine is two open-source binaries. The trade is convenience for control and
cost: you give up a polished GUI and gain a pipeline that is free, scriptable,
versionable in git, and yours forever.
