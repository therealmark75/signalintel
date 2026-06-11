// ============================================================================
// Print interior template (trade paperback). This is the part you would
// otherwise pay for: real book typesetting. Edit the CONFIG block to taste.
//
// It does NOT contain the manuscript text. build.sh converts your Markdown
// chapters to Typst and drops them at /output/body.typ, which is included
// near the bottom. Author your book in manuscript/, never here.
// ============================================================================

// ----------------------------------------------------------------- CONFIG ---
#let book = (
  title: "Your Book Title",
  subtitle: "An Optional Subtitle",
  author: "Your Name",
  // Standard self-publishing trim sizes: 6x9 (most common), 5x8, 5.5x8.5.
  trim: (width: 6in, height: 9in),
  body-font: "Libertinus Serif",   // also bundled: "New Computer Modern"
  body-size: 11pt,
  // First-line indent for paragraphs (set to 0pt for a block/modern look).
  indent: 1.5em,
)
// ------------------------------------------------------------- END CONFIG ---

#set document(title: book.title, author: book.author)

#set page(
  width: book.trim.width,
  height: book.trim.height,
  margin: (inside: 0.875in, outside: 0.625in, top: 0.85in, bottom: 0.85in),
)

#set text(font: book.body-font, size: book.body-size, lang: "en")

#set par(
  justify: true,
  leading: 0.72em,
  first-line-indent: (amount: book.indent, all: false),
  linebreaks: "optimized",
)

// Tighter, balanced headings inside the body (sub-sections).
#show heading.where(level: 2): it => {
  v(1.1em, weak: true)
  set text(size: 13pt, weight: "bold")
  block(it.body)
  v(0.35em, weak: true)
}

// ---------------------------------------------------------- TITLE PAGE -------
#page(numbering: none, header: none, footer: none)[
  #set align(center + horizon)
  #text(size: 30pt, weight: "regular")[#book.title]
  #if book.subtitle != none and book.subtitle != "" [
    #v(0.6em)
    #text(size: 15pt, style: "italic", fill: rgb("#444"))[#book.subtitle]
  ]
  #v(2.2em)
  #text(size: 13pt, tracking: 0.12em)[#upper(book.author)]
]

// Copyright / colophon page (back of title page).
#page(numbering: none, header: none, footer: none)[
  #set align(left + bottom)
  #set text(size: 9pt, fill: rgb("#333"))
  Copyright © #datetime.today().year() #book.author. \
  All rights reserved. \
  #v(0.4em)
  Typeset with Typst. Cover and interior by the author.
]

// ---------------------------------------------------- RUNNING HEAD + FOLIO ---
// Pages now get a running header (author verso, title recto) and centered
// page numbers. Numbering restarts at 1 here so front matter is not counted.
#set page(
  numbering: "1",
  number-align: center,
  header: context {
    // Suppress the running head on pages where a chapter opens.
    let page-no = counter(page).get().first()
    let headings = query(heading.where(level: 1))
    let opens-here = headings.any(h =>
      counter(page).at(h.location()).first() == page-no)
    if opens-here { return }
    set text(size: 9pt, tracking: 0.06em, fill: rgb("#555"))
    if calc.odd(page-no) {
      align(center, smallcaps(book.title))
    } else {
      align(center, smallcaps(book.author))
    }
  },
)
#counter(page).update(1)

// ----------------------------------------------------- CHAPTER OPENINGS ------
// Level-1 headings begin a new page, sit low, with a "CHAPTER" eyebrow.
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(1.6in)
  set align(center)
  set text(size: 11pt, weight: "regular", tracking: 0.25em, fill: rgb("#777"))
  // Small "CHAPTER" eyebrow above the title is a common book convention; the
  // title text itself comes from your Markdown "# " heading.
  block(below: 0.8em)[#upper("Chapter")]
  set text(size: 22pt, weight: "regular", tracking: 0em, fill: black)
  block(it.body)
  v(1.4em)
}

// --------------------------------------------------- BODY HELPER DEFS -------
// Pandoc's Typst body references a couple of helpers that its standalone
// template would normally define. We inject the body only, so we define them
// here and get to style them the way a typesetter would.

// Block quotation: indented, ragged, slightly smaller.
#let blockquote(body) = pad(left: 1.4em, right: 1.4em)[
  #set text(size: 10.5pt, style: "italic", fill: rgb("#333"))
  #set par(first-line-indent: 0pt, justify: false)
  #body
]

// Thematic break ("---" in Markdown) becomes a centred star-divider, the
// classic scene-break ornament, instead of a printed rule.
#let horizontalrule = block(width: 100%, above: 1.2em, below: 1.2em)[
  #set align(center)
  #text(size: 12pt, tracking: 0.5em, fill: rgb("#888"))[#sym.ast #sym.ast #sym.ast]
]

// ------------------------------------------------------------- MANUSCRIPT ----
// We eval (not include) so the helper definitions above are in scope for the
// Pandoc-generated body. Document-level show/set rules still apply to it.
#eval(
  read("/output/body.typ"),
  mode: "markup",
  scope: (blockquote: blockquote, horizontalrule: horizontalrule),
)
