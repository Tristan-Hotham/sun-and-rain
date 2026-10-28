"""Shared bivariate colour logic (Python side). Mirrors code/bivariate.js exactly so the page, figures and collage agree.

The palette is built from four corner colours by bilinear interpolation in OKLab, then each class is used as is.
Axis 1 (columns, i) is sunshine: 0 = dull ... n-1 = sunny. Axis 2 (rows, j) is rain: 0 = dry ... n-1 = wet.
Reusable for any two variables (for example a UK 1 km companion): pass different corners if wanted.
"""
import numpy as np

# corners: dull and dry (palest), sunny and dry (warm), dull and wet (cool), sunny and wet (darkest)
CORNERS = dict(dull_dry="#EDE8DF", sunny_dry="#EB8A2E", dull_wet="#2E8F8C", sunny_wet="#3B1D47")
CORNER_LABELS = dict(dull_dry="dull and dry", sunny_dry="sunny and dry", dull_wet="dull and wet", sunny_wet="sunny and wet")


def _srgb_to_lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _lin_to_srgb(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def hex2rgb(h):
    h = h.lstrip("#"); return np.array([int(h[k:k + 2], 16) / 255 for k in (0, 2, 4)])


def rgb2hex(c):
    c = np.clip(np.round(np.asarray(c) * 255), 0, 255).astype(int); return "#%02X%02X%02X" % tuple(c)


def to_oklab(rgb):
    r, g, b = _srgb_to_lin(rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    return np.array([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s])


def from_oklab(lab):
    L, a, b = lab
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return _lin_to_srgb([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                         -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                         -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s])


def palette(n=3, corners=CORNERS):
    """n by n hex colours, P[i][j] with i = sunshine class (0 dull), j = rain class (0 dry)."""
    c00, c10, c01, c11 = (to_oklab(hex2rgb(corners[k])) for k in ("dull_dry", "sunny_dry", "dull_wet", "sunny_wet"))
    P = []
    for i in range(n):
        u = i / (n - 1); row = []
        for j in range(n):
            v = j / (n - 1)
            lab = (1 - u) * (1 - v) * c00 + u * (1 - v) * c10 + (1 - u) * v * c01 + u * v * c11
            row.append(rgb2hex(from_oklab(lab)))
        P.append(row)
    return P


def quantile_breaks(x, w, n):
    """n - 1 weighted quantile breaks (equal shares of weight, e.g. land area, per class)."""
    o = np.argsort(x); cw = np.cumsum(np.asarray(w, float)[o]); cw /= cw[-1]
    return [float(np.asarray(x)[o][min(np.searchsorted(cw, k / n), len(x) - 1)]) for k in range(1, n)]


def classify(x, breaks):
    return np.digitize(x, breaks)


if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(8, 4))
    for ax, n in zip(axs, (3, 4)):
        P = palette(n)
        for i in range(n):
            for j in range(n):
                ax.add_patch(plt.Rectangle((i, j), .95, .95, color=P[i][j])); ax.text(i + .45, j + .45, P[i][j], fontsize=6, ha="center")
        ax.set_xlim(0, n); ax.set_ylim(0, n); ax.set_xlabel("sunnier"); ax.set_ylabel("wetter")
    fig.savefig("swatch.png", dpi=110)
