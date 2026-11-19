#!/usr/bin/env python3
"""
BEKB Multi-Year Chart Generator (reports/charts/*.png)
Erzeugt alle 13 hochauflösenden Grafiken direkt aus den validierten Datensätzen
(`data/bekb_panel_all.json`) sowie den geprüften Jahresabschluss-Positionen 2025/2026:

Bilanz-Grafiken (Bericht 02):
  1. 02_bilanz_gestapelte_saeulen_2025.png  (Gestapeltes Säulendiagramm absolut & 100 %)
  2. 02_bilanz_treemap_2025.png             (Treemap / Kacheldiagramm detailliert)
  3. 02_bilanz_sankey_2025.png              (Sankey Mittelherkunft -> Mittelverwendung & Goldene Bilanzregel)
  4. 02_bilanz_langfrist_wachstum_2003_2026.png

Erfolgsrechnungs- & Controlling-Grafiken (Berichte 01 & 03):
  5. 01_erfolgsrechnung_wasserfall_2025.png (Wasserfalldiagramm / Bridge Chart FY2025)
  6. 01_ertrag_kosten_marge_kombi_2003_2025.png (Kombiniertes Säulen- & Liniendiagramm)
  7. 03_soll_ist_vergleich_horizontal_2026.png  (Horizontaler Balkenvergleich Soll-Ist 06-2026)

Weitere Langfrist- & Themen-Grafiken (Berichte 03–07 & README):
  8. 03_kapital_rwa_basel_2015_2026.png
  9. 04_effizienz_produktivitaet_2003_2025.png
 10. 05_aktie_dividende_kanton_2003_2025.png
 11. 06_semester_saisonalitaet_reserven_2013_2026.png
 12. 07_langfrist_dashboard_epochen_2003_2026.png
 13. 07_gewinn_loehne_verguetung_real_2003_2025.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path as MplPath
from matplotlib.ticker import FuncFormatter
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CHARTS_DIR = ROOT / "reports" / "charts"

# Corporate & Financial Times / SNB-inspirierte Farbpalette
NAVY = "#0F2942"
BLUE = "#2563EB"
STEEL = "#3B82F6"
SKY = "#60A5FA"
TEAL = "#0F766E"
EMERALD = "#10B981"
RED = "#C8102E"       # BEKB-Akzentrot
DARK_RED = "#991B1B"
AMBER = "#D97706"
GOLD = "#F59E0B"
SLATE = "#475569"
MUTED = "#94A3B8"
LIGHT_BG = "#F8FAFC"
GRID = "#E2E8F0"
PURPLE = "#6D28D9"


def ch_num(val: float, dec: int = 1) -> str:
    """Schweizer Zahlenformat mit Apostroph und Komma (z. B. 42'977,0)."""
    s = f"{val:,.{dec}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", "'")


def setup_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Liberation Sans", "Arial"],
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 0.8,
        "axes.facecolor": "#FFFFFF",
        "figure.facecolor": LIGHT_BG,
        "axes.titlesize": 12.2,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "xtick.labelsize": 8.8,
        "ytick.labelsize": 8.8,
        "legend.fontsize": 8.6,
        "legend.frameon": True,
        "legend.facecolor": "#FFFFFF",
        "legend.edgecolor": "#E2E8F0",
    })


def clean_ax(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis=grid_axis, linestyle="--", linewidth=0.7, color=GRID, alpha=0.9, zorder=0)
    ax.set_axisbelow(True)


def add_footer(fig: plt.Figure, source_note: str) -> None:
    fig.text(
        0.015, 0.012,
        source_note,
        fontsize=7.8, color="#64748B", ha="left", va="bottom",
    )


def load_panel() -> tuple[list[dict], list[dict], list[dict]]:
    with (DATA_DIR / "bekb_panel_all.json").open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["annual"], data["semester"], data["offenlegung"]


def load_verguetung_real() -> list[dict]:
    with (DATA_DIR / "bekb_panel_all.json").open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["verguetung_real"]


# ---------------------------------------------------------------------------
# Squarified Treemap Helper
# ---------------------------------------------------------------------------

def _worst_aspect(row: list[float], short_side: float) -> float:
    if not row or short_side <= 0:
        return float("inf")
    s = sum(row)
    rmax = max(row)
    rmin = min(row)
    if rmin <= 0 or s <= 0:
        return float("inf")
    w2 = short_side * short_side
    s2 = s * s
    return max((w2 * rmax) / s2, s2 / (w2 * rmin))


def _layout_row(row: list[float], x: float, y: float, w: float, h: float):
    s = sum(row)
    rects = []
    if w >= h:
        row_w = s / h if h > 0 else 0
        cy = y
        for val in row:
            rh = val / row_w if row_w > 0 else 0
            rects.append((x, cy, row_w, rh))
            cy += rh
        return rects, (x + row_w, y, w - row_w, h)
    else:
        row_h = s / w if w > 0 else 0
        cx = x
        for val in row:
            rw = val / row_h if row_h > 0 else 0
            rects.append((cx, y, rw, row_h))
            cx += rw
        return rects, (x, y + row_h, w, h - row_h)


def squarify(values: list[float], x: float, y: float, w: float, h: float):
    total = sum(values)
    area = w * h
    scaled = [v * area / total for v in values]

    rects: list[tuple[float, float, float, float]] = []
    row: list[float] = []
    cx, cy, cw, ch = x, y, w, h

    for v in scaled:
        short = min(cw, ch)
        if not row or _worst_aspect(row + [v], short) <= _worst_aspect(row, short):
            row.append(v)
        else:
            new_rects, (cx, cy, cw, ch) = _layout_row(row, cx, cy, cw, ch)
            rects.extend(new_rects)
            row = [v]
    if row:
        new_rects, _ = _layout_row(row, cx, cy, cw, ch)
        rects.extend(new_rects)
    return rects


# ---------------------------------------------------------------------------
# 1. Gestapeltes Säulendiagramm Bilanz 2025 (Absolut & 100 %)
# ---------------------------------------------------------------------------

def chart_02_bilanz_gestapelte_saeulen() -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.8, 7.4))
    fig.suptitle(
        "BEKB Bilanzstruktur 2025: Bilanzgleichung Aktiven vs. Passiven (42'977,0 Mio. CHF)",
        fontsize=14.2, fontweight="bold", color=NAVY, y=0.965,
    )

    akt_items = [
        ("Hypothekar-\nforderungen", "Hypothekarforderungen", 30099.6, NAVY),
        ("Flüssige\nMittel", "Flüssige Mittel", 7528.3, TEAL),
        ("Finanzanlagen", "Finanzanlagen", 2774.0, BLUE),
        ("Kunden-Ausl.", "Forderungen ggü. Kunden", 1844.3, SKY),
        ("Übrige Akt.", "Anlagevermögen & Übrige", 730.8, MUTED),
    ]
    pas_items = [
        ("Kunden-\neinlagen", "Verpflichtungen Kundeneinlagen", 28086.7, NAVY),
        ("Anleihen &\nPfandbriefe", "Anleihen, Pfandbriefe & KO", 9205.0, BLUE),
        ("Eigenkapital", "Eigenkapital & Reserven*", 3082.1, EMERALD),
        ("Repo/Bank", "Repo & Verpfl. Banken", 2169.9, AMBER),
        ("Übrige Pas.", "Rückstellungen & Übrige", 433.3, MUTED),
    ]
    total = 42977.0

    for ax, mode_100, subtitle in [
        (ax1, False, "Absolute Struktur (Mrd. CHF) — Exakte Bilanzgleichung"),
        (ax2, True, "Normierte Zusammensetzung (100 %)"),
    ]:
        clean_ax(ax, "y")
        x_positions = [0, 1]
        bar_w = 0.68
        for x, items in [(0, akt_items), (1, pas_items)]:
            bottom = 0.0
            for idx_item, (short_lbl, full_lbl, val, col) in enumerate(items):
                h = (val / total * 100.0) if mode_100 else (val / 1000.0)
                ax.bar(x, h, bottom=bottom, width=bar_w, color=col, edgecolor="#FFFFFF", linewidth=1.3, zorder=3)
                pct = val / total * 100.0
                if (mode_100 and h >= 6.4) or (not mode_100 and h >= 2.75):
                    txt_color = "#FFFFFF" if col in {NAVY, BLUE, TEAL} else "#0F172A"
                    if mode_100:
                        lbl = f"{short_lbl} ({pct:.1f}%)" if "\n" not in short_lbl else f"{short_lbl}\n{pct:.1f} %"
                    else:
                        lbl = (
                            f"{short_lbl}\n{ch_num(val/1000.0, 2)} Mrd. ({pct:.1f}%)"
                            if "\n" not in short_lbl
                            else f"{short_lbl}\n{ch_num(val/1000.0, 2)} Mrd.\n({pct:.1f} %)"
                        )
                    ax.text(x, bottom + h / 2, lbl, ha="center", va="center", fontsize=7.6 if pct >= 10 else 6.7, fontweight="bold", color=txt_color, zorder=4)
                else:
                    is_left = (x == 0)
                    edge_x = x - bar_w / 2 if is_left else x + bar_w / 2
                    text_x = x - bar_w / 2 - 0.12 if is_left else x + bar_w / 2 + 0.12
                    ha = "right" if is_left else "left"
                    y_mid = bottom + h / 2
                    y_off = (-3.6 if idx_item == 3 else 3.2) if mode_100 else (-1.8 if idx_item == 3 else 2.2)
                    txt = (
                        f"{full_lbl}\n{pct:.1f} %"
                        if mode_100
                        else f"{full_lbl}\n{ch_num(val/1000.0, 2)} Mrd. ({pct:.1f} %)"
                    )
                    ax.annotate(
                        txt,
                        xy=(edge_x, y_mid),
                        xytext=(text_x, y_mid + y_off),
                        ha=ha, va="center", fontsize=7.4, fontweight="bold", color="#334155",
                        arrowprops=dict(arrowstyle="-", color="#94A3B8", lw=0.8),
                        zorder=5,
                    )
                bottom += h

            top_lbl = "100,0 %" if mode_100 else "42,98 Mrd. CHF"
            ax.text(x, bottom + (3.2 if mode_100 else 1.4), top_lbl, ha="center", va="bottom", fontsize=9.8, fontweight="bold", color=NAVY)

        ax.set_xticks(x_positions)
        ax.set_xticklabels(["Aktiven\n(Mittelverwendung)", "Passiven\n(Mittelherkunft)"], fontsize=9.6, fontweight="bold", color=NAVY)
        ax.set_xlim(-1.55, 2.55)
        if mode_100:
            ax.set_ylim(0, 118)
            ax.set_ylabel("Anteil an der Bilanzsumme (%)")
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
        else:
            ax.set_ylim(0, 51)
            ax.set_ylabel("Betrag (Mrd. CHF)")
            ax.axhline(total / 1000.0, color=RED, linestyle=":", linewidth=1.2, alpha=0.8, zorder=2)
        ax.set_title(subtitle, pad=12, color=NAVY)

    add_footer(
        fig,
        "Quelle: BEKB Geschäftsbericht 2025, Jahresabschluss Bilanz per 31.12.2025 (42'977,0 Mio. CHF). "
        "*Eigenkapital & Reserven vor Gewinnverwendung (3'082,1 Mio. CHF inkl. 587,1 Mio. Reserven allg. Bankrisiken; nach Dividende 2'981,5 Mio.)."
    )
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.92])
    fig.savefig(CHARTS_DIR / "02_bilanz_gestapelte_saeulen_2025.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2. Treemap (Kacheldiagramm) Bilanz 2025 detailliert
# ---------------------------------------------------------------------------

def chart_02_bilanz_treemap() -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.0, 7.8))
    fig.suptitle(
        "Detaillierte Bilanz-Treemap 2025: Grössenverhältnisse aller Positionen (42'977,0 Mio. CHF)",
        fontsize=14.2, fontweight="bold", color=NAVY, y=0.965,
    )

    akt_data = [
        ("Hypothekarforderungen", "Hypotheken", 30099.6, NAVY),
        ("Flüssige Mittel", "Flüssige Mittel", 7528.3, TEAL),
        ("Finanzanlagen", "Finanzanlagen", 2774.0, BLUE),
        ("Forderungen\nggü. Kunden", "Kundenford.", 1844.3, SKY),
        ("Übrige Aktiven*", "Übrige\nAkt.*", 730.8, "#475569"),
    ]
    pas_data = [
        ("Verpflichtungen aus\nKundeneinlagen", "Kundeneinlagen", 28086.7, NAVY),
        ("Anleihen &\nPfandbriefdarlehen", "Anleihen & Pfandbriefe", 8926.0, BLUE),
        ("Freiwillige\nGewinnreserven", "Freiw. Res.", 1916.1, TEAL),
        ("Repo-Geschäfte", "Repo", 1425.0, AMBER),
        ("Verpfl. Banken", "Banken", 744.9, "#D97706"),
        ("Reserven allg.\nBankrisiken", "Bankris.", 587.1, EMERALD),
        ("Kassenobl.", "KO", 279.0, "#60A5FA"),
        ("Übrige Passiven & Kern-EK**", "Übrige EK/Pas.", 1012.2, "#475569"),
    ]

    for ax, items, title in [
        (ax1, akt_data, "Aktiven 2025 — Total 42'977,0 Mio. CHF"),
        (ax2, pas_data, "Passiven 2025 — Total 42'977,0 Mio. CHF"),
    ]:
        items_sorted = sorted(items, key=lambda t: t[2], reverse=True)
        vals = [t[2] for t in items_sorted]
        total = sum(vals)
        rects = squarify(vals, 0, 0, 100, 100)

        for (label, short_lbl, val, col), (rx, ry, rw, rh) in zip(items_sorted, rects):
            rect = patches.Rectangle((rx, ry), rw, rh, facecolor=col, edgecolor="#FFFFFF", linewidth=2.2)
            ax.add_patch(rect)
            pct = val / total * 100.0
            dark_bg = col in {NAVY, BLUE, TEAL, "#475569", AMBER, "#D97706"}
            tcol = "#FFFFFF" if dark_bg else "#0F172A"
            if rw >= 26 and rh >= 16:
                ax.text(
                    rx + rw / 2, ry + rh / 2,
                    f"{label}\n{ch_num(val)} Mio. ({pct:.1f} %)",
                    ha="center", va="center", fontsize=10.5 if rw * rh > 2000 else 8.6,
                    fontweight="bold", color=tcol,
                )
            elif rw >= 14 and rh >= 10:
                ax.text(
                    rx + rw / 2, ry + rh / 2,
                    f"{short_lbl}\n{ch_num(val, 0)} Mio.\n({pct:.1f} %)",
                    ha="center", va="center", fontsize=7.6, fontweight="bold", color=tcol,
                )
            elif rw >= 7 and rh >= 6:
                ax.text(
                    rx + rw / 2, ry + rh / 2,
                    f"{short_lbl}\n{pct:.1f}%",
                    ha="center", va="center", fontsize=6.9, fontweight="bold", color=tcol,
                )

        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis("off")
        ax.set_title(title, fontsize=11.5, fontweight="bold", color=NAVY, pad=10)

    add_footer(
        fig,
        "Quelle: BEKB Geschäftsbericht 2025, Jahresabschluss Bilanz. *Übrige Aktiven (730,8 Mio.): Sonstige 226,7 | Sachanlagen 224,0 | Banken 126,8 | Beteilig. 61,2 | Repo/Handel/Abgr. 92,3.\n"
        "**Übrige EK/Passiven (1'012,2 Mio.): Rückstellungen 235,0 | Gesellschaftskapital 186,4 | Gesetzl. Reserven 232,1 | Jahresgewinn 175,4 | Abgr./Sonstige/Derivate 198,2 – Eig. Anteile 15,1."
    )
    plt.tight_layout(rect=[0.01, 0.075, 0.99, 0.92])
    fig.savefig(CHARTS_DIR / "02_bilanz_treemap_2025.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Sankey-Diagramm (Flussdiagramm) Mittelherkunft -> Mittelverwendung 2025
# ---------------------------------------------------------------------------

def _draw_sankey_ribbon(ax: plt.Axes, x0: float, y0_bot: float, y0_top: float,
                        x1: float, y1_bot: float, y1_top: float, color: str, alpha: float = 0.44) -> None:
    xm = (x0 + x1) / 2.0
    verts = [
        (x0, y0_bot), (xm, y0_bot), (xm, y1_bot), (x1, y1_bot),
        (x1, y1_top), (xm, y1_top), (xm, y0_top), (x0, y0_top),
        (x0, y0_bot),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    ax.add_patch(patches.PathPatch(MplPath(verts, codes), facecolor=color, edgecolor="none", alpha=alpha, zorder=2))


def chart_02_bilanz_sankey() -> None:
    fig, ax = plt.subplots(figsize=(15.2, 8.4))
    fig.suptitle(
        "Bilanz-Sankey 2025: Mittelherkunft (Passiven) → Mittelverwendung (Aktiven) & Goldene Bilanzregel",
        fontsize=14.0, fontweight="bold", color=NAVY, y=0.96,
    )

    total = 42977.0
    sources = [
        ("Eigenkapital & Reserven\n(inkl. Gewinn 2025)", 3082.1, EMERALD),
        ("Anleihen, Pfandbriefe\n& Kassenobligationen", 9205.0, BLUE),
        ("Kundeneinlagen\n(stabile Kernbasis)", 28086.7, NAVY),
        ("Kurzfristige Refinanzierung\n(Repo, Banken, Übrige)", 2603.1, AMBER),
    ]
    uses = [
        ("Sachanlagen & Beteiligungen\n(Anlagevermögen)", 285.1, PURPLE),
        ("Hypothekarforderungen\n(Kern-Kreditbuch)", 30099.6, NAVY),
        ("Forderungen ggü. Kunden\n(Firmen-/Privatkredite)", 1844.3, SKY),
        ("Finanzanlagen\n(HQLA / Obligationen)", 2774.0, BLUE),
        ("Flüssige Mittel & Übrige\n(SNB-Giro & Abgrenzungen)", 7974.0, TEAL),
    ]

    def layout_nodes(items: list[tuple[str, float, str]], gap: float):
        avail = 100.0 - gap * (len(items) - 1)
        scale = avail / total
        pos = []
        y_top = 100.0
        for lbl, val, col in items:
            h = val * scale
            y_bot = y_top - h
            pos.append((lbl, val, col, y_bot, y_top))
            y_top = y_bot - gap
        return pos

    src_pos = layout_nodes(sources, gap=3.2)
    use_pos = layout_nodes(uses, gap=3.4)

    hub_bot, hub_top = 0.0, 100.0
    x_left, x_mid, x_right = 26.0, 50.0, 74.0
    bw = 2.6

    mid_y_top = hub_top
    for lbl, val, col, y0b, y0t in src_pos:
        h_mid = val / total * (hub_top - hub_bot)
        mid_y_bot = mid_y_top - h_mid
        _draw_sankey_ribbon(ax, x_left + bw, y0b, y0t, x_mid - bw / 2, mid_y_bot, mid_y_top, col, alpha=0.45)
        mid_y_top = mid_y_bot

    mid_y_top = hub_top
    for lbl, val, col, y1b, y1t in use_pos:
        h_mid = val / total * (hub_top - hub_bot)
        mid_y_bot = mid_y_top - h_mid
        _draw_sankey_ribbon(ax, x_mid + bw / 2, mid_y_bot, mid_y_top, x_right, y1b, y1t, col, alpha=0.45)
        mid_y_top = mid_y_bot

    for lbl, val, col, yb, yt in src_pos:
        ax.add_patch(patches.Rectangle((x_left, yb), bw, yt - yb, facecolor=col, edgecolor="#FFFFFF", lw=1.2, zorder=4))
        pct = val / total * 100.0
        ax.text(
            x_left - 1.5, (yb + yt) / 2,
            f"{lbl}\n{ch_num(val)} Mio. ({pct:.1f} %)",
            ha="right", va="center", fontsize=8.8, fontweight="bold", color=NAVY,
        )

    ax.add_patch(patches.Rectangle((x_mid - bw / 2, hub_bot), bw, hub_top - hub_bot, facecolor=NAVY, edgecolor="#FFFFFF", lw=1.5, zorder=4))
    ax.text(
        x_mid, 50.0,
        "BILANZ\n2025\n\n42'977,0\nMio. CHF",
        ha="center", va="center", fontsize=8.8, fontweight="bold", color="#FFFFFF", zorder=5,
        bbox=dict(boxstyle="round,pad=0.42", facecolor=NAVY, edgecolor="#FFFFFF", lw=1.2),
    )

    right_y_nudge = {
        "Forderungen ggü. Kunden\n(Firmen-/Privatkredite)": 2.4,
        "Finanzanlagen\n(HQLA / Obligationen)": -2.4,
    }
    for lbl, val, col, yb, yt in use_pos:
        ax.add_patch(patches.Rectangle((x_right, yb), bw, yt - yb, facecolor=col, edgecolor="#FFFFFF", lw=1.2, zorder=4))
        pct = val / total * 100.0
        y_center = (yb + yt) / 2
        y_lbl = y_center + right_y_nudge.get(lbl, 0.0)
        if lbl in right_y_nudge:
            ax.plot([x_right + bw + 0.2, x_right + bw + 1.3], [y_center, y_lbl], color="#94A3B8", lw=0.9)
        ax.text(
            x_right + bw + 1.6, y_lbl,
            f"{lbl}\n{ch_num(val)} Mio. ({pct:.1f} %)",
            ha="left", va="center", fontsize=8.8, fontweight="bold", color=NAVY,
        )

    ax.text(x_left - 1.5, 105.5, "MITTELHERKUNFT (PASSIVEN)", ha="right", va="bottom", fontsize=10.5, fontweight="bold", color=NAVY)
    ax.text(x_mid, 105.5, "BILANZSUMME", ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=NAVY)
    ax.text(x_right + bw + 1.6, 105.5, "MITTELVERWENDUNG (AKTIVEN)", ha="left", va="bottom", fontsize=10.5, fontweight="bold", color=NAVY)

    rule_text = (
        "Goldene Bilanzregel & Fristenkongruenz (2025):\n"
        "• Eigenkapital (3'082,1 Mio.) deckt Sachanlagen & Beteiligungen (285,1 Mio.) mehr als 10-fach  |  • NSFR: 143,3 % (06-2026: 144,0 %)\n"
        "• Langfristige Mittel + stabile Kundeneinlagen (40'373,8 Mio. = 93,9 % Passiven) überdecken Kreditbuch + Anlagevermögen (32'229,0 Mio.) deutlich."
    )
    ax.text(
        50.0, -4.5, rule_text,
        ha="center", va="top", fontsize=8.2, color="#065F46", fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.55", facecolor="#ECFDF5", edgecolor="#10B981", lw=1.0),
    )

    ax.set_xlim(-6, 108)
    ax.set_ylim(-18, 112)
    ax.axis("off")

    add_footer(fig, "Quelle: BEKB Geschäftsbericht 2025 (Bilanz per 31.12.2025) & Offenlegungsbericht 06-2026 (NSFR).")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.92])
    fig.savefig(CHARTS_DIR / "02_bilanz_sankey_2025.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. Langfristige Bilanzentwicklung 2003–H1-2026
# ---------------------------------------------------------------------------

def chart_02_bilanz_langfrist(ann: list[dict], sem: list[dict]) -> None:
    fig, ax1 = plt.subplots(figsize=(13.8, 6.5))
    clean_ax(ax1, "y")

    h26 = sem[-1]
    labels = [str(r["year"]) for r in ann] + ["H1-26"]
    x = np.arange(len(labels))
    assets = [r["total_assets_mio"] / 1000.0 for r in ann] + [h26["total_assets_mio"] / 1000.0]
    mortgages = [r["mortgage_loans_mio"] / 1000.0 for r in ann] + [h26["mortgage_loans_mio"] / 1000.0]
    deposits = [r["customer_deposits_mio"] / 1000.0 for r in ann] + [h26["customer_deposits_mio"] / 1000.0]
    dep_to_mort = [r["deposit_to_mortgage_pct"] for r in ann] + [h26["customer_deposits_mio"] / h26["mortgage_loans_mio"] * 100.0]

    ax1.fill_between(x, assets, color="#E2E8F0", alpha=0.55, label="Bilanzsumme (Mrd. CHF)", zorder=1)
    ax1.plot(x, assets, color=NAVY, lw=2.6, marker="o", ms=4.5, label="_nolegend_", zorder=4)
    ax1.plot(x, mortgages, color=RED, lw=2.4, marker="s", ms=4.2, label="Hypothekarforderungen (Mrd. CHF)", zorder=4)
    ax1.plot(x, deposits, color=TEAL, lw=2.4, marker="^", ms=4.5, label="Kundeneinlagen (Mrd. CHF)", zorder=4)

    # Start- und Endpunkte sauber ohne Überschneidung beschriften
    ax1.text(0, assets[0] + 1.1, ch_num(assets[0], 1), fontsize=8.3, fontweight="bold", color=NAVY, ha="center")
    ax1.text(0, deposits[0] + 1.0, ch_num(deposits[0], 1), fontsize=8.3, fontweight="bold", color=TEAL, ha="center")
    ax1.text(0, mortgages[0] - 2.3, ch_num(mortgages[0], 1), fontsize=8.3, fontweight="bold", color=RED, ha="center")

    ax1.text(len(x) - 1, assets[-1] + 1.3, f"{ch_num(assets[-1], 1)} Mrd.", fontsize=8.6, fontweight="bold", color=NAVY, ha="right")
    ax1.text(len(x) - 1, mortgages[-1] + 1.3, f"{ch_num(mortgages[-1], 1)} Mrd.", fontsize=8.6, fontweight="bold", color=RED, ha="right")
    ax1.text(len(x) - 1, deposits[-1] - 2.4, f"{ch_num(deposits[-1], 1)} Mrd.", fontsize=8.6, fontweight="bold", color=TEAL, ha="right")

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    ax1.set_ylabel("Volumen (Mrd. CHF)", fontweight="bold", color=NAVY)
    ax1.set_ylim(0, 51)

    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    ax2.plot(x, dep_to_mort, color=AMBER, lw=2.1, linestyle="--", label="Kundeneinlagen / Hypotheken (%)", zorder=3)
    ax2.axhline(100.0, color=AMBER, linestyle=":", lw=1.1, alpha=0.8)
    ax2.set_ylabel("Deckung Hypotheken durch Einlagen (%)", fontweight="bold", color=AMBER)
    ax2.set_ylim(75, 138)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
    ax2.text(
        18.2, 98.2, "100 %-Schwelle (Einlagen = Hypotheken)",
        fontsize=8.0, color=AMBER, fontweight="bold", ha="right",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.85),
    )

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", ncol=2)

    fig.suptitle(
        "Langfristige Bilanzexpansion (2003–H1-2026): Von der Einlagen- zur Pfandbrief-Refinanzierung",
        fontsize=14.0, fontweight="bold", color=NAVY, y=0.96,
    )
    add_footer(fig, "Quelle: BEKB Geschäftsberichte 2003–2025 & Semesterbericht H1-2026 (data/bekb_panel_all.json).")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.92])
    fig.savefig(CHARTS_DIR / "02_bilanz_langfrist_wachstum_2003_2026.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5. Wasserfalldiagramm (Bridge Chart) Erfolgsrechnung 2025
# ---------------------------------------------------------------------------

def chart_01_erfolgsrechnung_wasserfall() -> None:
    fig, ax = plt.subplots(figsize=(14.4, 7.0))
    clean_ax(ax, "y")

    steps = [
        ("Netto-\nZinserfolg", 376.677, "pos"),
        ("Kommissions-\nerfolg", 125.975, "pos"),
        ("Handels-\nerfolg", 21.868, "pos"),
        ("Übriger ord.\nErfolg", 22.777, "pos"),
        ("Geschäfts-\nertrag", 547.297, "total"),
        ("Personal-\naufwand", -153.849, "neg"),
        ("Sach-\naufwand", -126.701, "neg"),
        ("Abschreib. &\nRückst.", -46.003, "neg"),
        ("Geschäfts-\nerfolg", 220.744, "total"),
        ("AO & Res.\nBankris.", -2.589, "neg"),
        ("Steuern", -42.800, "neg"),
        ("Jahresgewinn\n2025", 175.355, "final"),
    ]

    x = np.arange(len(steps))
    running = 0.0
    bottoms, heights, colors = [], [], []

    for lbl, val, kind in steps:
        if kind in {"total", "final"}:
            bottoms.append(0.0)
            heights.append(val)
            running = val
            colors.append(NAVY if kind == "total" else TEAL)
        elif val >= 0:
            bottoms.append(running)
            heights.append(val)
            running += val
            colors.append(BLUE)
        else:
            bottoms.append(running + val)
            heights.append(abs(val))
            running += val
            colors.append(RED)

    for i in range(1, len(steps)):
        prev_end = bottoms[i - 1] + heights[i - 1] if steps[i - 1][2] != "neg" else bottoms[i - 1]
        ax.plot([i - 0.72, i - 0.28], [prev_end, prev_end], color="#94A3B8", lw=1.0, linestyle=":")

    ax.bar(x, heights, bottom=bottoms, width=0.58, color=colors, edgecolor="#FFFFFF", linewidth=1.2, zorder=3)

    for i, (lbl, val, kind) in enumerate(steps):
        top_y = bottoms[i] + heights[i]
        if kind in {"total", "final"}:
            ax.text(i, top_y + 9, f"{ch_num(val)}", ha="center", va="bottom", fontsize=9.5, fontweight="bold", color=colors[i])
        elif val >= 0:
            ax.text(i, top_y + 9, f"+{ch_num(val)}", ha="center", va="bottom", fontsize=8.8, fontweight="bold", color=BLUE)
        else:
            y_pos = bottoms[i] - 9 if heights[i] < 35 else bottoms[i] + heights[i] + 9
            va = "top" if heights[i] < 35 else "bottom"
            ax.text(i, y_pos, f"{ch_num(val)}", ha="center", va=va, fontsize=8.8, fontweight="bold", color=RED)

    legend_handles = [
        patches.Patch(color=BLUE, label="Ertragsbeiträge (+)"),
        patches.Patch(color=NAVY, label="Zwischensummen (Geschäftsertrag / -erfolg)"),
        patches.Patch(color=RED, label="Aufwände, Abschreibungen, Reserven & Steuern (–)"),
        patches.Patch(color=TEAL, label="Jahresgewinn 2025 (175,4 Mio. CHF)"),
    ]
    ax.legend(handles=legend_handles, loc="upper right")

    ax.set_xticks(x)
    ax.set_xticklabels([s[0] for s in steps], fontsize=8.8, color=NAVY)
    ax.set_ylabel("Betrag (Mio. CHF)", fontweight="bold", color=NAVY)
    ax.set_ylim(0, 625)

    fig.suptitle(
        "Wasserfalldiagramm Erfolgsrechnung 2025: Vom Netto-Zinserfolg zum Jahresgewinn (Mio. CHF)",
        fontsize=14.0, fontweight="bold", color=NAVY, y=0.96,
    )
    add_footer(fig, "Quelle: BEKB Geschäftsbericht 2025, Erfolgsrechnung (in Mio. CHF; Gewinnverwendung: 100,7 Mio. Dividende, 74,0 Mio. Gewinnreserven).")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.92])
    fig.savefig(CHARTS_DIR / "01_erfolgsrechnung_wasserfall_2025.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 6. Kombiniertes Säulen- & Liniendiagramm Ertrag, Kosten & Gewinnmarge 2003–2025
# ---------------------------------------------------------------------------

def chart_01_ertrag_kosten_marge_kombi(ann: list[dict]) -> None:
    fig, ax1 = plt.subplots(figsize=(14.0, 6.6))
    clean_ax(ax1, "y")

    years = [r["year"] for r in ann]
    x = np.arange(len(years))
    w = 0.38

    income = [r["total_operating_income_mio"] for r in ann]
    expenses = [abs(r["total_operating_expenses_mio"]) for r in ann]
    op_margin = [r["operating_profit_mio"] / r["total_operating_income_mio"] * 100.0 for r in ann]
    net_margin = [r["net_profit_mio"] / r["total_operating_income_mio"] * 100.0 for r in ann]

    ax1.bar(x - w / 2, income, width=w, color=NAVY, label="Geschäftsertrag (Mio. CHF)", zorder=3)
    exp_colors = [AMBER if y == 2015 else SLATE for y in years]
    ax1.bar(x + w / 2, expenses, width=w, color=exp_colors, label="Geschäftsaufwand (Mio. CHF; 2015 inkl. PK-Einlage)", zorder=3)

    ax1.set_xticks(x)
    ax1.set_xticklabels([str(y) for y in years], rotation=45, ha="right")
    ax1.set_xlim(-0.7, len(years) + 0.65)
    ax1.set_ylabel("Ertrag & Aufwand (Mio. CHF)", fontweight="bold", color=NAVY)
    ax1.set_ylim(0, 660)

    idx_15 = years.index(2015)
    ax1.annotate(
        "2015: PK-Einlage\n83,8 Mio. CHF",
        xy=(idx_15 + w / 2, expenses[idx_15]),
        xytext=(idx_15 + 1.1, 395),
        fontsize=8.0, color=AMBER, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFBEB", edgecolor=AMBER, lw=0.8),
        arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.0),
    )

    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    ax2.plot(x, op_margin, color=BLUE, lw=2.3, marker="o", ms=4.5, label="Operative Marge (Geschäftserfolg / Ertrag %)", zorder=5)
    ax2.plot(x, net_margin, color=RED, lw=2.3, marker="s", ms=4.2, label="Nettogewinnmarge (Reingewinn / Ertrag %)", zorder=5)
    ax2.set_ylabel("Gewinnmarge (%)", fontweight="bold", color=RED)
    ax2.set_ylim(10, 62)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))

    idx_07 = years.index(2007)
    ax2.text(idx_07, net_margin[idx_07] + 1.7, f"2007: {net_margin[idx_07]:.1f}%\n(BKW-Verkauf)", ha="center", fontsize=7.6, color=RED, fontweight="bold")
    pill = dict(boxstyle="round,pad=0.22", facecolor="#FFFFFF", edgecolor="#E2E8F0", alpha=0.95)
    ax2.text(len(x) - 0.75, op_margin[-1], f" {op_margin[-1]:.1f}%", va="center", ha="left", fontsize=8.3, color=BLUE, fontweight="bold", bbox=pill, zorder=6)
    ax2.text(len(x) - 0.75, net_margin[-1], f" {net_margin[-1]:.1f}%", va="center", ha="left", fontsize=8.3, color=RED, fontweight="bold", bbox=pill, zorder=6)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", ncol=2, fontsize=8.2)

    fig.suptitle(
        "Kombiniertes Säulen- & Liniendiagramm (2003–2025): Ertrag, Kosten & Margenentwicklung",
        fontsize=14.0, fontweight="bold", color=NAVY, y=0.96,
    )
    add_footer(fig, "Quelle: BEKB Geschäftsberichte 2003–2025 (2003–2014 Bruttogewinn vor FINMA-RVB; ab 2015 Geschäftserfolg). Operatives Spitzenergebnis 2023–2025 nach Zinswende.")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.92])
    fig.savefig(CHARTS_DIR / "01_ertrag_kosten_marge_kombi_2003_2025.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 7. Horizontaler Balkenvergleich (Soll-Ist-Vergleich 06-2026 / 2025)
# ---------------------------------------------------------------------------

def chart_03_soll_ist_horizontal(off: list[dict], ann: list[dict], sem: list[dict]) -> None:
    o26 = off[-1]
    h26 = sem[-1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.6, 6.5), gridspec_kw={"width_ratios": [1.22, 1.08]})
    fig.suptitle(
        "Horizontaler Soll-Ist-Vergleich (06-2026 & Strategie 2025): Regulatorische & Strategische Zielerreichung",
        fontsize=13.8, fontweight="bold", color=NAVY, y=0.965,
    )

    clean_ax(ax1, "x")
    kpis_cap = [
        ("Leverage Ratio\n(Basel-Minimum 3,00 %)", 3.00, o26["leverage_ratio_pct"], None),
        ("CET1-Quote\n(FINMA 9,26 % | BEKB-Ziel ≥16 %)", 9.26, o26["cet1_ratio_pct"], 16.0),
        ("Tier-1-Quote\n(FINMA-Zielquote inkl. Puffer)", 11.06, o26["cet1_ratio_pct"], None),
        ("Gesamtkapitalquote\n(FINMA-Zielquote inkl. Puffer)", 13.46, o26["total_capital_ratio_pct"], None),
    ]
    y = np.arange(len(kpis_cap))
    bh = 0.34
    ax1.barh(y - bh / 2, [k[1] for k in kpis_cap], height=bh, color=MUTED, label="Soll / FINMA-Mindestziel (inkl. antizykl. Puffer)", zorder=3)
    ax1.barh(y + bh / 2, [k[2] for k in kpis_cap], height=bh, color=NAVY, label="Ist per 30.06.2026 (Offenlegungsbericht 06-2026)", zorder=3)

    for idx, (_, sv, iv, strat_goal) in enumerate(kpis_cap):
        if strat_goal is not None:
            ax1.plot([strat_goal, strat_goal], [idx - 0.38, idx + 0.38], color=RED, lw=2.3, zorder=5)
            ax1.text(strat_goal, idx - 0.42, "BEKB-Ziel ≥16%", ha="center", va="top", fontsize=7.6, fontweight="bold", color=RED)
        ax1.text(sv + 0.3, idx - bh / 2, f"{sv:.2f} %", va="center", ha="left", fontsize=8.4, color=SLATE, fontweight="bold")
        diff = iv - sv
        ax1.text(iv + 0.3, idx + bh / 2, f"{iv:.2f} %  (+{diff:.2f} PP)", va="center", ha="left", fontsize=8.6, color=TEAL, fontweight="bold")

    ax1.set_yticks(y)
    ax1.set_yticklabels([k[0] for k in kpis_cap], fontsize=8.8, fontweight="bold", color=NAVY)
    ax1.set_xlim(0, 27.5)
    ax1.set_xlabel("Quote (%)")
    ax1.set_title("Eigenmittel- & Verschuldungsquoten (06-2026)", color=NAVY, pad=10)
    ax1.legend(loc="lower right", fontsize=8.0)

    clean_ax(ax2, "x")
    kpis_liq = [
        ("Cost-Income-Ratio H1-2026\n(Zielzone <55 % | kleiner = besser)", 55.0, h26["cir_pct"], True),
        ("LCR – Kurzfristige Liquidität\n(Regul. Minimum ≥100 %)", 100.0, o26["lcr_pct"], False),
        ("NSFR – Stabile Finanzierung\n(Regul. Minimum ≥100 %)", 100.0, o26["nsfr_pct"], False),
    ]
    y2 = np.arange(len(kpis_liq))
    ax2.barh(y2 - bh / 2, [k[1] for k in kpis_liq], height=bh, color=MUTED, label="Soll / Benchmark", zorder=3)
    ax2.barh(y2 + bh / 2, [k[2] for k in kpis_liq], height=bh, color=TEAL, label="Ist (H1 / 30.06.2026)", zorder=3)

    for idx, (_, sv, iv, lower_better) in enumerate(kpis_liq):
        ax2.text(sv + 2.5, idx - bh / 2, f"{sv:.1f} %", va="center", ha="left", fontsize=8.4, color=SLATE, fontweight="bold")
        diff = sv - iv if lower_better else iv - sv
        tag = f"–{diff:.1f} PP besser" if lower_better else f"+{diff:.1f} PP Puffer"
        ax2.text(iv + 2.5, idx + bh / 2, f"{iv:.1f} % ({tag})", va="center", ha="left", fontsize=8.4, color=TEAL, fontweight="bold")

    ax2.set_yticks(y2)
    ax2.set_yticklabels([k[0] for k in kpis_liq], fontsize=8.8, fontweight="bold", color=NAVY)
    ax2.set_xlim(0, 222)
    ax2.set_xlabel("Quote (%)")
    ax2.set_title("Liquidität (06-2026) & Kosteneffizienz (H1-2026)", color=NAVY, pad=10)
    ax2.legend(loc="lower right", fontsize=8.0)

    add_footer(fig, "Quelle: BEKB Offenlegungsbericht 06-2026 (KM1), Geschäftsbericht 2025 (CET1-Ziel ≥16 %) & Semesterbericht H1-2026 (CIR 49,1 %).")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.92])
    fig.savefig(CHARTS_DIR / "03_soll_ist_vergleich_horizontal_2026.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 8. Basel III Evolution: Kapital, RWA-Dichte & Liquidität (2015–06-2026)
# ---------------------------------------------------------------------------

def chart_03_kapital_rwa_basel(off: list[dict]) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13.5, 8.4), sharex=True)
    fig.suptitle(
        "Aufsichtsrechtliche Resilienz unter Basel III & Basel III final (2015–06-2026)",
        fontsize=14.0, fontweight="bold", color=NAVY, y=0.965,
    )

    periods = [r["period"] for r in off]
    x = np.arange(len(periods))
    cet1 = [r["cet1_ratio_pct"] for r in off]
    totcap = [r["total_capital_ratio_pct"] for r in off]
    rwa_dens = [r["rwa_density_pct"] for r in off]
    lev = [r["leverage_ratio_pct"] for r in off]
    lcr = [r["lcr_pct"] for r in off]
    nsfr = [r["nsfr_pct"] for r in off]

    b3f_idx = periods.index("H1-2025") - 0.5
    for ax in (ax1, ax2):
        clean_ax(ax, "y")
        ax.axvspan(b3f_idx, len(periods) - 0.5, color="#EFF6FF", alpha=0.8, zorder=0)
        ax.axvline(b3f_idx, color=BLUE, linestyle="--", lw=1.2, zorder=2)

    ax1.plot(x, totcap, color=NAVY, lw=2.4, marker="o", ms=5, label="Gesamtkapitalquote (%)", zorder=4)
    ax1.plot(x, cet1, color=TEAL, lw=2.4, marker="s", ms=4.5, label="CET1-Quote (%)", zorder=4)
    ax1.axhline(13.46, color=RED, linestyle=":", lw=1.1, label="FINMA Gesamtkapital-Zielquote (13,46 %)")
    ax1.axhline(9.26, color=AMBER, linestyle=":", lw=1.1, label="FINMA CET1-Zielquote (9,26 %)")
    ax1.set_ylabel("Kapitalquote (%)", fontweight="bold", color=NAVY)
    ax1.set_ylim(7, 24.5)
    ax1.text(b3f_idx + 0.14, 23.7, "Basel III final\n(ab 1.1.2025)", fontsize=8.4, fontweight="bold", color=BLUE, va="top")

    ax1r = ax1.twinx()
    ax1r.spines["top"].set_visible(False)
    ax1r.plot(x, rwa_dens, color=PURPLE, lw=1.9, linestyle="-.", marker="^", ms=4.5, label="RWA-Dichte (RWA / Bilanz %)")
    ax1r.set_ylabel("RWA-Dichte (%)", fontweight="bold", color=PURPLE)
    ax1r.set_ylim(30, 50)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax1r.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="lower left", ncol=3, fontsize=8.0)

    lcr_x = [i for i, v in enumerate(lcr) if v is not None]
    lcr_v = [lcr[i] for i in lcr_x]
    nsfr_x = [i for i, v in enumerate(nsfr) if v is not None]
    nsfr_v = [nsfr[i] for i in nsfr_x]
    lev_x = [i for i, v in enumerate(lev) if v is not None]
    lev_v = [lev[i] for i in lev_x]

    ax2.plot(lcr_x, lcr_v, color=BLUE, lw=2.3, marker="o", ms=4.5, label="LCR – Kurzfristige Liquidität (%)")
    ax2.plot(nsfr_x, nsfr_v, color=TEAL, lw=2.3, marker="D", ms=4.5, label="NSFR – Stabile Finanzierung (%)")
    ax2.axhline(100.0, color=RED, linestyle=":", lw=1.1, label="Liquiditäts-Minimum (100 %)")
    ax2.set_ylabel("LCR / NSFR (%)", fontweight="bold", color=NAVY)
    ax2.set_ylim(90, 248)

    # Peak LCR H1-2021 markieren
    pk_idx = lcr_v.index(max(lcr_v))
    ax2.text(lcr_x[pk_idx], lcr_v[pk_idx] + 6, f"COVID-Peak: {lcr_v[pk_idx]:.1f}%", ha="center", fontsize=8.0, fontweight="bold", color=BLUE)

    ax2r = ax2.twinx()
    ax2r.spines["top"].set_visible(False)
    ax2r.plot(lev_x, lev_v, color=AMBER, lw=2.0, linestyle="--", marker="s", ms=4.2, label="Leverage Ratio (%)")
    ax2r.set_ylabel("Leverage Ratio (%)", fontweight="bold", color=AMBER)
    ax2r.set_ylim(3.0, 9.5)

    h3, l3 = ax2.get_legend_handles_labels()
    h4, l4 = ax2r.get_legend_handles_labels()
    ax2.legend(h3 + h4, l3 + l4, loc="upper left", ncol=2, fontsize=8.1)

    ax2.set_xticks(x)
    ax2.set_xticklabels(periods, rotation=45, ha="right")

    add_footer(fig, "Quelle: Alle 20 BEKB Offenlegungsberichte 2015–06-2026 (data/bekb_panel_offenlegung.csv).")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.93])
    fig.savefig(CHARTS_DIR / "03_kapital_rwa_basel_2015_2026.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 9. Operative Effizienz & Produktivität (2003–2025)
# ---------------------------------------------------------------------------

def chart_04_effizienz_produktivitaet(ann: list[dict]) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13.5, 8.2), sharex=True)
    fig.suptitle(
        "Operative Effizienz, Kostenstruktur & Produktivitätssprung je Vollzeitstelle (2003–2025)",
        fontsize=14.0, fontweight="bold", color=NAVY, y=0.965,
    )

    years = [r["year"] for r in ann]
    x = np.arange(len(years))
    pers = [abs(r["personnel_expenses"]) / 1000.0 for r in ann]
    gen = [abs(r["general_expenses"]) / 1000.0 for r in ann]
    cir = [r["cir_pct"] for r in ann]
    cir_clean = [r["cir_ex_oneoff_pct"] for r in ann]
    fte = [r["fte_count"] for r in ann]
    inc_fte = [r["income_per_fte_tchf"] for r in ann]
    ass_fte = [r["assets_per_fte_mio"] for r in ann]

    clean_ax(ax1, "y")
    ax1.bar(x, pers, width=0.58, color=NAVY, label="Personalaufwand (Mio. CHF)", zorder=2)
    ax1.bar(x, gen, bottom=pers, width=0.58, color=SKY, label="Sachaufwand (Mio. CHF)", zorder=2)
    ax1.set_ylabel("Geschäftsaufwand (Mio. CHF)", fontweight="bold", color=NAVY)
    ax1.set_ylim(0, 390)

    ax1r = ax1.twinx()
    ax1r.spines["top"].set_visible(False)
    ax1r.plot(x, cir, color=RED, lw=1.7, linestyle="--", marker="o", ms=3.8, label="CIR berichtet (%)")
    ax1r.plot(x, cir_clean, color=AMBER, lw=2.4, marker="s", ms=4.2, label="CIR bereinigt (ohne PK-Einmaleffekt 2015, %)")
    ax1r.set_ylabel("Cost-Income-Ratio (%)", fontweight="bold", color=RED)
    ax1r.set_ylim(40, 82)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax1r.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", ncol=2, fontsize=8.2)

    clean_ax(ax2, "y")
    ax2.bar(x, fte, width=0.55, color="#CBD5E1", label="Vollzeitstellen (FTE)", zorder=2)
    ax2.set_ylabel("Vollzeitstellen (FTE)", fontweight="bold", color=SLATE)
    ax2.set_ylim(0, 1450)

    ax2r = ax2.twinx()
    ax2r.spines["top"].set_visible(False)
    ax2r.plot(x, inc_fte, color=TEAL, lw=2.5, marker="o", ms=4.5, label="Geschäftsertrag / FTE (TCHF)")
    ax2r.plot(x, [v * 10.0 for v in ass_fte], color=BLUE, lw=2.2, linestyle="-.", marker="^", ms=4.2, label="Bilanzsumme / FTE (in 100'000 CHF)")
    ax2r.set_ylabel("Produktivität (TCHF bzw. 0,1 Mio. / FTE)", fontweight="bold", color=TEAL)
    ax2r.set_ylim(100, 620)
    h3, l3 = ax2.get_legend_handles_labels()
    h4, l4 = ax2r.get_legend_handles_labels()
    ax2.legend(h3 + h4, l3 + l4, loc="upper left", ncol=2, fontsize=8.2)

    ax2.set_xticks(x)
    ax2.set_xticklabels([str(y) for y in years], rotation=45, ha="right")

    add_footer(fig, "Quelle: BEKB Geschäftsberichte 2003–2025 (data/bekb_panel_annual.csv). 2015 PK-Einmaleinlage 83,8 Mio. CHF separat bereinigt.")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.93])
    fig.savefig(CHARTS_DIR / "04_effizienz_produktivitaet_2003_2025.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 10. Aktie, Dividende & Rückfluss an die öffentliche Hand (2003–2025)
# ---------------------------------------------------------------------------

def chart_05_aktie_dividende_kanton(ann: list[dict]) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13.5, 8.2), sharex=True)
    fig.suptitle(
        "BEKB-Aktie, 30. Dividendenerhöhung in Folge & 1,61 Mrd. CHF für die öffentliche Hand (2003–2025)",
        fontsize=13.8, fontweight="bold", color=NAVY, y=0.965,
    )

    years = [r["year"] for r in ann]
    x = np.arange(len(years))
    px = [r["share_price_eoy"] for r in ann]
    div = [r["dividend_per_share"] for r in ann]
    taxes = [r["taxes_public_mio"] or 0.0 for r in ann]
    div_kt = [r["dividend_canton_mio"] or 0.0 for r in ann]
    guar = [r["canton_guarantee_fee_mio"] or 0.0 for r in ann]

    clean_ax(ax1, "y")
    ax1.fill_between(x, px, color="#DBEAFE", alpha=0.55)
    ax1.plot(x, px, color=NAVY, lw=2.5, marker="o", ms=4.5, label="Aktienkurs Jahresende (CHF)", zorder=4)
    ax1.set_ylabel("Aktienkurs (CHF)", fontweight="bold", color=NAVY)
    ax1.set_ylim(100, 355)
    ax1.text(len(x) - 1, px[-1] + 10, f"Kurs 2025: CHF {px[-1]:.2f}", ha="right", va="bottom", fontsize=8.6, fontweight="bold", color=NAVY)

    ax1r = ax1.twinx()
    ax1r.spines["top"].set_visible(False)
    ax1r.plot(x, div, color=RED, lw=2.5, marker="s", ms=4.5, label="Ordentliche Dividende je Aktie (CHF)")
    idx_12 = years.index(2012)
    ax1r.scatter([idx_12], [10.6], color=GOLD, edgecolor=RED, s=75, zorder=6, label="2012 inkl. Sonderdividende (CHF 10.60)")
    ax1r.set_ylabel("Dividende je Aktie (CHF)", fontweight="bold", color=RED)
    ax1r.set_ylim(0, 13.5)
    ax1r.text(len(x) - 1.25, div[-1] - 0.85, f"Div. 2025: CHF {div[-1]:.2f}", ha="right", va="top", fontsize=8.6, fontweight="bold", color=RED)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax1r.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", ncol=2, fontsize=8.2)

    clean_ax(ax2, "y")
    ax2.bar(x, div_kt, width=0.58, color=RED, label=f"Dividende an Kanton Bern (Summe: {ch_num(sum(div_kt), 1)} Mio.)", zorder=3)
    ax2.bar(x, taxes, bottom=div_kt, width=0.58, color=NAVY, label=f"Steuern Bund/Kanton/Gem. (Summe: {ch_num(sum(taxes), 1)} Mio.)", zorder=3)
    bot2 = [a + b for a, b in zip(div_kt, taxes)]
    ax2.bar(x, guar, bottom=bot2, width=0.58, color=AMBER, label=f"Abgeltung Staatsgarantie bis 2013 (Summe: {ch_num(sum(guar), 1)} Mio.)", zorder=3)
    ax2.set_ylabel("Rückfluss öff. Hand (Mio. CHF)", fontweight="bold", color=NAVY)
    ax2.set_ylim(0, 122)
    ax2.legend(loc="upper left", ncol=1, fontsize=8.2)

    ax2.set_xticks(x)
    ax2.set_xticklabels([str(y) for y in years], rotation=45, ha="right")

    add_footer(fig, "Quelle: BEKB Geschäftsberichte 2003–2025 (data/bekb_panel_annual.csv). Gesamtrückfluss 2003–2025: 1'607,4 Mio. CHF.")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.93])
    fig.savefig(CHARTS_DIR / "05_aktie_dividende_kanton_2003_2025.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 11. Semester-Saisonalität & Reservensteuerung H1 vs. H2 (2013–2026)
# ---------------------------------------------------------------------------

def chart_06_semester_saisonalitaet(sem: list[dict]) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13.5, 8.2), sharex=True)
    fig.suptitle(
        "Unterjährige Dynamik (2013–2026): Hohe Ertragsplanbarkeit & Antizyklische Reservensteuerung",
        fontsize=13.8, fontweight="bold", color=NAVY, y=0.965,
    )

    periods = [r["period"] for r in sem]
    x = np.arange(len(periods))
    h1_inc = [r["total_operating_income_mio"] for r in sem]
    h2_inc = [(r["fy_income_mio"] - r["total_operating_income_mio"]) if r["fy_income_mio"] else 0.0 for r in sem]
    h1_share = [r["h1_share_of_fy_income_pct"] for r in sem]

    clean_ax(ax1, "y")
    ax1.bar(x, h1_inc, width=0.55, color=NAVY, label="Geschäftsertrag H1 (Mio. CHF)", zorder=3)
    ax1.bar(x[:-1], h2_inc[:-1], bottom=h1_inc[:-1], width=0.55, color=SKY, label="Geschäftsertrag H2 implizit (Mio. CHF)", zorder=3)
    ax1.set_ylabel("Geschäftsertrag (Mio. CHF)", fontweight="bold", color=NAVY)
    ax1.set_ylim(0, 645)
    ax1.text(len(x) - 1, h1_inc[-1] + 14, f"H1-26:\n{ch_num(h1_inc[-1])} Mio.", ha="center", fontsize=8.3, fontweight="bold", color=NAVY)

    ax1r = ax1.twinx()
    ax1r.spines["top"].set_visible(False)
    valid_idx = [i for i, v in enumerate(h1_share) if v is not None]
    ax1r.plot(valid_idx, [h1_share[i] for i in valid_idx], color=RED, lw=2.3, marker="o", ms=4.8, label="H1-Anteil am FY-Ertrag (%)")
    ax1r.axhline(49.7, color=RED, linestyle=":", lw=1.0, alpha=0.8)
    ax1r.set_ylabel("H1-Anteil (%)", fontweight="bold", color=RED)
    ax1r.set_ylim(35, 62)
    h_a, l_a = ax1.get_legend_handles_labels()
    h_b, l_b = ax1r.get_legend_handles_labels()
    ax1.legend(h_a + h_b, l_a + l_b, loc="upper left", ncol=3, fontsize=8.1)

    clean_ax(ax2, "y")
    h1_res = [r["reserves_change_mio"] if r["reserves_change_mio"] is not None else 0.0 for r in sem]
    h2_res = [r["h2_implied_reserves_change_mio"] if r["h2_implied_reserves_change_mio"] is not None else 0.0 for r in sem]
    w = 0.35
    ax2.bar(x - w / 2, h1_res, width=w, color=BLUE, label="Reserven-Veränderung H1 (– Bildung / + Auflösung)", zorder=3)
    ax2.bar(x[:-1] + w / 2, h2_res[:-1], width=w, color=TEAL, label="Reserven-Veränderung H2 implizit (Mio. CHF)", zorder=3)
    ax2.axhline(0, color=NAVY, lw=1.0)
    ax2.set_ylabel("Reservenänderung (Mio. CHF)", fontweight="bold", color=NAVY)
    ax2.set_ylim(-58, 66)

    idx_20 = periods.index("H1-2020")
    ax2.text(idx_20 + w / 2, h2_res[idx_20] + 2.5, "+51,8 Mio.\n(COVID-Aufl.)", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=TEAL)

    ax2.legend(loc="lower left", ncol=2, fontsize=8.2)
    ax2.set_xticks(x)
    ax2.set_xticklabels(periods, rotation=45, ha="right")

    add_footer(fig, "Quelle: BEKB Semesterberichte H1-2013–H1-2026 & Geschäftsberichte 2013–2025 (data/bekb_panel_semester.csv).")
    plt.tight_layout(rect=[0.01, 0.04, 0.99, 0.93])
    fig.savefig(CHARTS_DIR / "06_semester_saisonalitaet_reserven_2013_2026.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 12. Langfrist-Dashboard & Strategische Epochen (2003 = 100)
# ---------------------------------------------------------------------------

def chart_07_langfrist_dashboard(ann: list[dict], sem: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(14.0, 7.2))
    clean_ax(ax, "y")

    years = [r["year"] for r in ann]
    x = np.arange(len(years))

    def idx_series(key: str) -> list[float]:
        base = ann[0][key]
        return [r[key] / base * 100.0 for r in ann]

    ax.axvspan(-0.5, 9.5, color="#F1F5F9", alpha=0.8, zorder=0)
    ax.axvspan(9.5, 16.5, color="#EFF6FF", alpha=0.7, zorder=0)
    ax.axvspan(16.5, len(years) - 0.5, color="#ECFDF5", alpha=0.7, zorder=0)

    ax.text(4.5, 398, "Epoche 1 (2003–2012)\nFCF / NEM & Expansion", ha="center", va="top", fontsize=9.2, fontweight="bold", color=SLATE)
    ax.text(13.0, 398, "Epoche 2 (2013–2019)\nLangfrist, RVB & Substanz", ha="center", va="top", fontsize=9.2, fontweight="bold", color=BLUE)
    ax.text(19.5, 398, "Epoche 3 (2020–2025)\nStrategie 2025 & Zinswende", ha="center", va="top", fontsize=9.2, fontweight="bold", color=TEAL)

    series = [
        ("dividend_per_share", "Dividende je Aktie (3.00 → 10.80 CHF)", RED, 2.7, "o", 0.0),
        ("mortgage_loans_mio", "Hypothekarforderungen (12,0 → 30,1 Mrd.)", NAVY, 2.4, "s", 4.0),
        ("net_profit_mio", "Jahresgewinn (71,1 → 175,4 Mio.)", TEAL, 2.3, "D", -5.0),
        ("total_assets_mio", "Bilanzsumme (20,1 → 43,0 Mrd.)", BLUE, 2.2, "^", 3.5),
        ("share_price_eoy", "Aktienkurs 31.12. (149.00 → 309.50 CHF)", AMBER, 2.0, "v", -4.5),
        ("total_operating_income_mio", "Geschäftsertrag (418,1 → 547,3 Mio.)", PURPLE, 1.9, "P", 0.0),
        ("fte_count", "Vollzeitstellen FTE (1'210 → 1'058)", SLATE, 1.9, "--", 0.0),
    ]

    for key, lbl, col, lw, marker, y_nudge in series:
        vals = idx_series(key)
        if marker == "--":
            ax.plot(x, vals, color=col, lw=lw, linestyle="--", label=lbl, zorder=4)
        else:
            ax.plot(x, vals, color=col, lw=lw, marker=marker, ms=4.2, label=lbl, zorder=4)
        ax.text(len(x) - 0.85, vals[-1] + y_nudge, f" {vals[-1]:.0f}", va="center", ha="left", fontsize=8.3, fontweight="bold", color=col)

    ax.axhline(100.0, color="#94A3B8", lw=1.0, linestyle=":")
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years], rotation=45, ha="right")
    ax.set_xlim(-0.5, len(years) + 0.65)
    ax.set_ylim(60, 412)
    ax.set_ylabel("Index (Basis 2003 = 100)", fontweight="bold", color=NAVY)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=3, fontsize=8.4)

    fig.suptitle(
        "Langfrist-Scorecard über drei Strategie-Epochen (2003 = 100 bis 2025): Wertwachstum bei stabilen Ressourcen",
        fontsize=13.8, fontweight="bold", color=NAVY, y=0.96,
    )
    add_footer(fig, "Quelle: BEKB Geschäftsberichte 2003–2025 (data/bekb_panel_annual.csv). Spitze 2007 beim Jahresgewinn reflektiert den einmaligen BKW-Beteiligungsverkauf (Index 332).")
    plt.tight_layout(rect=[0.01, 0.08, 0.99, 0.92])
    fig.savefig(CHARTS_DIR / "07_langfrist_dashboard_epochen_2003_2026.png", dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 13. Gesamtgewinn vs. Lohnkosten, VR-, CEO-, GL- & FTE-Vergütung (real 2025 CHF)
# ---------------------------------------------------------------------------

def chart_07_gewinn_loehne_verguetung_real(comp: list[dict]) -> None:
    fig = plt.figure(figsize=(15.6, 12.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.22, 1.0], hspace=0.50, wspace=0.18)
    ax_idx = fig.add_subplot(gs[0, :])
    ax_mac = fig.add_subplot(gs[1, 0])
    ax_pk = fig.add_subplot(gs[1, 1])

    years = [r["year"] for r in comp]
    x = np.arange(len(years))
    base_2008 = next(r for r in comp if r["year"] == 2008)

    fig.suptitle(
        "Gesamtgewinn vs. Lohnkosten, VR-, CEO-, GL- und FTE-Vergütung (2003–2025, rückwirkend inflationsbereinigt)",
        fontsize=14.0, fontweight="bold", color=NAVY, y=0.972,
    )
    fig.text(
        0.5, 0.943,
        "Alle Frankenwerte real in Kaufkraft 2025 gemäss BFS-Landesindex der Konsumentenpreise (LIK Dez. 1982 = 100; 2003: 150,7 → 2025: 169,7)",
        ha="center", va="top", fontsize=9.5, color=SLATE,
    )

    # --- Panel A: Reale Indexentwicklung (Basis 2008 = 100) ---
    clean_ax(ax_idx, "y")
    ax_idx.set_title(
        "A) Reale Entwicklung im Indexvergleich (Basis 2008 = 100, Kaufkraft 2025)",
        color=NAVY, pad=10, loc="left", fontsize=11.5,
    )

    # Hintergrund-Markierung ab 2013 (VegüV inkl. gesetzl. AHV/IV/ALV)
    idx_13 = years.index(2013)
    ax_idx.axvline(idx_13 - 0.5, color="#94A3B8", linestyle="--", lw=1.0, zorder=1)
    ax_idx.text(
        idx_13 - 0.35, 224,
        "Ab 2013: VegüV-Ausweis\n(inkl. gesetzl. AHV/IV/ALV)",
        fontsize=8.0, color=SLATE, va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=0.7),
    )

    # Undisclosed Kurzberichte 2003 & 2006 leicht schattieren
    for u_y in (2003, 2006):
        ui = years.index(u_y)
        ax_idx.axvspan(ui - 0.4, ui + 0.4, color="#E2E8F0", alpha=0.45, zorder=0)

    ax_idx.axhline(100.0, color="#64748B", lw=1.1, linestyle=":", zorder=1)

    series_spec = [
        ("net_profit_mio_real2025", "Gesamtgewinn real (2008: 119,3 → 2025: 175,4 Mio.)", TEAL, 2.7, "D", 0.0),
        ("avg_per_fte_tchf_real2025", "Ø Personalaufwand / FTE real (127,2 → 145,4 TCHF)", BLUE, 2.3, "o", 1.5),
        ("personnel_ord_mio_real2025", "Lohnkosten gesamt real ord. (149,0 → 153,8 Mio.)", NAVY, 2.3, "s", 3.2),
        ("ceo_total_tchf_real2025", "CEO-Lohn real (1'018 → 998 TCHF)", RED, 2.3, "^", 0.0),
        ("gl_ex_ceo_avg_tchf_real2025", "Ø GL-Mitglied ohne CEO real (705 → 658 TCHF)", AMBER, 2.2, "P", -3.4),
        ("vr_avg_tchf_real2025", "Ø VR-Mitglied real (207 → 161 TCHF)", PURPLE, 2.2, "v", 0.0),
    ]

    for col, lbl, color, lw, marker, y_nudge in series_spec:
        bval = base_2008[col]
        vals = [(r[col] / bval * 100.0) if r[col] is not None else None for r in comp]
        valid_i = [i for i, v in enumerate(vals) if v is not None]
        segments: list[list[int]] = []
        cur: list[int] = []
        for idx_pt in valid_i:
            if cur and idx_pt != cur[-1] + 1:
                segments.append(cur)
                cur = [idx_pt]
            else:
                cur.append(idx_pt)
        if cur:
            segments.append(cur)

        for s_i, seg in enumerate(segments):
            sx = [x[i] for i in seg]
            sy = [vals[i] for i in seg]
            ax_idx.plot(
                sx, sy, color=color, lw=lw, marker=marker, ms=4.3,
                label=lbl if s_i == len(segments) - 1 else None, zorder=4,
            )
            if s_i > 0:
                prev_end = segments[s_i - 1][-1]
                cur_start = seg[0]
                ax_idx.plot(
                    [x[prev_end], x[cur_start]],
                    [vals[prev_end], vals[cur_start]],
                    color=color, lw=lw * 0.75, linestyle=":", alpha=0.65, zorder=3,
                )

        end_val = vals[-1]
        pct_str = f"{end_val - 100.0:+.1f} %".replace(".", ",")
        ax_idx.text(
            len(x) - 0.68, end_val + y_nudge,
            f" {end_val:.0f} ({pct_str})",
            va="center", ha="left", fontsize=8.3, fontweight="bold", color=color,
        )

    # Spezifische Meilenstein-Annotationen in Panel A (alle im freien Weissraum)
    idx_07 = years.index(2007)
    bkw_idx_val = comp[idx_07]["net_profit_mio_real2025"] / base_2008["net_profit_mio_real2025"] * 100.0
    ax_idx.annotate(
        "2007: BKW-Einmalverkauf\n(256,3 Mio. CHF real / Index 215)",
        xy=(idx_07, bkw_idx_val), xytext=(idx_07 + 0.9, 206),
        fontsize=8.0, fontweight="bold", color=TEAL,
        arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.0),
    )

    idx_17 = years.index(2017)
    vr_17_val = comp[idx_17]["vr_avg_tchf_real2025"] / base_2008["vr_avg_tchf_real2025"] * 100.0
    ax_idx.annotate(
        "Ab 2017: Verzicht auf\nvariable VR-Vergütung",
        xy=(idx_17, vr_17_val), xytext=(idx_17 - 1.5, 66),
        fontsize=7.9, fontweight="bold", color=PURPLE, ha="center",
        arrowprops=dict(arrowstyle="->", color=PURPLE, lw=1.0),
    )

    idx_19 = years.index(2019)
    ceo_19_val = comp[idx_19]["ceo_total_tchf_real2025"] / base_2008["ceo_total_tchf_real2025"] * 100.0
    ax_idx.annotate(
        "2019: CEO-Wechsel\n(6 Mt. GL / 6 Mt. CEO)",
        xy=(idx_19, ceo_19_val), xytext=(idx_19 + 0.3, 66),
        fontsize=7.9, fontweight="bold", color=RED, ha="center",
        arrowprops=dict(arrowstyle="->", color=RED, lw=1.0),
    )

    idx_22 = years.index(2022)
    fte_22_val = comp[idx_22]["avg_per_fte_tchf_real2025"] / base_2008["avg_per_fte_tchf_real2025"] * 100.0
    ax_idx.annotate(
        "2022: aity IT-Ausl.\n(940 FTE, Ø 157,6 TCHF)",
        xy=(idx_22, fte_22_val), xytext=(idx_22 - 1.5, 168),
        fontsize=7.9, fontweight="bold", color=BLUE, ha="center",
        bbox=dict(boxstyle="round,pad=0.22", facecolor="#FFFFFF", edgecolor="#BFDBFE", alpha=0.92),
        arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.0, connectionstyle="arc3,rad=-0.12"),
    )

    ax_idx.set_xticks(x)
    ax_idx.set_xticklabels([str(y) for y in years], rotation=45, ha="right")
    ax_idx.set_xlim(-0.6, len(years) + 2.45)
    ax_idx.set_ylim(58, 232)
    ax_idx.set_ylabel("Real-Index (Basis 2008 = 100)", fontweight="bold", color=NAVY)
    ax_idx.legend(loc="upper center", bbox_to_anchor=(0.5, -0.175), ncol=3, fontsize=8.3)

    # --- Panel B: Makro-Ebene Gesamtgewinn vs. Lohnkosten in real 2025 Mio. CHF ---
    clean_ax(ax_mac, "y")
    ax_mac.set_title(
        "B) Gesamtgewinn vs. Lohnkosten (real 2025 Mio. CHF)",
        color=NAVY, pad=10, loc="left", fontsize=11.0,
    )
    prof_r = [r["net_profit_mio_real2025"] for r in comp]
    pers_r = [r["personnel_ord_mio_real2025"] for r in comp]

    ax_mac.bar(
        x, pers_r, width=0.58, color="#CBD5E1", edgecolor="#64748B", linewidth=0.6,
        label=f"Lohnkosten gesamt ord. (2025: {ch_num(pers_r[-1])} Mio.)", zorder=2,
    )
    ax_mac.plot(
        x, prof_r, color=TEAL, lw=2.5, marker="D", ms=4.2,
        label=f"Gesamtgewinn (2025: {ch_num(prof_r[-1])} Mio.)", zorder=4,
    )
    ax_mac.fill_between(
        x, pers_r, prof_r,
        where=[p >= w for p, w in zip(prof_r, pers_r)],
        interpolate=True, color="#99F6E4", alpha=0.45, zorder=1,
        label="Gewinn > Lohnkosten (ab 2018)",
    )
    ax_mac.text(idx_07 + 0.55, prof_r[idx_07] - 6, "256,3 Mio.\n(BKW 2007)", fontsize=7.9, fontweight="bold", color=TEAL, va="top")
    ax_mac.annotate(
        f"2025: {ch_num(prof_r[-1])} Mio.",
        xy=(len(x) - 1, prof_r[-1]), xytext=(len(x) - 1.5, 205),
        ha="right", fontsize=8.1, fontweight="bold", color=TEAL,
        arrowprops=dict(arrowstyle="->", color=TEAL, lw=0.9),
    )

    ax_mac.set_xticks(x[::2])
    ax_mac.set_xticklabels([str(years[i]) for i in range(0, len(years), 2)], rotation=45, ha="right")
    ax_mac.set_xlim(-0.7, len(years) - 0.1)
    ax_mac.set_ylim(0, 285)
    ax_mac.set_ylabel("Mio. CHF (Kaufkraft 2025)", fontweight="bold", color=NAVY)
    ax_mac.legend(loc="upper right", fontsize=8.0)

    # --- Panel C: Pro-Kopf-Ebene in real 2025 TCHF ---
    clean_ax(ax_pk, "y")
    ax_pk.set_title(
        "C) Pro-Kopf-Vergütung im Zeitverlauf (real 2025 TCHF)",
        color=NAVY, pad=10, loc="left", fontsize=11.0,
    )

    pk_specs = [
        ("ceo_total_tchf_real2025", "CEO-Lohn (2025: 998 TCHF)", RED, 2.3, "^", 0.0),
        ("gl_ex_ceo_avg_tchf_real2025", "Ø GL ohne CEO (2025: 658 TCHF)", AMBER, 2.2, "P", 0.0),
        ("vr_avg_tchf_real2025", "Ø VR-Mitglied (2025: 161 TCHF)", PURPLE, 2.2, "v", 28.0),
        ("avg_per_fte_tchf_real2025", "Ø Personalaufw. / FTE (2025: 145 TCHF)", BLUE, 2.2, "o", -32.0),
    ]
    for col, lbl, color, lw, marker, end_nudge in pk_specs:
        vals = [r[col] for r in comp]
        valid_i = [i for i, v in enumerate(vals) if v is not None]
        segments = []
        cur = []
        for idx_pt in valid_i:
            if cur and idx_pt != cur[-1] + 1:
                segments.append(cur)
                cur = [idx_pt]
            else:
                cur.append(idx_pt)
        if cur:
            segments.append(cur)
        for s_i, seg in enumerate(segments):
            ax_pk.plot(
                [x[i] for i in seg], [vals[i] for i in seg],
                color=color, lw=lw, marker=marker, ms=4.0,
                label=lbl if s_i == len(segments) - 1 else None, zorder=4,
            )
            if s_i > 0:
                pe, cs = segments[s_i - 1][-1], seg[0]
                ax_pk.plot([x[pe], x[cs]], [vals[pe], vals[cs]], color=color, lw=lw * 0.75, linestyle=":", alpha=0.65, zorder=3)
        ev = vals[-1]
        ax_pk.text(len(x) - 0.65, ev + end_nudge, f" {ev:,.0f}".replace(",", "'"), va="center", ha="left", fontsize=8.2, fontweight="bold", color=color)

    ax_pk.set_xticks(x[::2])
    ax_pk.set_xticklabels([str(years[i]) for i in range(0, len(years), 2)], rotation=45, ha="right")
    ax_pk.set_xlim(-0.6, len(years) + 1.8)
    ax_pk.set_ylim(0, 1260)
    ax_pk.set_ylabel("TCHF (Kaufkraft 2025)", fontweight="bold", color=NAVY)
    ax_pk.legend(loc="center", bbox_to_anchor=(0.48, 0.38), ncol=2, fontsize=7.6)

    add_footer(
        fig,
        "Quellen: BEKB Geschäftsberichte 2003–2025 (data/bekb_verguetung_real_2003_2025.csv) & BFS LIK Jahresdurchschnitt. "
        "Ordentliche Vergütungen exkl. Einmaleffekte (2012/2017 NP & Pensionierung; 2013/2015 PK-Sanierung). 2003 & 2006 Kurzberichte ohne VR/GL-Tabellen."
    )
    plt.subplots_adjust(left=0.06, right=0.92, top=0.895, bottom=0.085)
    fig.savefig(CHARTS_DIR / "07_gewinn_loehne_verguetung_real_2003_2025.png", dpi=220)
    plt.close(fig)


def main() -> None:
    setup_style()
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    ann, sem, off = load_panel()
    comp = load_verguetung_real()

    chart_02_bilanz_gestapelte_saeulen()
    chart_02_bilanz_treemap()
    chart_02_bilanz_sankey()
    chart_02_bilanz_langfrist(ann, sem)
    chart_01_erfolgsrechnung_wasserfall()
    chart_01_ertrag_kosten_marge_kombi(ann)
    chart_03_soll_ist_horizontal(off, ann, sem)
    chart_03_kapital_rwa_basel(off)
    chart_04_effizienz_produktivitaet(ann)
    chart_05_aktie_dividende_kanton(ann)
    chart_06_semester_saisonalitaet(sem)
    chart_07_langfrist_dashboard(ann, sem)
    chart_07_gewinn_loehne_verguetung_real(comp)

    charts = sorted(CHARTS_DIR.glob("*.png"))
    print(f"[OK] {len(charts)} Grafiken erfolgreich in {CHARTS_DIR.relative_to(ROOT)}/ erstellt:")
    for c in charts:
        print(f"  - {c.name} ({c.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

