#!/usr/bin/env python3
"""
Bereitet das Dokumentationsverzeichnis `.rtd_docs/` für MkDocs Material / Read the Docs vor.
Single-Source-of-Truth bleiben die Root-Dateien (README.md, ANALYSE_STRATEGIE.md, ROADMAP.md),
data/ sowie reports/, ohne PNG-Grafiken doppelt in Git zu speichern.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RTD_DIR = ROOT / ".rtd_docs"
REPO_BLOB_BASE = "https://github.com/chatelao/bekb-geschaeftsbereichte-analysen/blob/main"
REPO_TREE_BASE = "https://github.com/chatelao/bekb-geschaeftsbereichte-analysen/tree/main"


def clean_markdown_for_rtd(text: str, rel_kind: str) -> str:
    """Optimiert Links und LaTeX-Pfeile für strikte MkDocs-Builds."""
    # Pfeile für sofortiges, klares Tabellen-Rendering in Unicode umwandeln
    text = text.replace("$\\rightarrow$", "→")

    if rel_kind == "root_readme":
        # Links in root README.md -> .rtd_docs/index.md
        replacements = {
            "(./reports/README.md)": "(reports/index.md)",
            "(./reports/": "(reports/",
            "(./ANALYSE_STRATEGIE.md)": "(ANALYSE_STRATEGIE.md)",
            "(./ROADMAP.md)": "(ROADMAP.md)",
            "(./data/validation_report.md)": "(data/validation_report.md)",
            "(./data/": "(data/",
            "(./download_reports.py)": f"({REPO_BLOB_BASE}/download_reports.py)",
            "(./convert_pdf_to_md.py)": f"({REPO_BLOB_BASE}/convert_pdf_to_md.py)",
            "(./scripts/": f"({REPO_BLOB_BASE}/scripts/",
            "(./.readthedocs.yaml)": f"({REPO_BLOB_BASE}/.readthedocs.yaml)",
            "(./mkdocs.yml)": f"({REPO_BLOB_BASE}/mkdocs.yml)",
            "(./.github/workflows/docs-cicd.yml)": f"({REPO_BLOB_BASE}/.github/workflows/docs-cicd.yml)",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
    elif rel_kind == "reports_readme":
        replacements = {
            "(../ANALYSE_STRATEGIE.md)": "(../ANALYSE_STRATEGIE.md)",
            "(../data/validation_report.md)": "(../data/validation_report.md)",
            "(../scripts/generate_charts.py)": f"({REPO_BLOB_BASE}/scripts/generate_charts.py)",
            "(./charts/)": f"({REPO_TREE_BASE}/reports/charts)",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

    return text


def build_gallery_page() -> str:
    """Erstellt eine übersichtliche Grafik-Galerie aller 13 Visualisierungen."""
    charts = [
        (
            "Langfrist-Scorecard & Strategie-Epochen (2003 = 100)",
            "07_langfrist_dashboard_epochen_2003_2026.png",
            "07_strategische_epochen_und_governance_2003_2026.md",
            "Wertwachstum über die Epochen 2003–2012, 2013–2019 und 2020–2025 bei sinkendem FTE-Bestand.",
        ),
        (
            "Gesamtgewinn vs. Lohnkosten & Pro-Kopf-Vergütung (real 2025 CHF)",
            "07_gewinn_loehne_verguetung_real_2003_2025.png",
            "07_strategische_epochen_und_governance_2003_2026.md",
            "Inflationsbereinigt (BFS LIK): Gewinn +110 % (2004–2025), Personal/FTE +15,5 %, reale VR-/GL-/CEO-Saläre rückläufig.",
        ),
        (
            "Erfolgsrechnung 2025 – Wasserfalldiagramm (Bridge Chart)",
            "01_erfolgsrechnung_wasserfall_2025.png",
            "01_zinszyklen_und_ertragsarchitektur_2003_2025.md",
            "Vom Bruttoertrag über Personal-, Sachaufwand, Abschreibungen, Reserven und Steuern zum Reingewinn von 175,4 Mio. CHF.",
        ),
        (
            "Ertrag, Aufwand & Reingewinnmarge (2003–2025)",
            "01_ertrag_kosten_marge_kombi_2003_2025.png",
            "01_zinszyklen_und_ertragsarchitektur_2003_2025.md",
            "Kombiniertes Säulen- und Liniendiagramm über alle Zinszyklen inkl. SNB-Negativzinsphase und Zinswende.",
        ),
        (
            "Bilanzgleichung 2025 – Gestapelte Säulen (Absolut & 100 %)",
            "02_bilanz_gestapelte_saeulen_2025.png",
            "02_bilanzwachstum_hypotheken_und_refinanzierung_2003_2026.md",
            "Gegenüberstellung von Aktiven und Passiven bei 42'977,0 Mio. CHF Bilanzsumme.",
        ),
        (
            "Detaillierte Bilanz-Treemap 2025",
            "02_bilanz_treemap_2025.png",
            "02_bilanzwachstum_hypotheken_und_refinanzierung_2003_2026.md",
            "Flächenproportionale Struktur aller Vermögens- und Finanzierungspositionen.",
        ),
        (
            "Mittelherkunft → Mittelverwendung (Sankey-Diagramm 2025)",
            "02_bilanz_sankey_2025.png",
            "02_bilanzwachstum_hypotheken_und_refinanzierung_2003_2026.md",
            "Verknüpfung von Refinanzierung und Aktivgeschäft inkl. Prüfung der Goldenen Bilanzregel.",
        ),
        (
            "Langfristiges Bilanz- & Hypothekarwachstum (2003–H1-2026)",
            "02_bilanz_langfrist_wachstum_2003_2026.png",
            "02_bilanzwachstum_hypotheken_und_refinanzierung_2003_2026.md",
            "Ausbau der Bilanz auf 44,65 Mrd. CHF sowie Deckungsgrad durch Kundeneinlagen.",
        ),
        (
            "Aufsichtsrechtlicher Soll-Ist-Vergleich (06-2026)",
            "03_soll_ist_vergleich_horizontal_2026.png",
            "03_aufsichtsrechtliche_resilienz_basel_iii_2015_2026.md",
            "Komfortable Puffer gegenüber FINMA-Zielquoten und Liquiditäts-Mindestanforderungen.",
        ),
        (
            "Basel III & Basel III final: Kapital, RWA & Liquidität (2015–06-2026)",
            "03_kapital_rwa_basel_2015_2026.png",
            "03_aufsichtsrechtliche_resilienz_basel_iii_2015_2026.md",
            "20 Stichtage inklusive Basel-III-final-Effekt ab 2025, Leverage Ratio, LCR und NSFR.",
        ),
        (
            "Operative Effizienz, CIR & Produktivität je FTE (2003–2025)",
            "04_effizienz_produktivitaet_2003_2025.png",
            "04_operative_effizienz_und_transformation_2003_2025.md",
            "Bereinigte Cost-Income-Ratio (ohne PK-Einmalzuweisung 2015) sowie Ertrag und Bilanz je Vollzeitstelle.",
        ),
        (
            "BEKB-Aktie, Dividendenkontinuität & Öffentliche Hand (2003–2025)",
            "05_aktie_dividende_kanton_2003_2025.png",
            "05_aktie_dividenden_und_wertschoepfung_2003_2025.md",
            "30. Dividendenerhöhung in Folge (CHF 3.00 → 10.80) und kumuliert 1'607,4 Mio. CHF an Bund, Kanton und Gemeinden.",
        ),
        (
            "Semester-Saisonalität & Reservensteuerung H1 vs. H2 (2013–2026)",
            "06_semester_saisonalitaet_reserven_2013_2026.png",
            "06_unterjaehrige_dynamik_semesterberichte_2013_2026.md",
            "Hohe Ertragsstabilität (Ø 49,7 % im H1) und antizyklische Steuerung der Bankrisikoreserven.",
        ),
    ]

    lines = [
        "# Grafik-Galerie: Alle 13 Visualisierungen (2003–2026)",
        "",
        "> Sämtliche Grafiken werden deterministisch durch [`generate_charts.py`]("
        f"{REPO_BLOB_BASE}/scripts/generate_charts.py) aus den validierten Datensätzen erzeugt.",
        "",
    ]
    for title, png, report, desc in charts:
        lines.extend([
            f"## {title}",
            "",
            f"{desc} → [Zum vollständigen Bericht](./{report})",
            "",
            f"![{title}](./charts/{png})",
            "",
        ])
    return "\n".join(lines)


def main() -> None:
    if RTD_DIR.exists():
        shutil.rmtree(RTD_DIR)
    RTD_DIR.mkdir(parents=True, exist_ok=True)

    # Root-Dokumente
    (RTD_DIR / "index.md").write_text(
        clean_markdown_for_rtd((ROOT / "README.md").read_text(encoding="utf-8"), "root_readme"),
        encoding="utf-8",
    )
    (RTD_DIR / "ANALYSE_STRATEGIE.md").write_text(
        clean_markdown_for_rtd((ROOT / "ANALYSE_STRATEGIE.md").read_text(encoding="utf-8"), "other"),
        encoding="utf-8",
    )
    (RTD_DIR / "ROADMAP.md").write_text(
        clean_markdown_for_rtd((ROOT / "ROADMAP.md").read_text(encoding="utf-8"), "other"),
        encoding="utf-8",
    )

    # Data-Audit & CSV/JSON-Artefakte (ohne chunks/extracted Rohdaten)
    rtd_data = RTD_DIR / "data"
    rtd_data.mkdir(parents=True, exist_ok=True)
    (rtd_data / "validation_report.md").write_text(
        clean_markdown_for_rtd((ROOT / "data" / "validation_report.md").read_text(encoding="utf-8"), "other"),
        encoding="utf-8",
    )
    for asset in list((ROOT / "data").glob("*.csv")) + [ROOT / "data" / "bekb_panel_all.json"]:
        shutil.copy2(asset, rtd_data / asset.name)

    # Reports & Charts
    rtd_reports = RTD_DIR / "reports"
    rtd_reports.mkdir(parents=True, exist_ok=True)
    for md in sorted((ROOT / "reports").glob("*.md")):
        raw = md.read_text(encoding="utf-8")
        if md.name == "README.md":
            (rtd_reports / "index.md").write_text(
                clean_markdown_for_rtd(raw, "reports_readme"),
                encoding="utf-8",
            )
        else:
            (rtd_reports / md.name).write_text(
                clean_markdown_for_rtd(raw, "other"),
                encoding="utf-8",
            )
    (rtd_reports / "galerie.md").write_text(build_gallery_page(), encoding="utf-8")

    shutil.copytree(ROOT / "reports" / "charts", rtd_reports / "charts")

    # Theme Assets
    if (ROOT / "docs_assets").exists():
        for item in (ROOT / "docs_assets").iterdir():
            dest = RTD_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    print(f"[OK] Read-the-Docs-Staging unter {RTD_DIR.relative_to(ROOT)}/ erstellt.")


if __name__ == "__main__":
    main()
