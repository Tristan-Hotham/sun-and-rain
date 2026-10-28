/* bivariate.js: shared bivariate map logic for the "Sun and rain" pages (world and UK).
   No dependencies. Exposes window.BV. Mirrors code/bivariate.py (same corners, same OKLab interpolation).

   Conventions: axis A (i, columns) = sunshine, 0 = dull ... n-1 = sunny; axis B (j, rows) = rain, 0 = dry ... n-1 = wet.
   Values are per cell in plain typed arrays (one entry per data cell); a cell also has a pixel index in a source raster.

   Main pieces:
     BV.palette(n, corners)              n x n colours, P[i][j] = {hex, rgb:[r,g,b]}
     BV.quantileBreaks(v, w, n, tf)      weighted quantile breaks (equal area per class); tf optional transform for binning
     BV.classOf(x, breaks)               class index
     BV.paint(img, pix, a, b, ba, bb, P, opt)  write classed colours into an ImageData (opt.only=[i,j], opt.mask, opt.dim)
     BV.mercatorRows(H, W, latTop, latBot, srcLatTop, srcRowDeg)  row lookup to reproject a lat/lon raster to Web Mercator
     BV.reproject(srcCanvas, outCanvas, rows)   draw the reprojected raster
     BV.legend(el, n, P, opt)            SVG legend with corner words; hover or tap a cell to isolate a class
     BV.breakSlider(el, opt)             histogram with draggable class breaks
     BV.distance(sunA, rainA, sun, rain, ncell, sd, flip)  RMS distance between 12-month profiles (sqrt rain)
*/
(function () {
  "use strict";
  const BV = {};
  BV.CORNERS = { dull_dry: "#EDE8DF", sunny_dry: "#EB8A2E", dull_wet: "#2E8F8C", sunny_wet: "#3B1D47" };
  BV.CORNER_LABELS = { dull_dry: "dull and dry", sunny_dry: "sunny and dry", dull_wet: "dull and wet", sunny_wet: "sunny and wet" };

  const s2l = c => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const l2s = c => { c = Math.min(1, Math.max(0, c)); return c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055; };
  function hex2rgb(h) { h = h.replace("#", ""); return [0, 2, 4].map(k => parseInt(h.slice(k, k + 2), 16) / 255); }
  function toLab(rgb) {
    const [r, g, b] = rgb.map(s2l);
    const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
    const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
    const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
      0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s];
  }
  function fromLab([L, a, b]) {
    const l = Math.pow(L + 0.3963377774 * a + 0.2158037573 * b, 3), m = Math.pow(L - 0.1055613458 * a - 0.0638541728 * b, 3),
      s = Math.pow(L - 0.0894841775 * a - 1.2914855480 * b, 3);
    return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
      -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s].map(l2s);
  }
  const toHex = rgb => "#" + rgb.map(c => Math.round(c).toString(16).padStart(2, "0")).join("").toUpperCase();

  BV.palette = function (n, corners) {
    corners = corners || BV.CORNERS;
    const c00 = toLab(hex2rgb(corners.dull_dry)), c10 = toLab(hex2rgb(corners.sunny_dry)),
      c01 = toLab(hex2rgb(corners.dull_wet)), c11 = toLab(hex2rgb(corners.sunny_wet));
    const P = [];
    for (let i = 0; i < n; i++) {
      const u = i / (n - 1), row = [];
      for (let j = 0; j < n; j++) {
        const v = j / (n - 1), lab = [0, 1, 2].map(k => (1 - u) * (1 - v) * c00[k] + u * (1 - v) * c10[k] + (1 - u) * v * c01[k] + u * v * c11[k]);
        const rgb = fromLab(lab).map(c => Math.round(c * 255));
        row.push({ rgb, hex: toHex(rgb) });
      }
      P.push(row);
    }
    return P;
  };
  // words for a class: corners named, edges and middle described
  BV.classWords = function (i, j, n) {
    const s = i === 0 ? "dull" : i === n - 1 ? "sunny" : (n === 3 ? "middling sun" : (i === 1 ? "fairly dull" : "fairly sunny"));
    const r = j === 0 ? "dry" : j === n - 1 ? "wet" : (n === 3 ? "middling rain" : (j === 1 ? "fairly dry" : "fairly wet"));
    if (n === 3 && i === 1 && j === 1) return "middling sun and rain";
    return s + " and " + r;
  };

  BV.quantileBreaks = function (v, w, n, tf, nb) {
    tf = tf || (x => x); nb = nb || 20000;
    let lo = Infinity, hi = -Infinity;
    for (let k = 0; k < v.length; k++) { const t = tf(v[k]); if (t < lo) lo = t; if (t > hi) hi = t; }
    const h = new Float64Array(nb + 1), sc = nb / (hi - lo || 1); let tot = 0;
    for (let k = 0; k < v.length; k++) { const wk = w ? w[k] : 1; h[Math.floor((tf(v[k]) - lo) * sc)] += wk; tot += wk; }
    const out = []; let acc = 0, q = 1;
    for (let b = 0; b <= nb && q < n; b++) {
      acc += h[b];
      while (q < n && acc >= tot * q / n) { out.push(lo + (b + 1) / sc); q++; }
    }
    return out; // in transformed units; the caller inverts tf
  };
  BV.classOf = function (x, br) { let c = 0; while (c < br.length && x >= br[c]) c++; return c; };

  BV.paint = function (img, pix, a, b, ba, bb, P, opt) {
    opt = opt || {};
    const d = img.data, n = P.length, only = opt.only, mask = opt.mask, dim = opt.dim || [222, 219, 212, 150];
    const flat = []; for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) flat[i * n + j] = P[i][j].rgb;
    d.fill(0);
    for (let k = 0; k < pix.length; k++) {
      const i = BV.classOf(a[k], ba), j = BV.classOf(b[k], bb), o = pix[k] * 4;
      let on = true;
      if (only && (only[0] !== i || only[1] !== j)) on = false;
      if (mask && !mask[k]) on = false;
      if (on) { const c = flat[i * n + j]; d[o] = c[0]; d[o + 1] = c[1]; d[o + 2] = c[2]; d[o + 3] = 255; }
      else { d[o] = dim[0]; d[o + 1] = dim[1]; d[o + 2] = dim[2]; d[o + 3] = dim[3]; }
    }
    return img;
  };

  // Reprojection of a regular lat/lon raster (row 0 at srcLatTop, srcRowDeg degrees per row) to Web Mercator rows
  BV.mercY = lat => Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360));
  BV.mercatorRows = function (W, latTop, latBot, srcLatTop, srcRowDeg) {
    const y0 = BV.mercY(latTop), y1 = BV.mercY(latBot), H = Math.round(W / (2 * Math.PI) * (y0 - y1)), rows = new Int32Array(H);
    for (let y = 0; y < H; y++) {
      const my = y0 - (y + 0.5) / H * (y0 - y1), lat = (2 * Math.atan(Math.exp(my)) - Math.PI / 2) * 180 / Math.PI;
      rows[y] = Math.floor((srcLatTop - lat) / srcRowDeg);
    }
    return rows;
  };
  BV.reproject = function (src, out, rows) {
    const ctx = out.getContext("2d"), W = out.width;
    ctx.imageSmoothingEnabled = false; ctx.clearRect(0, 0, W, out.height);
    let y = 0;
    while (y < rows.length) {           // draw runs of output rows that share a source row in one call
      let z = y; while (z + 1 < rows.length && rows[z + 1] === rows[y]) z++;
      if (rows[y] >= 0 && rows[y] < src.height) ctx.drawImage(src, 0, rows[y], src.width, 1, 0, y, W, z - y + 1);
      y = z + 1;
    }
  };

  const NS = "http://www.w3.org/2000/svg";
  const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
  BV.el = el;

  // Legend: square grid, sunshine to the right, rain upwards, corner words. opt.onHover(i,j|null), opt.onClick(i,j), opt.labelA/B
  BV.legend = function (host, n, P, opt) {
    opt = opt || {};
    host.innerHTML = "";
    const cs = n === 3 ? 46 : 36, g = n * cs, L = 78, T = 26, Wd = L + g + 82, Hd = T + g + 54;
    const svg = el("svg", { viewBox: `0 0 ${Wd} ${Hd}`, width: Wd, height: Hd, role: "group", "aria-label": "Map legend" }, host);
    let pinned = null;
    const cells = [];
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const r = el("rect", { x: L + i * cs, y: T + (n - 1 - j) * cs, width: cs - 2, height: cs - 2, fill: P[i][j].hex, tabindex: 0,
        class: "bvcell", "aria-label": BV.classWords(i, j, n) }, svg);
      r.style.cursor = "pointer"; cells.push(r);
      el("title", {}, r).textContent = BV.classWords(i, j, n) + (opt.share ? " (" + opt.share(i, j) + ")" : "");
      const enter = () => { if (pinned === null) { mark(i, j); opt.onHover && opt.onHover(i, j); } };
      const leave = () => { if (pinned === null) { mark(null); opt.onHover && opt.onHover(null); } };
      r.addEventListener("mouseenter", enter); r.addEventListener("mouseleave", leave);
      r.addEventListener("focus", enter); r.addEventListener("blur", leave);
      r.addEventListener("click", e => {
        e.stopPropagation();
        if (pinned && pinned[0] === i && pinned[1] === j) { pinned = null; mark(null); opt.onHover && opt.onHover(null); }
        else { pinned = [i, j]; mark(i, j); opt.onHover && opt.onHover(i, j); }
      });
    }
    function mark(i, j) {
      cells.forEach((r, k) => {
        const on = i === null || i === undefined || (Math.floor(k / n) === i && k % n === j);
        r.setAttribute("opacity", on ? 1 : 0.35);
        r.setAttribute("stroke", i !== null && i !== undefined && on ? "var(--fg)" : "none"); r.setAttribute("stroke-width", 2);
      });
    }
    const tx = (x, y, s, a) => { const t = el("text", Object.assign({ x, y, class: "lab" }, a || {}), svg); t.textContent = s; return t; };
    tx(L - 6, T + g - 4, "dull", { "text-anchor": "end", class: "lab m" }); tx(L - 6, T + g + 10, "and dry", { "text-anchor": "end", class: "lab m" });
    tx(L - 6, T + 12, "dull", { "text-anchor": "end", class: "lab m" }); tx(L - 6, T + 26, "and wet", { "text-anchor": "end", class: "lab m" });
    tx(L + g + 4, T + 12, "sunny", { class: "lab m" }); tx(L + g + 4, T + 26, "and wet", { class: "lab m" });
    tx(L + g + 4, T + g - 4, "sunny", { class: "lab m" }); tx(L + g + 4, T + g + 10, "and dry", { class: "lab m" });
    el("path", { d: `M${L} ${T + g + 22}H${L + g - 2}m-6 -4l6 4l-6 4`, stroke: "currentColor", fill: "none", class: "ax" }, svg);
    tx(L + g / 2, T + g + 40, opt.labelA || "more sunshine", { "text-anchor": "middle", class: "lab b" });
    el("path", { d: `M${L - 64} ${T + g - 2}V${T + 30}m-4 6l4 -6l4 6`, stroke: "currentColor", fill: "none", class: "ax" }, svg);
    const tb = tx(0, 0, opt.labelB || "more rain", { "text-anchor": "middle", class: "lab b", transform: `translate(${L - 70} ${T + g / 2 + 18}) rotate(-90)` });
    svg.style.color = "var(--muted)";
    return { clear: () => { pinned = null; mark(null); }, mark };
  };

  // Histogram with draggable breaks. opt: {hist:[{x0,x1,w}], breaks:[], colors:[], fmt, onChange(breaks, done), scale:'lin'|'sqrt', min, max, label}
  BV.breakSlider = function (host, opt) {
    host.innerHTML = "";
    const W = opt.width || 300, H = opt.height || 92, ml = 8, mr = 8, mt = 16, mb = 22, iw = W - ml - mr, ih = H - mt - mb;
    const tf = opt.scale === "sqrt" ? Math.sqrt : (x => x), inv = opt.scale === "sqrt" ? (x => x * x) : (x => x);
    const t0 = tf(opt.min), t1 = tf(opt.max);
    const X = v => ml + (tf(Math.min(Math.max(v, opt.min), opt.max)) - t0) / (t1 - t0) * iw;
    const V = x => inv(t0 + (x - ml) / iw * (t1 - t0));
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, class: "bslider", role: "group", "aria-label": opt.label }, host);
    const gb = el("g", {}, svg), gh = el("g", {}, svg);
    let br = opt.breaks.slice();
    const wmax = Math.max(...opt.hist.map(h => h.w / Math.max(1e-9, X(h.x1) - X(h.x0))));
    const cap = document.createElement("div"); cap.className = "bvvals"; host.appendChild(cap);
    function draw() {
      cap.textContent = "Breaks at " + br.map(b => opt.fmt(b)).join(", ");
      gb.innerHTML = "";
      const edges = [opt.min].concat(br, [opt.max]);
      opt.hist.forEach(h => {
        const x0 = X(h.x0), x1 = X(h.x1); if (x1 - x0 < .2) return;
        const mid = (h.x0 + h.x1) / 2; let c = 0; while (c < br.length && mid >= br[c]) c++;
        const hh = h.w / (x1 - x0) / wmax * ih;
        el("rect", { x: x0, y: mt + ih - hh, width: Math.max(.5, x1 - x0 - .4), height: hh, fill: opt.colors[c] }, gb);
      });
      el("line", { x1: ml, x2: ml + iw, y1: mt + ih + .5, y2: mt + ih + .5, stroke: "var(--muted)" }, gb);
      (opt.ticks || []).forEach(t => {
        el("line", { x1: X(t), x2: X(t), y1: mt + ih, y2: mt + ih + 4, stroke: "var(--muted)" }, gb);
        const tt = el("text", { x: X(t), y: mt + ih + 16, "text-anchor": "middle", class: "lab s m" }, gb); tt.textContent = opt.fmt(t, true);
      });
      gh.innerHTML = "";
      br.forEach((b, k) => {
        const x = X(b), g = el("g", { class: "hdl", tabindex: 0, role: "slider", "aria-label": opt.label + " break " + (k + 1), "aria-valuenow": Math.round(b) }, gh);
        el("line", { x1: x, x2: x, y1: mt - 4, y2: mt + ih, stroke: "var(--fg)", "stroke-width": 2 }, g);
        el("rect", { x: x - 9, y: mt - 20, width: 18, height: ih + 22, fill: "transparent" }, g);
        el("circle", { cx: x, cy: mt - 7, r: 7, fill: "var(--card)", stroke: "var(--fg)", "stroke-width": 2 }, g);
        g.style.cursor = "ew-resize";
        g.addEventListener("pointerdown", e => start(e, k));
        g.addEventListener("keydown", e => {
          const step = (opt.max - opt.min) / 100 * (e.shiftKey ? 5 : 1);
          if (e.key === "ArrowLeft" || e.key === "ArrowDown") move(k, br[k] - step, true);
          else if (e.key === "ArrowRight" || e.key === "ArrowUp") move(k, br[k] + step, true);
          else return;
          e.preventDefault();
        });
      });
    }
    function move(k, v, done) {
      const lo = k ? br[k - 1] : opt.min, hi = k < br.length - 1 ? br[k + 1] : opt.max, gap = (opt.max - opt.min) / 200;
      br[k] = Math.min(hi - gap, Math.max(lo + gap, v));
      if (opt.round) br[k] = opt.round(br[k]);
      draw(); opt.onChange(br.slice(), done);
      const h = gh.children[k]; if (h && done) h.focus();
    }
    function start(e, k) {
      e.preventDefault();
      const pt = svg.createSVGPoint();
      const mv = ev => { pt.x = ev.clientX; pt.y = ev.clientY; const p = pt.matrixTransform(svg.getScreenCTM().inverse()); move(k, V(p.x), false); };
      const up = () => { window.removeEventListener("pointermove", mv); window.removeEventListener("pointerup", up); opt.onChange(br.slice(), true); };
      window.addEventListener("pointermove", mv); window.addEventListener("pointerup", up);
    }
    draw();
    return { set: (b, colors) => { br = b.slice(); if (colors) opt.colors = colors; draw(); }, get: () => br.slice() };
  };

  // RMS distance over 12 months between one profile and every cell; sun and rain arrays are cell-major (cell*12 + month)
  BV.distance = function (sA, rA, sun, rain, ncell, sd, flip) {
    const out = new Float32Array(ncell), rq = rA.map(Math.sqrt), sF = [], rF = [];
    for (let m = 0; m < 12; m++) { sF[m] = sA[(m + 6) % 12]; rF[m] = rq[(m + 6) % 12]; }
    for (let k = 0; k < ncell; k++) {
      let d1 = 0, d2 = 0; const o = k * 12;
      for (let m = 0; m < 12; m++) {
        const s = sun[o + m], r = Math.sqrt(rain[o + m]);
        const a = (s - sA[m]) / sd[0], b = (r - rq[m]) / sd[1]; d1 += a * a + b * b;
        if (flip) { const c = (s - sF[m]) / sd[0], e = (r - rF[m]) / sd[1]; d2 += c * c + e * e; }
      }
      out[k] = Math.sqrt((flip ? Math.min(d1, d2) : d1) / 12);
    }
    return out;
  };

  window.BV = BV;
})();
