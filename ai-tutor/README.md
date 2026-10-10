# Tutor feedback: setup and reporting

The Socratic tutor can ask students how it is working and send their answers to
a spreadsheet you own. This directory holds the two pieces that make that work:

- `feedback-endpoint.gs` — the Google Apps Script that receives a note and
  appends it to a sheet.
- `../scripts/tutor_feedback_report.py` — turns the sheet's CSV export into a
  readable report.

Until you finish the setup below, `FEEDBACK_URL` in `assets/gemini-tutor.html`
stays `""`, the feedback button stays hidden, and nothing is ever sent.

## One-time setup (about two minutes)

1. **Make a spreadsheet.** Go to <https://sheets.new> and give it a name, say
   *MATH 14 tutor feedback*. Use the **personal Google account** you use for the
   tutor's API key — a university account may refuse step 4.

2. **Open the script editor.** In that sheet: **Extensions → Apps Script**.
   Delete the stub `myFunction` and paste in all of `feedback-endpoint.gs`, then
   save (the disk icon).

3. **Deploy it.** **Deploy → New deployment**; click the gear next to *Select
   type* and choose **Web app**. Set:
   - *Description*: anything, e.g. `tutor feedback v1`
   - *Execute as*: **Me**
   - *Who has access*: **Anyone**  ← this matters; "Anyone with Google account"
     would force every student to sign in
   Click **Deploy** and authorize when Google asks. Because the script is your
   own and unverified, you will pass through *Advanced → Go to … (unsafe)*;
   that warning is about unpublished scripts, not about this one being harmful.

4. **Copy the Web app URL.** It ends in `/exec` and looks like
   `https://script.google.com/macros/s/AKfy…/exec`.

5. **Wire it in.** In `assets/gemini-tutor.html`, set

   ```js
   const FEEDBACK_URL = "https://script.google.com/macros/s/AKfy…/exec";
   ```

   then rebuild and deploy the site (`pretext build web`, publish to
   `gh-pages`). The **feedback** button appears in the panel header, and a
   one-line invitation is added when a student's hints on a problem run out.

6. **Check it once.** Open a problems page, click **feedback**, send a test
   note, and confirm a row appears in the sheet's *Feedback* tab.

### If your university account blocks step 3

Workspace administrators can forbid deploying a web app to "Anyone". If the
option is missing or the deployment is refused, redo steps 1–4 signed in with a
personal Gmail. This is the same restriction that makes students use a personal
account for the Gemini key.

### Changing the script later

Apps Script keeps serving the *deployed* version, not the saved one. After
editing, use **Deploy → Manage deployments → (pencil) → Version: New version →
Deploy** to publish the change at the same URL, so `FEEDBACK_URL` never changes.

## What a submission contains

| column | what it holds |
| --- | --- |
| `received`, `sentAt` | when the sheet got it; when the browser sent it |
| `session` | random per-browser id (`s-4f2a…`), so several notes from one student group together — it identifies a browser, never a person |
| `page`, `section` | e.g. `sec-exercises-hw3-online.html`, `Assignment 3` |
| `problem`, `hintsUsed` | the problem selected in the picker and hints spent on it |
| `model`, `modelUsed` | which model the student had chosen (`careful` / `quick`) and the concrete id that answered (`gemini-3.8-flash`, `gemini-3.5-flash-lite`, …) — the report compares ratings between them. Notes sent before August 2026 carry the older `pro` / `flash` names |
| `rating` | one of *helped a lot*, *helped a little*, *did not help*, *made things worse* (blank if they only wrote a comment) |
| `comment` | the open-ended answer to "How could the tutor be better?" |
| `transcript` | the conversation, **only** when the student ticked the box |
| `device` | `small 390x844` / `large 1512x860` — enough to spot phone-only problems |

No name, no email, no student id, and never the student's API key. The panel
tells students exactly this before they send.

## Getting a report

In the sheet: **File → Download → Comma-separated values**, then

```bash
python3 scripts/tutor_feedback_report.py ~/Downloads/feedback.csv
```

for a summary in the terminal, or

```bash
python3 scripts/tutor_feedback_report.py ~/Downloads/feedback.csv --html report.html
```

for a self-contained page. Useful flags: `--since 2026-09-01` to limit the
window, `--assignment 3` to focus on one assignment, `--transcripts` to include
the attached conversations in full.

You can also hand the CSV to Claude Code in this repo and ask for the report —
it will run this script and can publish the result as a shareable page.
