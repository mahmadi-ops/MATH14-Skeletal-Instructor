# MATH 14 — Skeletal Notes

PreTeXt book of *skeletal* (fill-in) lecture notes for SCU's MATH 14
(vector calculus: line integrals, multiple integrals, and the big
theorems). Students complete them by hand — printed, or annotated on an
iPad over the PDF — while the derivation is done in class.

Deployed to GitHub Pages by `.github/workflows/pretext-deploy.yml`.

## Where the content comes from

This repository started as a copy of the **completed** MATH 14 notes, and
the 18 lecture sections of `source/` were then hollowed out **in place**:
same file names, same `xml:id`s, same figures. There is no parallel set of
`sec-skel-*` files and no `skel-` prefix, unlike the MATH 13 skeletal book
(`mahmadi-ops/M13-Skeletal-Instructor`), because here the skeletal version
*is* the book. The completed notes live in their own repository; to see what
a box used to contain, look there, or at this repository's history before
the skeletonizing commits.

The book has four chapters. The first three are the skeletal sections:

| Chapter | Files |
| --- | --- |
| 1 · Line Integrals | `section-parametrization`, `section-arc-length`, `section-line-integrals`, `section-vector-fields`, `conservative-fields` |
| 2 · Multiple Integrals | `double-integrals-rectangles`, `double-integrals-general-regions`, `polar-coordinates`, `double-integrals-polar-form`, `triple-integrals-rectangular`, `triple-integrals-cylindrical`, `triple-integrals-spherical`, `mass-center-of-mass`, `jacobian-substitution`, `surface-integrals` |
| 3 · The Big Theorems | `greens-theorem`, `stokes-theorem`, `divergence-theorem` |

The fourth, **Assignments and Review Problems** (`hw*-online.ptx`,
`review*-practice.ptx`, plus the `hw*-exercises`/`hw*-solutions` files they
include), is **not skeletal** and must not be touched by a skeletonizing
pass: those are the auto-graded problem sets with the AI tutor, and their
solutions are released per assignment through `<version include="..."/>`
in `publication/publication.ptx` (see the comment there). The skeletal
sections cite ids in these files and vice versa; every `xml:id` was kept
so that nothing had to be rewired.

Section 3.1 (`greens-theorem.ptx`) has its own layout (Nov 2026, at the
instructor's request): two subsections, *Flux and Divergence* and
*Circulation and Curl*, each running from its operator through its line
integral to its form of Green's theorem, with what uses both in the
Concept Check, and the derivations of the outward unit normal and of the
flux element written out as in the completed notes. The old subsection
ids live on as subsubsections. The file is the same in this book and in
the student book (`mahmadi-ops/MATH14-Skeletal`), and the completed notes
(`MATH-14-Instructor`, `MATH-14`) share the layout; keep the four in step.

`section-arc-length-old.ptx`, `cone-plane-arc-length.ptx`,
`cylindrical-element-instructions.ptx` and `hw1-paragraphs.ptx` are not
included from `main.ptx`; leave them alone.

## The skeletonizing recipe

See `.claude/skills/skeletonize/SKILL.md` for the full rules and the
helper scripts. In short:

- **Keep** objectives, definitions, theorem statements, `assemblage`
  summaries, problem statements, videos, interactives, and every figure
  that is either part of a statement or the *check* on a computation.
- **Replace** every derivation, proof, worked solution and Concept Check
  answer with a blank `latex-image` workspace box (15 wide, height to
  fit, faint rules between labelled rows), preceded by a **one- to
  three-sentence parenthetical instruction** naming what to do and which
  numbered result to use — not how. The calibration target is
  `source/section-parametrization.ptx`, which mirrors the MATH 13 book's
  `sec-skel-geom-parametrization.ptx`.
- A numbered result that a later section or an assignment cites
  (`eq-mass-speed`, `eq-polar-area-element`, `eq-sphere-cross`, …) is
  restated in an `<assemblage>` right after the box that derives it, so
  the id survives.
- Figures that *answer* an exercise (the parabola plotted from a table,
  a region of integration the student must find, a projection) become
  empty grids to draw on, under the same `xml:id`. Captions that stated an
  answer are trimmed to "compare with what you found".
- Each section file opens with a comment recording what was kept, what
  was hollowed, and what was done with the figures.

## Building

```bash
pretext build web        # output/web
pretext build print      # output/print (the PDF students annotate)
scripts/build-site.sh    # both, with the PDF copied into output/web
pretext view web
```

Check well-formedness and cross-references before a build — it is far
faster than reading the log:

```bash
python3 .claude/skills/skeletonize/xrefs.py --check
```

### The PDF button

The navbar carries a **PDF** button linking to `math14-skeletal-notes.pdf`
next to the HTML pages. Three pieces have to stay in step:

- `project.ptx` — the print target's `output-filename`.
- `scripts/build-site.sh` — copies that file into `output/web/`.
- `assets/custom.js` — `PDF_HREF`, the button it injects into the navbar.

`scripts/build-site.sh` is what CI runs; a plain `pretext build web`
leaves the button hidden (it checks for the file before showing itself).

Do **not** give the print target a `deploy-dir`: that makes it a deploy
target, which switches `pretext deploy` to Pelican and would publish all of
`output/print` rather than the one PDF.

### Two root files

`source/main.ptx` is the web book; `source/main-print.ptx` is the root of
the print and latex targets and differs only in leaving out the
"Assignments and Review Problems" chapter and using
`frontmatter-print.ptx` (no `introduction.ptx`, which is about the web
features). The Runestone fill-in problems print as their regex answer
patterns plus "Correct." feedback lines, so that chapter is web-only. The
shared `<docinfo>` lives in `source/docinfo.ptx`. A structural change to
`main.ptx` (a new chapter or section) must be mirrored in
`main-print.ptx`; nothing in the print tree may `<xref>` into the problems
chapter.

### Two publication files

`publication/publication.ptx` (web) and `publication/publication-print.ptx`
(print, latex) must carry the same `<version include="..."/>` list, so a
released set of solutions appears in both the site and the PDF. Edit both
when releasing.

### Videos and interactives in the PDF

Every `<video>` in the sections carries `preview="play-button.png"`
(`assets/play-button.png`, a plain play-button still): PreTeXt prints a
local-file video as its preview image plus a QR code, and without a
preview it prints "BUG: PREVIEW NOT HANDLED". (`preview="generic"` needs
a play-button asset that pretext 2.37.1 did not ship.) Interactives get
an automatic screenshot plus a QR code. Both QR codes are absolute links
built from `<baseurl>` in the publication files, which must be the deployed
site's address. A new video needs the attribute too.

## Traps

- XML comments may not contain `--` (write the aside in parentheses).
- A bare `<` or `>` inside a `latex-image` that is not wrapped in `CDATA`
  has to be written `&lt;` / `&gt;`. The empty grids use `CDATA` for this
  reason (`>=stealth`).
- `\$` in a `latex-image` is a *literal* dollar, so any math after it lands
  in text mode and LaTeX fails.
- The print build can exhaust xelatex's main memory on a book with
  hundreds of tikz pictures; the workflow raises `extra_mem_top`/`_bot`,
  and `scripts/build-site.sh` refuses a truncated PDF by page count.
