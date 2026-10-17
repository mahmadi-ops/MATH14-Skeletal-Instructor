/* ------------------------------------------------------------------ *
 * Floating Socratic AI tutor for the assignment pages.                 *
 *                                                                      *
 * On each of the ten assignment pages of "Assignments and Review       *
 * Problems" (URL starts with "sec-exercises-hw") this adds a chat      *
 * bubble fixed to the lower-right corner. Opening it loads             *
 * external/gemini-tutor.html in a panel that stays in place as the     *
 * student scrolls. The page's exercise STATEMENTS (never the           *
 * solutions, and never the answer-checking data Runestone embeds in    *
 * <script> tags) are harvested before MathJax typesets them — so the   *
 * raw \( ... \) LaTeX is intact — and handed to the tutor via          *
 * postMessage so it knows every problem on the page. The review        *
 * problem sets ("sec-exercises-review...") are left alone.             *
 * ------------------------------------------------------------------ */
(function () {
    var page = window.location.pathname.split("/").pop() || "";
    if (page.indexOf("sec-exercises-hw") !== 0) return;
    var articles = document.querySelectorAll("article.exercise");
    if (!articles.length) return;

    // Harvest statements now, while the DOM still holds raw LaTeX.
    // The <script type="application/json"> blobs inside each Runestone
    // exercise carry the answer patterns and feedback, so scripts are
    // stripped along with the solutions; the answer <input> boxes have
    // no text content, so each is replaced by a visible "___" blank.
    function clean(el) {
        var c = el.cloneNode(true);
        c.querySelectorAll(
            ".solutions, .solution, .hint, .answer, .autopermalink, .knowl-output, iframe, script, style"
        ).forEach(function (n) { n.remove(); });
        c.querySelectorAll("input").forEach(function (n) {
            n.replaceWith(document.createTextNode(" ___ "));
        });
        return c.textContent.replace(/\s+/g, " ").trim();
    }
    var exercises = [];
    articles.forEach(function (a) {
        var heading = a.querySelector(".heading");
        var label = heading ? clean(heading).replace(/\s*\.$/, "") : "Problem";
        var body = a.cloneNode(true);
        var h = body.querySelector(".heading");
        if (h) h.remove();
        exercises.push({ label: label, text: clean(body) });
    });
    var sectionHeading = document.querySelector("section .heading .title");
    var context = {
        type: "math14-exercises",
        // The widget lives in an iframe, so its own location is the widget
        // file; tell it which page of the book it is serving.
        page: page,
        section: sectionHeading ? sectionHeading.textContent.trim() : document.title,
        exercises: exercises,
    };

    // When a student is stuck on how to begin, the most useful thing the tutor
    // can do is send them to a worked example — but it can only name one if it
    // knows which exist. The introduction at the top of this page links the
    // sections the assignment draws on, so read each one's examples (number,
    // title, and the section they sit in) and hand the list over with the
    // problems. These are same-origin pages the student has already been
    // pointed at. Anything that fails is skipped: the tutor then falls back to
    // naming the section, which is what it did before this existed.
    function harvestExamples(done) {
        var links = Array.prototype.slice.call(document.querySelectorAll(
            "section.introduction a.internal[href^='sec-']"
        ));
        if (!links.length || typeof fetch !== "function") return done([]);
        var found = [];
        var pending = links.length;
        links.forEach(function (link) {
            // The link's title attribute reads "Section 1.1: Parametrization
            // of Curves", which is exactly how a student would look it up.
            var section = link.getAttribute("title") || link.textContent.trim();
            fetch(link.getAttribute("href"))
                .then(function (r) { return r.ok ? r.text() : ""; })
                .then(function (html) {
                    if (!html) return;
                    var doc = new DOMParser().parseFromString(html, "text/html");
                    // Headings sit at whatever level the section nests to (h3
                    // in one of these sections, h4 in another), so match on the
                    // class rather than the tag. "example-like" is a family, so
                    // carry the type across instead of assuming every one of
                    // them is an Example.
                    doc.querySelectorAll(".example-like .heading").forEach(function (h) {
                        var number = h.querySelector(".codenumber");
                        var title = h.querySelector(".title");
                        var type = h.querySelector(".type");
                        if (!number) return;
                        found.push({
                            type: type ? type.textContent.trim() : "Example",
                            number: number.textContent.trim(),
                            title: title ? title.textContent.trim().replace(/\.\s*$/, "") : "",
                            section: section,
                        });
                    });
                })
                .catch(function () {})
                .then(function () {
                    if (--pending) return;
                    // Fetches finish in whatever order they finish; the tutor
                    // should see them in the order the book presents them.
                    found.sort(function (a, b) {
                        return a.number.localeCompare(b.number, undefined, { numeric: true });
                    });
                    done(found);
                });
        });
    }

    // Build the bubble + panel.
    var fab = document.createElement("button");
    fab.id = "m14-tutor-fab";
    fab.type = "button";
    fab.setAttribute("aria-label", "Open the AI tutor");
    fab.innerHTML = "&#127891; Tutor";

    var panel = document.createElement("div");
    panel.id = "m14-tutor-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Socratic AI tutor");
    panel.innerHTML =
        '<div id="m14-tutor-bar">' +
        '<span>Socratic tutor &mdash; hints, never answers</span>' +
        '<button type="button" id="m14-tutor-min" aria-label="Minimize">&#8211;</button>' +
        "</div>";
    var frame = null;

    // The examples arrive over the network, so the list may be ready before or
    // after the student opens the panel. Send whatever exists when the widget
    // loads, and send again if the list lands later; the widget keeps the most
    // recent context it is handed.
    var frameReady = false;
    function sendContext() {
        if (frameReady) frame.contentWindow.postMessage(context, "*");
    }
    harvestExamples(function (examples) {
        context.examples = examples;
        sendContext();
    });

    function openPanel() {
        if (!frame) {
            frame = document.createElement("iframe");
            frame.id = "m14-tutor-frame";
            frame.src = "external/gemini-tutor.html";
            frame.addEventListener("load", function () {
                frameReady = true;
                sendContext();
            });
            panel.appendChild(frame);
        }
        panel.classList.add("m14-open");
        fab.style.display = "none";
        try { localStorage.setItem("math14-tutor-open", "1"); } catch (e) {}
    }
    function closePanel() {
        panel.classList.remove("m14-open");
        fab.style.display = "";
        try { localStorage.setItem("math14-tutor-open", "0"); } catch (e) {}
    }

    fab.addEventListener("click", openPanel);
    panel.querySelector("#m14-tutor-min").addEventListener("click", closePanel);

    document.body.appendChild(fab);
    document.body.appendChild(panel);

    var wasOpen = false;
    try { wasOpen = localStorage.getItem("math14-tutor-open") === "1"; } catch (e) {}
    if (wasOpen) openPanel();

    // First visit only: pulse the button twice so new students notice it,
    // then never again on this browser.
    try {
        if (!wasOpen && !localStorage.getItem("math14-tutor-seen")) {
            localStorage.setItem("math14-tutor-seen", "1");
            setTimeout(function () {
                fab.classList.add("m14-pulse");
                fab.addEventListener("animationend", function () {
                    fab.classList.remove("m14-pulse");
                }, { once: true });
            }, 900);
        }
    } catch (e) {}
})();

/* ------------------------------------------------------------------ *
 * "PDF" button in the navigation bar.
 *
 * These are skeletal notes, meant to be completed by hand, so the PDF is
 * the copy students actually work on -- printed, or annotated on an iPad.
 * PreTeXt has no built-in link to it, so we add one to the navbar, styled
 * with the theme's own .button classes so it matches Contents / Search /
 * Prev-Up-Next.
 *
 * scripts/build-site.sh puts the PDF next to the HTML pages, and every
 * chunked page of this book sits at the root of the output directory, so a
 * bare relative href resolves from all of them. The icon is inline SVG
 * rather than a Material Symbols codepoint so it cannot come out as tofu if
 * the icon font is unavailable.
 * ------------------------------------------------------------------ */
(function () {
  var PDF_HREF = "math14-skeletal-notes.pdf";
  var PDF_TITLE =
    "Download the whole book as a PDF, to print or annotate — rebuilt " +
    "whenever new notes are posted";

  function addPdfButton() {
    var contents = document.querySelector("#ptx-navbar .ptx-navbar-contents");
    if (!contents) return;
    if (contents.querySelector(".pdf-button")) return;

    var a = document.createElement("a");
    a.className = "pdf-button button";
    a.href = PDF_HREF;
    a.title = PDF_TITLE;
    // Open in a new tab so a reader who is midway through a section does not
    // lose their place to the browser's PDF viewer.
    a.target = "_blank";
    a.rel = "noopener";

    var icon = document.createElement("span");
    icon.className = "icon";
    icon.setAttribute("aria-hidden", "true");
    icon.innerHTML =
      '<svg viewBox="0 0 24 24" width="18" height="18" focusable="false" ' +
      'aria-hidden="true"><path fill="currentColor" d="M6 2h7l5 5v13a2 2 0 0 ' +
      '1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm6.5 1.5V8H17l-4.5-4.5zM12 10.5' +
      'a.75.75 0 0 0-.75.75v3.19l-1.22-1.22a.75.75 0 1 0-1.06 1.06l2.5 2.5a' +
      '.75.75 0 0 0 1.06 0l2.5-2.5a.75.75 0 1 0-1.06-1.06l-1.22 1.22v-3.19' +
      'a.75.75 0 0 0-.75-.75z"/></svg>';

    var name = document.createElement("span");
    name.className = "name";
    name.textContent = "PDF";

    a.appendChild(icon);
    a.appendChild(name);

    // Sit just before the Prev/Up/Next group, which is pinned to the right.
    var tree = contents.querySelector(".treebuttons");
    if (tree) {
      contents.insertBefore(a, tree);
    } else {
      contents.appendChild(a);
    }
  }

  /* Only offer the button if the PDF is actually there.
   *
   * The deployed site always has it, because scripts/build-site.sh puts it
   * beside the HTML. A local `pretext build web` on its own does not, and a
   * visible link that 404s is worse than no link, so ask before showing.
   *
   * fetch() cannot read file:// URLs (the browser blocks it as cross-origin),
   * so when the page has been opened straight off disk there is no way to
   * check; show the button rather than hide it wrongly.
   */
  function addPdfButtonIfPresent() {
    if (window.location.protocol === "file:" || typeof fetch !== "function") {
      addPdfButton();
      return;
    }
    fetch(PDF_HREF, { method: "HEAD" })
      .then(function (r) {
        if (r.ok) addPdfButton();
      })
      .catch(function () {
        /* offline, or no PDF built: leave the navbar as it was */
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addPdfButtonIfPresent);
  } else {
    addPdfButtonIfPresent();
  }
})();
