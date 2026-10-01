/* ------------------------------------------------------------------ *
 * math-input-palette.js
 *
 * Adds a small equation-entry palette to the answer boxes of selected
 * dynamic exercises.  The boxes are plain text inputs graded by the
 * Runestone "fillintheblank" component, which parses the ASCII syntax
 * pi, ^, /, sqrt(), ln(), exp().  The palette does not replace that
 * syntax with a rendered field: it inserts exactly the characters the
 * grader expects, at the caret, so what a student sees in the box is
 * always what gets submitted.
 *
 * Runestone builds the inputs at run time from the JSON embedded in the
 * page, so the palette is attached from a MutationObserver rather than
 * on DOMContentLoaded.
 *
 * To put a palette on another exercise, add its xml:id to EXERCISES.
 * ------------------------------------------------------------------ */
(function () {
  "use strict";

  /* xml:id of every exercise that should get a palette. */
  var EXERCISES = ["ex-r3o-area-change-of-variables"];

  /* label    what gets inserted   where the caret lands afterwards
   * ---------------------------------------------------------------- */
  var KEYS = [
    { label: "π",        insert: "pi",      caret: 2, title: "pi" },
    { label: "xʸ",       insert: "^",       caret: 1, title: "power" },
    { label: "a/b",           insert: "/",       caret: 1, title: "divide" },
    { label: "×",        insert: "*",       caret: 1, title: "multiply" },
    { label: "( )",           insert: "()",      caret: 1, title: "parentheses" },
    { label: "√",        insert: "sqrt()",  caret: 5, title: "square root" },
    { label: "ln",            insert: "ln()",    caret: 3, title: "natural logarithm" },
    { label: "eˣ",       insert: "exp()",   caret: 4, title: "exponential" }
  ];

  var STYLE_ID = "math-input-palette-style";
  var CSS = [
    ".mip-bar{display:flex;flex-wrap:wrap;gap:.3rem;align-items:center;",
    "margin:.6rem 0 .8rem;padding:.45rem .55rem;border:1px solid rgba(128,128,128,.45);",
    "border-radius:6px;background:rgba(128,128,128,.07);}",
    ".mip-bar .mip-label{font-size:.85rem;opacity:.8;margin-right:.25rem;}",
    ".mip-key{font:inherit;font-size:.95rem;line-height:1;min-width:2.3rem;",
    "padding:.35rem .5rem;cursor:pointer;border:1px solid rgba(128,128,128,.55);",
    "border-radius:4px;background:rgba(255,255,255,.75);color:inherit;}",
    ".mip-key:hover{background:rgba(0,114,178,.15);}",
    ".mip-key:focus{outline:2px solid rgba(0,114,178,.7);outline-offset:1px;}",
    ".mip-bar .mip-hint{font-size:.8rem;opacity:.75;flex-basis:100%;}",
    "@media (prefers-color-scheme:dark){.mip-key{background:rgba(0,0,0,.35);}}"
  ].join("");

  function addStyleOnce() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.appendChild(document.createTextNode(CSS));
    document.head.appendChild(s);
  }

  /* Insert `text` at the caret of `input`, then place the caret at
   * `offset` characters into the inserted text and hand focus back. */
  function insertAtCaret(input, text, offset) {
    var start = input.selectionStart, end = input.selectionEnd;
    if (typeof start !== "number") { start = end = input.value.length; }
    input.value = input.value.slice(0, start) + text + input.value.slice(end);
    var pos = start + offset;
    input.focus();
    try { input.setSelectionRange(pos, pos); } catch (e) { /* older browsers */ }
    /* Let Runestone see the edit as if it had been typed. */
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function buildBar(container) {
    var bar = document.createElement("div");
    bar.className = "mip-bar";
    bar.setAttribute("role", "group");
    bar.setAttribute("aria-label", "Equation entry palette");

    var lab = document.createElement("span");
    lab.className = "mip-label";
    lab.textContent = "Insert:";
    bar.appendChild(lab);

    KEYS.forEach(function (k) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "mip-key";
      b.textContent = k.label;
      b.title = k.title + "  →  " + k.insert;
      b.setAttribute("aria-label", k.title);
      /* mousedown, not click: acting before focus leaves the input means
       * the caret position is still the one the student was editing. */
      b.addEventListener("mousedown", function (ev) {
        ev.preventDefault();
        var target = container.__mipActive;
        if (!target || !container.contains(target)) {
          target = container.querySelector('input[type="text"]');
        }
        if (target) insertAtCaret(target, k.insert, k.caret);
      });
      bar.appendChild(b);
    });

    var hint = document.createElement("span");
    hint.className = "mip-hint";
    hint.textContent =
      "Click a box, then a button. Answers are exact, so type pi rather " +
      "than 3.14159 — for example pi*8^3/2.";
    bar.appendChild(hint);

    return bar;
  }

  function attach(container) {
    if (container.dataset.mipDone === "yes") return;
    var inputs = container.querySelectorAll('input[type="text"]');
    if (!inputs.length) return;          /* not rendered yet */
    container.dataset.mipDone = "yes";
    addStyleOnce();

    /* Remember which box the student was last editing. */
    Array.prototype.forEach.call(inputs, function (inp) {
      inp.addEventListener("focus", function () {
        container.__mipActive = inp;
      });
    });
    container.__mipActive = inputs[0];

    container.insertBefore(buildBar(container), container.firstChild);
  }

  function containers() {
    return EXERCISES
      .map(function (id) { return document.getElementById("rs-" + id); })
      .filter(Boolean);
  }

  function sweep() { containers().forEach(attach); }

  function start() {
    sweep();                              /* in case it is already there */
    var pending = containers();
    if (!pending.length) return;
    var obs = new MutationObserver(function () {
      sweep();
      if (containers().every(function (c) { return c.dataset.mipDone === "yes"; })) {
        obs.disconnect();
      }
    });
    pending.forEach(function (c) {
      obs.observe(c, { childList: true, subtree: true });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
