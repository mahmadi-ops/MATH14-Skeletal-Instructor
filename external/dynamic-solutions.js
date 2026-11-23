/* Render released solutions below their randomized questions.
 * The HTML template stays inert until Runestone has evaluated the current
 * question. Reuse those values and its math queue without moving a solution
 * into the question, changing its seed, or generating another set of values.
 */
(function () {
  "use strict";

  var VALUE = /\[%=\s*(?:toTeX\(\s*([A-Za-z_]\w*)\s*\)|([A-Za-z_]\w*))\s*%\]/g;

  function fill(template, variables) {
    var fragment = template.content.cloneNode(true);
    var walker = document.createTreeWalker(fragment, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) {
      node.textContent = node.textContent.replace(VALUE, function (_, mathName, textName) {
        var name = mathName || textName;
        if (!Object.prototype.hasOwnProperty.call(variables, name)) {
          throw new Error("Missing solution value: " + name);
        }
        return mathName ? variables.toTeX(variables[name]) : String(variables[name]);
      });
      if (node.textContent.indexOf("[%=") !== -1) {
        throw new Error("Unsupported dynamic solution expression");
      }
    }
    return fragment.firstElementChild;
  }

  function attach(template) {
    var article = template.closest(".exercise");
    var previousVariables = null;
    var output = null;

    function update() {
      var component = window.componentMap && window.componentMap[template.dataset.exercise];
      var variables = component && component.dyn_vars_eval;
      if (!variables || (variables === previousVariables && output && output.isConnected)) {
        return;
      }

      var replacement;
      try {
        replacement = fill(template, variables);
      } catch (error) {
        console.error("Unable to render solution for " + template.dataset.exercise, error);
        return;
      }
      previousVariables = variables;
      if (output && output.isConnected) {
        if (window.MathJax && MathJax.typesetClear) {
          MathJax.typesetClear([output]);
        }
        output.replaceWith(replacement);
      } else {
        template.after(replacement);
      }
      output = replacement;
      component.queueMathJax(output);
    }

    // A new question, restored attempt, or Randomize replaces its content.
    // Object identity avoids re-rendering on feedback and MathJax mutations.
    new MutationObserver(update).observe(article, { childList: true, subtree: true });
    update();
  }

  function start() {
    document.querySelectorAll("template.dynamic-solution-template").forEach(attach);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
