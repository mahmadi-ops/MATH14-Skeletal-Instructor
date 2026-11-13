/* Polar sweep widgets for the Concept Check of "Double Integrals in Polar
 * Form".  One canvas draws two polar curves, a polar grid, and the ray of
 * angle theta; a slider turns the ray and a readout reports the radii the
 * ray meets, which are the limits of r the reader is being asked to find.
 *
 * A container carries data-widget="rose" or data-widget="cardioids"; the
 * canvas, slider and readout inside it are found by class.
 */
(function () {
  "use strict";

  var SANS = '13px "Open Sans", "Helvetica Neue", Helvetica, Arial, sans-serif';
  var MATH = 'italic 15px "PT Serif", "Times New Roman", Times, serif';

  var STEPS = 24;                          /* the slider counts pi/STEPS */

  function gcd(a, b) { return b ? gcd(b, a % b) : a; }

  /* k twenty-fourths of pi, as an exact fraction: 0, pi/6, 5pi/12, 3pi/2, 2pi */
  function piFraction(k) {
    if (k === 0) { return "0"; }
    var g = gcd(k, STEPS), n = k / g, d = STEPS / g;
    return (n === 1 ? "" : n) + "\u03C0" + (d === 1 ? "" : "/" + d);
  }

  var WIDGETS = {
    rose: {
      xmin: -1.25, xmax: 1.25, ymin: -1.25, ymax: 1.25, rings: 2, raylen: 1.2,
      f1: function (t) { return Math.cos(3 * t); }, c1: "#CC0000",
      f2: function () { return 0.5; }, c2: "#0072B2",
      l1: "r = cos(3θ)", l1p: [0.42, -1.05],
      l2: "r = 1/2", l2p: [-1.15, 0.62],
      readout: function (t, k) {
        var rose = Math.cos(3 * t);
        var top = Math.min(Math.max(rose, 0), 0.5);
        return "<b>θ = " + piFraction(k) + "</b><br/>" +
          "cos(3θ) = " + rose.toFixed(3) + ", so inside both curves " +
          "<i>r</i> runs from 0 to " + top.toFixed(3) +
          (rose > 0.5 ? " (the circle)" : (rose > 0 ? " (the rose)" : " (nothing)"));
      }
    },
    cardioids: {
      xmin: -1.35, xmax: 2.35, ymin: -1.35, ymax: 2.35, rings: 4, raylen: 2.2,
      f1: function (t) { return 1 + Math.cos(t); }, c1: "#CC0000",
      f2: function (t) { return 1 + Math.sin(t); }, c2: "#0072B2",
      l1: "r = 1 + cos θ", l1p: [1.15, -0.95],
      l2: "r = 1 + sin θ", l2p: [-1.28, 1.95],
      readout: function (t, k) {
        var a = 1 + Math.cos(t), b = 1 + Math.sin(t);
        var which = a > b ? "1 + sin θ" : "1 + cos θ";
        return "<b>θ = " + piFraction(k) + "</b><br/>" +
          "1 + cosθ = " + a.toFixed(3) + ", 1 + sinθ = " + b.toFixed(3) +
          " — inside both, <i>r</i> stops at " + Math.min(a, b).toFixed(3) +
          " (" + which + ")";
      }
    }
  };

  function build(box) {
    var cfg = WIDGETS[box.getAttribute("data-widget")];
    if (!cfg) { return; }
    var cv = box.querySelector("canvas"),
        sl = box.querySelector("input"),
        out = box.querySelector(".pw-readout"),
        ctx = cv.getContext("2d"),
        W = cv.width, H = cv.height,
        s = Math.min(W / (cfg.xmax - cfg.xmin), H / (cfg.ymax - cfg.ymin)),
        dpr = Math.max(2, window.devicePixelRatio || 1);

    /* keep the drawing in CSS pixels but give the canvas dpr times as many
       device pixels, so curves and text are not soft on any display */
    cv.style.width = W + "px";
    cv.width = Math.round(W * dpr);
    cv.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    function X(x) { return (x - (cfg.xmin + cfg.xmax) / 2) * s + W / 2; }
    function Y(y) { return H / 2 - (y - (cfg.ymin + cfg.ymax) / 2) * s; }

    function polarCurve(f, stroke) {
      ctx.beginPath();
      for (var i = 0; i <= 1440; i++) {
        var t = i * Math.PI / 720, r = f(t);
        var px = X(r * Math.cos(t)), py = Y(r * Math.sin(t));
        if (i === 0) { ctx.moveTo(px, py); } else { ctx.lineTo(px, py); }
      }
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 2.5;
      ctx.stroke();
    }

    function grid() {
      ctx.strokeStyle = "#e4e4e4";
      ctx.lineWidth = 1;
      var k, t, L = cfg.rings / 2;
      for (k = 1; k <= cfg.rings; k++) {
        ctx.beginPath();
        ctx.arc(X(0), Y(0), (k / 2) * s, 0, 2 * Math.PI);
        ctx.stroke();
      }
      for (k = 0; k < 12; k++) {
        t = k * Math.PI / 6;
        ctx.beginPath();
        ctx.moveTo(X(0), Y(0));
        ctx.lineTo(X(L * Math.cos(t)), Y(L * Math.sin(t)));
        ctx.stroke();
      }
      ctx.strokeStyle = "#333";
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(X(cfg.xmin), Y(0));
      ctx.lineTo(X(cfg.xmax), Y(0));
      ctx.moveTo(X(0), Y(cfg.ymin));
      ctx.lineTo(X(0), Y(cfg.ymax));
      ctx.stroke();
      ctx.fillStyle = "#333";
      ctx.font = SANS;
      ctx.textAlign = "center";
      for (k = Math.ceil(cfg.xmin); k <= Math.floor(cfg.xmax); k++) {
        if (k === 0) { continue; }
        ctx.beginPath();
        ctx.moveTo(X(k), Y(0) - 4);
        ctx.lineTo(X(k), Y(0) + 4);
        ctx.stroke();
        ctx.fillText(String(k), X(k), Y(0) + 17);
      }
    }

    function draw() {
      var k = parseInt(sl.value, 10), th = k * Math.PI / STEPS, i, r, hits;
      ctx.clearRect(0, 0, W, H);
      grid();
      polarCurve(cfg.f2, cfg.c2);
      polarCurve(cfg.f1, cfg.c1);
      ctx.beginPath();                       /* the ray theta = constant */
      ctx.moveTo(X(0), Y(0));
      ctx.lineTo(X(cfg.raylen * Math.cos(th)), Y(cfg.raylen * Math.sin(th)));
      ctx.strokeStyle = "#333";
      ctx.lineWidth = 2;
      ctx.stroke();
      hits = [[cfg.f1(th), cfg.c1], [cfg.f2(th), cfg.c2]];
      for (i = 0; i < hits.length; i++) {    /* where the ray meets a curve */
        r = hits[i][0];
        if (r < 0) { continue; }
        ctx.beginPath();
        ctx.arc(X(r * Math.cos(th)), Y(r * Math.sin(th)), 4.5, 0, 2 * Math.PI);
        ctx.fillStyle = hits[i][1];
        ctx.fill();
        ctx.strokeStyle = "white";
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
      ctx.font = MATH;
      ctx.textAlign = "left";
      ctx.fillStyle = cfg.c1;
      ctx.fillText(cfg.l1, X(cfg.l1p[0]), Y(cfg.l1p[1]));
      ctx.fillStyle = cfg.c2;
      ctx.fillText(cfg.l2, X(cfg.l2p[0]), Y(cfg.l2p[1]));
      out.innerHTML = cfg.readout(th, k);
    }

    sl.addEventListener("input", draw);
    draw();
  }

  function init() {
    var boxes = document.querySelectorAll("[data-widget]"), i;
    for (i = 0; i < boxes.length; i++) { build(boxes[i]); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
