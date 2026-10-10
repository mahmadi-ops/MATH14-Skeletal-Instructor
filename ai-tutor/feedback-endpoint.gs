/**
 * MATH 14 Socratic tutor — feedback collector.
 *
 * A Google Apps Script web app that receives the notes students send from the
 * tutor panel and appends each one as a row of a spreadsheet you own. Paste
 * this file into the Apps Script editor of a new Google Sheet and deploy it as
 * a web app; the step-by-step is in README.md next to this file.
 *
 * Nothing here identifies a student: the widget sends a random per-browser id,
 * never a name, an email, or an API key.
 */

var SHEET_NAME = 'Feedback';

var HEADERS = [
  'received',    // when this server saw it
  'sentAt',      // when the student's browser sent it
  'session',     // random per-browser id, not a person
  'page',        // e.g. sec-exercises-hw3-online.html
  'section',     // e.g. Assignment 3
  'problem',     // the problem selected in the picker
  'hintsUsed',   // hints spent on that problem when the note was written
  'rating',
  'comment',
  'transcript',  // only when the student ticked the box
  'device',
  // Appended, not inserted: a sheet that has been collecting since before
  // these existed keeps every old row aligned under the header it was written
  // with, and simply gains two more columns from here on. New fields must
  // always be added at the END for that reason.
  'model',       // which model the student had chosen: pro | flash
  'modelUsed',   // the concrete model id that answered, e.g. gemini-3.8-flash
];

// Generous ceilings, purely so a runaway or malicious post cannot bloat the
// sheet. A real comment is nowhere near these.
var LIMITS = { comment: 4000, transcript: 20000, field: 300 };

// The four from the written form, plus the two the one-tap rating under a hint
// sends. Kept distinct on purpose: a thumb is a reflex about one hint, a form
// answer is a considered verdict on the tutor, and reading them apart matters.
var RATINGS = ['helped a lot', 'helped a little', 'did not help', 'made things worse',
               'thumbs up', 'thumbs down'];

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) || '';
    var d = JSON.parse(raw || '{}');
    var sheet = getSheet_();
    sheet.appendRow([
      new Date(),
      clip_(d.sentAt, LIMITS.field),
      clip_(d.session, LIMITS.field),
      clip_(d.page, LIMITS.field),
      clip_(d.section, LIMITS.field),
      clip_(d.problem, LIMITS.field),
      Number(d.hintsUsed) || 0,
      rating_(d.rating),
      clip_(d.comment, LIMITS.comment),
      clip_(d.transcript, LIMITS.transcript),
      clip_(d.device, LIMITS.field),
      clip_(d.model, LIMITS.field),
      clip_(d.modelUsed, LIMITS.field),
    ]);
    return json_({ ok: true });
  } catch (err) {
    // Swallow the error into a response rather than throwing: a failed parse
    // should never turn into a 500 the student sees as a broken tutor.
    return json_({ ok: false, error: String(err) });
  }
}

/** Visiting the deployment URL in a browser should say something reassuring. */
function doGet() {
  return json_({ ok: true, service: 'MATH 14 tutor feedback collector' });
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
    return sheet;
  }
  // A sheet created by an older version of this script has a shorter header
  // row than we now write. Name the new columns rather than leaving them
  // blank, so the report can find them; existing rows keep their alignment
  // because new fields are only ever appended.
  var width = sheet.getLastColumn();
  if (width < HEADERS.length) {
    sheet.getRange(1, width + 1, 1, HEADERS.length - width)
         .setValues([HEADERS.slice(width)]);
  }
  return sheet;
}

function clip_(v, n) {
  if (v === null || v === undefined) return '';
  var s = String(v);
  return s.length > n ? s.slice(0, n) + '…[truncated]' : s;
}

/** Keep the rating column to the four known values so it stays countable. */
function rating_(v) {
  var s = String(v || '').trim();
  if (!s) return '';
  return RATINGS.indexOf(s) >= 0 ? s : 'other: ' + clip_(s, 60);
}

/**
 * Every reply is JSON, so a failure reads the same way a success does. The
 * widget posts cross-origin and cannot read this body back — it is here for
 * the instructor, who can open the deployment URL and see the collector
 * answer, and for the doPost catch above.
 */
function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
