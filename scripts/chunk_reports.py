#!/usr/bin/env python3
"""
Stufe 1 der Hydrogen-Analysestrategie: Deterministischer Markdown-Chunker.

Zerlegt alle 57 BEKB-Berichte (.md/*.md) anhand von Überschriften und
Schlüsselwörtern in kleine, aufgabenspezifische Chunks (< 2.500 Tokens),
damit ein kompaktes Modell (z. B. Gemini Hydrogen) sie ohne Kontextverlust
präzise im Map-Schritt auslesen kann.
"""

import json
import re
from pathlib import Path

MD_DIR = Path(".md")
CHUNKS_DIR = Path("data/chunks")
MAX_CHUNK_CHARS = 9500  # ~2.200-2.400 Tokens


def detect_report_meta(filename: str) -> dict:
    stem = Path(filename).stem
    if stem.startswith("bekb-geschaeftsbericht-"):
        year = int(stem.rsplit("-", 1)[-1])
        return {"stem": stem, "report_type": "annual", "year": year, "period": f"FY{year}"}
    if stem.startswith("bekb-semesterbericht-"):
        year = int(stem.rsplit("-", 1)[-1])
        return {"stem": stem, "report_type": "semester", "year": year, "period": f"H1-{year}"}
    if stem.startswith("bekb-offenlegungsbericht-06-"):
        year = int(stem.rsplit("-", 1)[-1])
        return {"stem": stem, "report_type": "offenlegung_h1", "year": year, "period": f"H1-{year}"}
    if stem.startswith("bekb-offenlegungsbericht-"):
        year = int(stem.rsplit("-", 1)[-1])
        return {"stem": stem, "report_type": "offenlegung_fy", "year": year, "period": f"FY{year}"}
    raise ValueError(f"Unbekannter Dateiname: {filename}")


def is_toc_region(lines: list[str], idx: int) -> bool:
    window = "\n".join(lines[max(0, idx - 8):min(len(lines), idx + 4)])
    return bool(re.search(r"Tabellenbezeichnung|Übersicht der Tabellen|Inhaltsverzeichnis", window, re.I))


def find_window(lines: list[str], patterns: list[str], before: int = 12, after: int = 90,
                require_pipe: bool = True, prefer_last: bool = False,
                skip_toc: bool = False) -> str:
    """Sucht den besten Abschnitt rund um eines der Muster und begrenzt auf MAX_CHUNK_CHARS."""
    indices = []
    for idx, line in enumerate(lines):
        if require_pipe and "|" not in line:
            continue
        if skip_toc and is_toc_region(lines, idx):
            continue
        if any(re.search(pat, line, re.IGNORECASE) for pat in patterns):
            indices.append(idx)

    if not indices:
        return ""

    anchor = indices[-1] if prefer_last else indices[0]
    start = max(0, anchor - before)
    end = min(len(lines), anchor + after)
    text = "\n".join(lines[start:end]).strip()
    if len(text) > MAX_CHUNK_CHARS:
        text = text[:MAX_CHUNK_CHARS]
    return text


def find_all_matching_windows(lines: list[str], patterns: list[str], before: int = 12, after: int = 55,
                              require_pipe: bool = True, max_windows: int = 3,
                              skip_toc: bool = False) -> str:
    """Sammelt bis zu max_windows nicht-überlappende Fenster für Tabellen über Seitengrenzen."""
    ranges = []
    for idx, line in enumerate(lines):
        if require_pipe and "|" not in line:
            continue
        if skip_toc and is_toc_region(lines, idx):
            continue
        if any(re.search(pat, line, re.IGNORECASE) for pat in patterns):
            if not ranges or idx > ranges[-1][1] + 5:
                ranges.append([max(0, idx - before), min(len(lines), idx + after)])
            if len(ranges) >= max_windows:
                break

    blocks = ["\n".join(lines[s:e]).strip() for s, e in ranges]
    joined = "\n\n---\n\n".join(b for b in blocks if b)
    if len(joined) > MAX_CHUNK_CHARS:
        joined = joined[:MAX_CHUNK_CHARS]
    return joined


def extract_lagebericht_excerpt(lines: list[str], max_chars: int = 7500) -> str:
    """Extrahiert die ersten aussagekräftigen Textabschnitte (Lagebericht / Brief / Aktuell)."""
    collected = []
    total = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("![](") or stripped.startswith("|") or stripped.startswith("<!--"):
            continue
        if re.fullmatch(r"\d{1,3}", stripped):
            continue
        if any(k in stripped.lower() for k in ["impressum", "fotografie", "konzept und design", "druck", "titelbild"]):
            continue
        if len(stripped) > 40 or stripped.startswith("#"):
            collected.append(stripped)
            total += len(stripped) + 1
            if total >= max_chars:
                break
    return "\n".join(collected)


def chunk_report(md_path: Path) -> dict:
    meta = detect_report_meta(md_path.name)
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    chunks = {}

    if meta["report_type"] == "annual":
        chunks["bilanz"] = find_all_matching_windows(
            lines,
            [
                r"\|Hypothekarforderungen\||\|Créances hypothécaires\||Mortgage loans",
                r"\|Verpflichtungen aus Kundeneinlagen\||\|Verpflichtungen gegenüber Kunden\||\|Engagements envers la clientèle\|",
                r"\|Total Eigenkapital\||\|Total Passiven\||\|Total des capitaux propres\|",
            ],
            before=18,
            after=45,
            require_pipe=True,
            max_windows=3,
        )
        chunks["erfolgsrechnung"] = find_window(
            lines,
            [
                r"\|Zins- und Diskontertrag\||\|Produit des intérêts|^\|\*\*Erfolg aus dem Zinsengeschäft",
                r"\|Subtotal Erfolg Zinsengeschäft\||\|Subtotal Netto-Erfolg Zinsengeschäft\||\|Netto-Erfolg aus dem Zinsengeschäft\|",
                r"\|Geschäftserfolg\||\|Bruttogewinn\||\|Bénéfice brut\|",
            ],
            before=12,
            after=85,
            require_pipe=True,
            prefer_last=False,
        )
        chunks["mehrjahresvergleich"] = find_window(
            lines,
            [
                r"\|Personalbestand|BEKB im Mehrjahresvergleich|BEKB \| BCBE im Mehrjahresvergleich",
                r"\|Leistungen an die öffentliche Hand|Free cash flow \(FCF\)|\|Effectif du personnel",
            ],
            before=(38 if meta["year"] >= 2012 else 62),
            after=48,
            require_pipe=True,
            prefer_last=(meta["year"] >= 2012),
            skip_toc=True,
        )
        chunks["aktie_basisdaten"] = find_window(
            lines,
            [r"Dividende\s*\(in CHF\)\s*je Namenaktie|Dividendeje Namenaktie|Dividende je Namenaktie|Dividende par action|Dividendper registered share|Basisdaten der BEKB-Aktie"],
            before=22,
            after=42,
            require_pipe=True,
            prefer_last=True,
        )
        chunks["betreute_vermoegen"] = find_window(
            lines,
            [r"Netto-Neugeld-Zufluss|Netto-Neugeld\|"],
            before=8,
            after=25,
            require_pipe=True,
            prefer_last=False,
        )
        chunks["lagebericht_strategie"] = extract_lagebericht_excerpt(lines)

    elif meta["report_type"] == "semester":
        chunks["bilanz"] = find_all_matching_windows(
            lines,
            [
                r"\|Hypothekarforderungen\|",
                r"\|Verpflichtungen aus Kundeneinlagen\||\|Verpflichtungen gegenüber Kunden\||\|Total Passiven\||\|TOTAL PASSIVEN\|",
            ],
            before=16,
            after=40,
            require_pipe=True,
            max_windows=2,
        )
        chunks["erfolgsrechnung"] = find_window(
            lines,
            [
                r"\|Zins- und Diskontertrag\||Erfolg aus dem Zinsengeschäft",
                r"\|Subtotal Erfolg Zinsengeschäft\||\|Subtotal Netto-Erfolg Zinsengeschäft\||\|Netto-Zinserfolg\|",
            ],
            before=12,
            after=80,
            require_pipe=True,
            prefer_last=False,
        )
        chunks["lagebericht_strategie"] = extract_lagebericht_excerpt(lines, max_chars=5500)

    else:  # offenlegung_fy or offenlegung_h1
        chunks["km1_eigenmittel"] = find_all_matching_windows(
            lines,
            [
                r"Hartes Kernkapital.*CET1|CET1-Quote|CET1­Quote",
                r"Gesamtkapitalquote|Leverage Ratio\(Rz|22\s*(?:<br>|\|)?\s*Leverage Ratio",
                r"Quote für kurzfristige Liquidität.*LCR|17\s*(?:<br>|\|)\s*LCR|17\s*(?:<br>|\|)\s*Liquiditätsquote",
            ],
            before=14,
            after=55,
            require_pipe=True,
            max_windows=4,
            skip_toc=True,
        )
        chunks["ov1_rwa"] = find_window(
            lines,
            [r"\|Total\s*\(.*RWA|Total risikogewichtete|^\|\|RWA<br>|^\|.*\|RWA\|"],
            before=10,
            after=45,
            require_pipe=True,
            prefer_last=False,
            skip_toc=True,
        )

    return {
        "meta": {**meta, "source_file": str(md_path), "total_chars": len(text), "total_lines": len(lines)},
        "chunks": {k: v for k, v in chunks.items() if v},
    }


def main():
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    md_files = sorted(MD_DIR.glob("*.md"))
    manifest = {"total_reports": len(md_files), "reports": []}

    for md_path in md_files:
        payload = chunk_report(md_path)
        out_path = CHUNKS_DIR / f"{md_path.stem}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        chunk_stats = {
            name: {"chars": len(content), "approx_tokens": max(1, len(content) // 4)}
            for name, content in payload["chunks"].items()
        }
        manifest["reports"].append({
            "stem": md_path.stem,
            "report_type": payload["meta"]["report_type"],
            "year": payload["meta"]["year"],
            "period": payload["meta"]["period"],
            "chunks": chunk_stats,
        })

    manifest_path = CHUNKS_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    max_tok = max(
        c["approx_tokens"]
        for r in manifest["reports"]
        for c in r["chunks"].values()
    )
    print(f"[OK] {len(md_files)} Berichte in {CHUNKS_DIR}/ gechunkt (max Chunk ~{max_tok} Tokens).")


if __name__ == "__main__":
    main()
