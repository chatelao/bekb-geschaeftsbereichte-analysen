#!/usr/bin/env python3
"""
Stufe 2 der Hydrogen-Analysestrategie: Atomare Extraktion (Map-Phase).

Liest die vorbereiteten Chunks aus data/chunks/*.json und erzeugt für jeden der
57 Berichte ein einheitliches JSON-Dokument unter data/extracted/<stem>.json.

Unterstützt zwei Backends:
  --backend gemini : Verwendet ein Gemini-Hydrogen-Modell (z. B. gemini-2.5-flash-lite)
                     über die Gemini REST API (benötigt GEMINI_API_KEY).
  --backend local  : Deterministischer Tabellen- & Sektions-Parser mit identischem
                     Ausgabeschema und Belegzitaten (source_quote).
  --backend auto   : Wählt automatisch 'gemini', falls GEMINI_API_KEY gesetzt ist,
                     andernfalls 'local'.
"""

import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

CHUNKS_DIR = Path("data/chunks")
EXTRACTED_DIR = Path("data/extracted")
DEFAULT_HYDROGEN_MODEL = "gemini-2.5-flash-lite"

HYDROGEN_SYSTEM_PROMPT = """Du bist ein präziser Finanzdaten-Extraktor. Du erhältst einen kurzen Textausschnitt aus einem BEKB-Bericht.
Regeln:
1. Extrahiere NUR Zahlen, die explizit im Text oder in der Tabelle stehen.
2. Rechne NICHT um und berechne KEINE Summen oder Quoten.
3. Übernimm Tausendertrennzeichen nicht in das Zahlenfeld (z. B. "41 893" -> 41893, "175,6" -> 175.6, "(280 848)" -> -280848).
4. Wenn ein Wert im Ausschnitt nicht vorkommt, setze "value_current": null.
5. Gib AUSSCHLIESSLICH valides JSON gemäss Schema zurück."""


def clean_cell(cell: str) -> str:
    txt = cell.replace("\xad", "")  # Soft-Hyphen entfernen
    txt = re.sub(r"<sup>.*?</sup>", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"^(?:[il]\s*<br\s*/?>\s*)+", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"(?:\s*<br\s*/?>\s*(?:[il]|\d)\s*)+$", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"<br\s*/?>", " ", txt, flags=re.IGNORECASE)
    txt = re.sub(r"[*_`]", "", txt)
    return re.sub(r"\s+", " ", txt).strip()


def parse_swiss_number(raw: str) -> float | None:
    if raw is None:
        return None
    s = raw.replace("\xad", "")
    s = re.sub(r"<sup>.*?</sup>", "", s, flags=re.IGNORECASE)
    # Entferne trailing footnote z.B. "100,7<br>2" oder "2 981<br>1"
    s = re.sub(r"<br\s*/?>\s*\d+\s*$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.IGNORECASE)
    s = s.replace("*", "").replace("'", "").replace("’", "").replace("`", "").strip()
    if not s or s in {"-", "–", "—", "n.a.", "n.a"}:
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    if s.startswith(("–", "—", "-")):
        neg = True
        s = s[1:].strip()
    s = s.rstrip("%").strip()
    m = re.match(r"^(\d[\d\s]*)(?:[.,](\d+))?$", s)
    if not m:
        # Fallback für "10.80 1" o.ä. ohne <br>
        m = re.match(r"^(\d[\d\s]*)(?:[.,](\d+))?", s)
        if not m:
            return None
    int_part = re.sub(r"\s+", "", m.group(1))
    dec_part = m.group(2)
    val = float(f"{int_part}.{dec_part}" if dec_part else int_part)
    return -val if neg else val


def split_md_row(line: str) -> list[str]:
    """Teilt eine Markdown-Tabellenzeile exakt an den Spaltengrenzen, ohne führende leere Zellen zu verlieren."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_year_header_cell(cell_text: str) -> bool:
    """Prüft, ob eine Zelle ein Spaltenkopf mit Jahr oder Stichtag ist."""
    c = clean_cell(cell_text)
    if not c:
        return False
    if re.fullmatch(
        r"(?:[a-f]\s+)?(?:1\.1\.[\-–]\s*)?(?:\d{1,2}\.(?:\d{1,2}\.|\s*[A-Za-zäöü]+\s*))?(?:19|20)\d{2}(?:\s+(?:in|en)\s+CHF)?",
        c,
        re.IGNORECASE,
    ):
        return True
    return bool(re.search(r"(?:30\.0?6\.|31\.12\.|1\.1\.[\-–]|30\.\s*Juni|31\.\s*Dezember)\s*(?:19|20)\d{2}", c, re.I))


def parse_markdown_tables(chunk_text: str) -> list[dict]:
    """Parst Markdown-Tabellen in strukturierte Objekte mit Kontext-Einheit und Spaltenjahren."""
    tables = []
    lines = chunk_text.splitlines()
    i = 0
    recent_unit = None
    recent_year_headers = None

    while i < len(lines):
        line = lines[i].strip()
        if re.search(r"\bin\s+(?:CHF\s*1\s*000|TCHF)\b", line, re.IGNORECASE):
            recent_unit = "TCHF"
        elif re.search(r"\b(?:in|Beträge in)\s+(?:Mio\.|Millionen)\s*(?:CHF|Franken)?\b", line, re.IGNORECASE):
            recent_unit = "Mio. CHF"
        elif re.search(r"^(?:in\s+)?CHF\s*$", line, re.IGNORECASE):
            recent_unit = "CHF"

        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|", lines[i + 1].strip()):
            header_cells = [clean_cell(c) for c in split_md_row(line)]
            unit = recent_unit
            for hc in header_cells:
                if re.search(r"in\s+CHF\s*1\s*000", hc, re.I):
                    unit = "TCHF"
                elif re.search(r"in\s+Mio\.\s*CHF|in\s+Millionen", hc, re.I):
                    unit = "Mio. CHF"
                elif re.search(r"\bin\s+CHF\b|^CHF$", hc, re.I):
                    unit = "CHF"

            has_yr_hdr = any(is_year_header_cell(hc) for hc in header_cells)
            if has_yr_hdr:
                recent_year_headers = header_cells
            elif recent_year_headers and len(header_cells) == len(recent_year_headers):
                c0_hdr = header_cells[0].lower()
                if any(k in c0_hdr for k in ("payments to the public sector", "in millionen franken", "leistungen an die öffentliche")):
                    header_cells = list(recent_year_headers)

            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                raw_cells = split_md_row(lines[j])
                rows.append((lines[j].strip(), raw_cells))
                j += 1
            tables.append({"headers": header_cells, "unit": unit, "rows": rows})
            i = j
            continue
        elif re.match(r"^\|[\s:|-]+\|$", line) and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            # Tabellenfragment ohne Kopfzeile (am Anfang eines Chunks)
            rows = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                raw_cells = split_md_row(lines[j])
                rows.append((lines[j].strip(), raw_cells))
                j += 1
            tables.append({"headers": [], "unit": recent_unit, "rows": rows})
            i = j
            continue
        i += 1
    return tables


def detect_year_columns(headers: list[str], target_year: int, report_type: str) -> tuple[int | None, int | None, bool]:
    """Bestimmt die Spaltenindizes für aktuelles Jahr (t) und Vorjahr (t-1)."""
    year_cols = {}
    has_pct_or_abs = any(re.search(r"absolut|in\s*%|Veränder", h, re.I) for h in headers)

    for idx, h in enumerate(headers):
        hc = clean_cell(h)
        m_num = re.findall(r"(?:(\d{1,2})\.(\d{1,2})\.)?(20\d{2}|19\d{2})", hc)
        m_word = re.findall(r"(30\.\s*Juni|31\.\s*Dezember|1\.\s*Halbjahr|1\.\s*Semester)\s*(20\d{2}|19\d{2})", hc, re.I)
        if m_word:
            period_word, yr_str = m_word[-1]
            yr = int(yr_str)
            is_h1 = bool(re.search(r"Juni|Halbjahr|Semester", period_word, re.I))
            year_cols.setdefault((yr, is_h1), idx)
        elif m_num:
            day, month, yr_str = m_num[-1]
            yr = int(yr_str)
            is_h1 = month in {"6", "06"}
            year_cols.setdefault((yr, is_h1), idx)

    if report_type in {"semester", "offenlegung_h1"}:
        cur = year_cols.get((target_year, True))
        if cur is None:
            cur = year_cols.get((target_year, False))
        prev = year_cols.get((target_year - 1, True))
        if prev is None:
            prev = year_cols.get((target_year - 1, False))
        return cur, prev, has_pct_or_abs

    cur = year_cols.get((target_year, False))
    if cur is None:
        cur = year_cols.get((target_year, True))
    prev = year_cols.get((target_year - 1, False))
    if prev is None:
        prev = year_cols.get((target_year - 1, True))
    return cur, prev, has_pct_or_abs


def match_row_value(tables: list[dict], row_patterns: list[str], target_year: int, report_type: str,
                    default_unit: str, prefer_unit: str | None = None,
                    exclude_patterns: list[str] | None = None,
                    allow_side_by_side: bool = False,
                    allow_row_num_col: bool = False,
                    fixed_unit: str | None = None,
                    exclude_units: list[str] | None = None) -> dict | None:
    """Sucht eine Kennzahl in geparsten Tabellen inkl. Spaltenzuordnung und Belegzitat."""
    candidates = []
    for tbl in tables:
        cur_headers = list(tbl["headers"])
        cur_col, prev_col, has_pct_or_abs = detect_year_columns(cur_headers, target_year, report_type)
        has_any_year_hdr = any(is_year_header_cell(h) for h in cur_headers)
        current_unit = tbl["unit"]
        for raw_line, raw_cells in tbl["rows"]:
            if not raw_cells:
                continue

            c0 = clean_cell(raw_cells[0])
            # Falls Zeile einen Inline-Einheitenhinweis enthält
            if re.search(r"^in\s+CHF\s*1\s*000$", c0, re.I):
                current_unit = "TCHF"
                if any(is_year_header_cell(c) for c in raw_cells[1:]):
                    cur_headers = [clean_cell(c) for c in raw_cells]
                    cur_col, prev_col, has_pct_or_abs = detect_year_columns(cur_headers, target_year, report_type)
                    has_any_year_hdr = True
                continue
            if re.search(r"^in\s+Mio\.?\s*CHF$", c0, re.I):
                current_unit = "Mio. CHF"
                if any(is_year_header_cell(c) for c in raw_cells[1:]):
                    cur_headers = [clean_cell(c) for c in raw_cells]
                    cur_col, prev_col, has_pct_or_abs = detect_year_columns(cur_headers, target_year, report_type)
                    has_any_year_hdr = True
                continue

            # Falls Zeile ein Jahres-/Stichtags-Subheader ist (z.B. ||**2025**|**2024**| oder |**AKTIVEN**|**30.6.2020**|**31.12.2019**|)
            cleaned_row = [clean_cell(c) for c in raw_cells]
            yr_hdr_hits = sum(1 for c in cleaned_row[1:] if is_year_header_cell(c))
            is_known_hdr_c0 = bool(re.fullmatch(
                r"(?:|AKTIVEN|PASSIVEN|ERFOLGSRECHNUNG|BILANZ|Ausschüttung|Kursentwicklung.*|Kennzahlen.*|ACTIF|PASSIF)",
                c0, re.I
            ))
            if (yr_hdr_hits >= 1 and is_known_hdr_c0) or yr_hdr_hits >= 2:
                cur_headers = cleaned_row
                cur_col, prev_col, has_pct_or_abs = detect_year_columns(cur_headers, target_year, report_type)
                has_any_year_hdr = True
                continue
            if not c0 and any(re.search(r"absolut|in\s*%", c, re.I) for c in cleaned_row[1:]):
                has_pct_or_abs = True
                continue

            # Label-Spalten bestimmen (bei KM1/CC1 steht teils Zeilennummer in Spalte 0 und Text in Spalte 1)
            label_offset = 0
            lbl_text = c0
            if allow_row_num_col and len(raw_cells) >= 3 and re.fullmatch(r"\d+[a-z]?", c0, re.I):
                c1 = clean_cell(raw_cells[1])
                if c1:
                    lbl_text = f"{c0} {c1}".strip()
                    label_offset = 1

            check_pairs = [(label_offset, lbl_text, cur_col, prev_col)]
            if allow_side_by_side and len(raw_cells) >= 6:
                lbl2 = clean_cell(raw_cells[3])
                cl, pl, _ = detect_year_columns(cur_headers[:3], target_year, report_type)
                cr, pr, _ = detect_year_columns(cur_headers[3:], target_year, report_type)
                c_left = cl if cl in {1, 2} else 2
                p_left = pl if pl in {1, 2} else 1
                c_right = (cr + 3) if cr in {1, 2} else 5
                p_right = (pr + 3) if pr in {1, 2} else 4
                check_pairs = [
                    (0, c0, c_left, p_left),
                    (3, lbl2, c_right, p_right),
                ]

            for lbl_idx, text_to_match, c_idx, p_idx in check_pairs:
                if not text_to_match:
                    continue
                if exclude_patterns and any(re.search(ex, text_to_match, re.I) for ex in exclude_patterns):
                    continue
                if not any(re.search(pat, text_to_match, re.I) for pat in row_patterns):
                    continue

                unit = fixed_unit or current_unit or default_unit
                if exclude_units and unit in exclude_units:
                    continue
                if exclude_units and (current_unit in exclude_units):
                    continue

                val_cur = None
                val_prev = None
                if c_idx is not None:
                    # Niemals aus der Label- oder Zeilennummernspalte (<= lbl_idx) lesen!
                    if c_idx <= lbl_idx:
                        continue
                    if c_idx < len(raw_cells):
                        val_cur = parse_swiss_number(raw_cells[c_idx])
                    if p_idx is not None and p_idx > lbl_idx and p_idx < len(raw_cells):
                        val_prev = parse_swiss_number(raw_cells[p_idx])
                elif not has_pct_or_abs and not has_any_year_hdr:
                    # Nur bei reinen Key-Value-Tabellen ohne Jahresspalten UND ohne %-Spalten
                    nums = [parse_swiss_number(c) for c in raw_cells[lbl_idx + 1:]]
                    nums = [n for n in nums if n is not None]
                    if len(nums) == 1:
                        val_cur = nums[0]

                if val_cur is None:
                    continue

                score = 2 if (prefer_unit and unit == prefer_unit) else 1
                candidates.append((score, {
                    "value_current": val_cur,
                    "value_prior_year": val_prev,
                    "unit": unit,
                    "source_quote": raw_line[:220],
                }))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def extract_annual_local(payload: dict) -> dict:
    meta = payload["meta"]
    chunks = payload["chunks"]
    y = meta["year"]
    rt = meta["report_type"]
    side = y in {2004, 2005, 2006, 2007}

    t_bil = parse_markdown_tables(chunks.get("bilanz", ""))
    t_er = parse_markdown_tables(chunks.get("erfolgsrechnung", ""))
    t_mj = parse_markdown_tables(chunks.get("mehrjahresvergleich", ""))
    t_ak = parse_markdown_tables(chunks.get("aktie_basisdaten", ""))
    t_au = parse_markdown_tables(chunks.get("betreute_vermoegen", ""))

    all_fin = t_bil + t_mj
    metrics = {}

    metrics["total_assets"] = match_row_value(
        all_fin, [r"^Total\s*Aktiven$", r"^TOTAL\s*AKTIVEN$", r"^Total des actifs$", r"^Total de l’actif$", r"^Bilanzsumme$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side
    )
    metrics["mortgage_loans"] = match_row_value(
        all_fin, [r"^Hypothekarforderungen$", r"^Créances hypothécaires$", r"davon Hypothekarforderungen"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side
    )
    metrics["customer_loans_other"] = match_row_value(
        t_bil, [r"^Forderungen\s*gegenüber\s*Kunden$", r"^Créances sur la clientèle$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side
    )

    dep_single = match_row_value(
        t_bil,
        [r"^Verpflichtungen aus Kundeneinlagen$", r"^Verpflichtungen\s*gegenüber\s*Kunden$", r"^Engagements envers la clientèle$"],
        y, rt, "TCHF", prefer_unit="TCHF", exclude_patterns=[r"Spar"], allow_side_by_side=side
    )
    if dep_single is None:
        dep_spar = match_row_value(
            t_bil,
            [r"^Verpflichtungen\s*gegenüber\s*Kunden\s*in\s*Spar", r"^in\s+Spar-?\s*und\s+Anlageform$", r"^Engagements envers la clientèle sous forme d’épargne", r"^et de placements$"],
            y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side
        )
        dep_oth = match_row_value(
            t_bil,
            [r"^Übrige\s*Verpflichtungen\s*gegenüber\s*Kunden$", r"^Autres engagements envers la clientèle$"],
            y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side
        )
        if dep_spar and dep_oth:
            vp = (
                (dep_spar["value_prior_year"] + dep_oth["value_prior_year"])
                if (dep_spar["value_prior_year"] is not None and dep_oth["value_prior_year"] is not None)
                else None
            )
            dep_single = {
                "value_current": dep_spar["value_current"] + dep_oth["value_current"],
                "value_prior_year": vp,
                "unit": dep_spar["unit"],
                "source_quote": f"{dep_spar['source_quote']} + {dep_oth['source_quote']}"[:220],
            }
    if dep_single is None:
        dep_single = match_row_value(t_mj, [r"^Kundengelder im engeren Sinn?"], y, rt, "Mio. CHF", fixed_unit="Mio. CHF")
    metrics["customer_deposits"] = dep_single

    metrics["kassenobligationen"] = match_row_value(
        all_fin, [r"^Kassenobligationen$", r"^Obligations de caisse$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side
    )
    metrics["reserves_banking_risks"] = match_row_value(
        all_fin, [r"^Reserven für allgemeine Bankrisiken$", r"^Réserves pour risques bancaires généraux$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side
    )
    metrics["shareholders_equity"] = match_row_value(
        t_bil, [r"^Total\s*Eigenkapital$", r"^Eigenkapital$", r"^Total des capitaux propres$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side
    ) or match_row_value(
        t_mj, [r"^Eigenkapital$", r"^Fonds propres$"], y, rt, "Mio. CHF", fixed_unit="Mio. CHF"
    )

    metrics["net_interest_income"] = match_row_value(
        t_er,
        [
            r"^Subtotal\s*Netto-?Erfolg\s*Zinsen-?\s*geschäft$",
            r"^Netto-?Erfolg\s*aus\s*dem\s*Zinsen-?\s*geschäft$",
            r"^Netto-?Zinserfolg$",
            r"^Subtotal\s*Erfolg\s*Zinsen-?\s*geschäft$",
            r"^Sous-total résultant des opérations d’intérêts$",
        ],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["commission_income"] = match_row_value(
        t_er,
        [
            r"^Erfolg\s*aus\s*dem\s*Kommissions-?\s*und\s*Dienstleistungs-?\s*geschäft$",
            r"^Subtotal\s*Erfolg\s*Kommissions-?\s*und\s*Dienstleistungs-?\s*geschäft$",
            r"^Sous-total résultant des opérations de commissions",
        ],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["trading_income"] = match_row_value(
        t_er, [r"^Erfolg\s*aus\s*dem\s*Handelsgeschäft(?:\s+und\s+der\s+Fair-Value-Option)?$", r"^Résultat des opérations de négoce$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["total_operating_income"] = match_row_value(
        t_er, [r"^Geschäftsertrag$", r"^Betriebsertrag\s*netto$", r"^Produit d’exploitation net$"],
        y, rt, "TCHF", prefer_unit="TCHF", exclude_patterns=[r"vor Erfolg aus Veräusserungen|avant résultat des aliénations"], allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["personnel_expenses"] = match_row_value(
        t_er, [r"^Personalaufwand$", r"^Charges de personnel$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["general_expenses"] = match_row_value(
        t_er, [r"^Sachaufwand$", r"^Autres charges d’exploitation$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["total_operating_expenses"] = match_row_value(
        t_er, [r"^Subtotal\s*Geschäftsaufwand$", r"^Geschäftsaufwand$", r"^Sous-total charges d’exploitation$", r"^Total des charges d’exploitation$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["operating_profit"] = match_row_value(
        t_er, [r"^Geschäftserfolg$", r"^Bruttogewinn$", r"^Bénéfice brut$"],
        y, rt, "TCHF", prefer_unit="TCHF", exclude_patterns=[r"vor Erfolg|avant résultat"], allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["reserves_change"] = match_row_value(
        t_er, [r"^Veränderungen von Reserven für allgemeine Bankrisiken$", r"^Zuweisung an Reserven für allgemeine Bankrisiken$"],
        y, rt, "TCHF", prefer_unit="TCHF", allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["taxes"] = match_row_value(
        t_er, [r"^Steuern$", r"^Impôts$"],
        y, rt, "TCHF", prefer_unit="TCHF", exclude_patterns=[r"Veräusserung"], allow_side_by_side=side, exclude_units=["CHF"]
    )
    metrics["net_profit"] = match_row_value(
        t_er, [r"^Gewinn$", r"^Jahresgewinn$", r"^Bénéfice annuel$", r"^Bénéfice de l’exercice$"],
        y, rt, "TCHF", prefer_unit="TCHF", exclude_patterns=[r"vor Steuern|avant impôts|avant impots|exkl\.|Veräusserung|vortrag|reporté"], allow_side_by_side=side, exclude_units=["CHF"]
    ) or match_row_value(
        t_mj, [r"^Gewinn$", r"^Jahresgewinn nach Steuern$", r"^Profit for the year after taxes", r"^Bénéfice annuel après impôts$"],
        y, rt, "Mio. CHF", fixed_unit="Mio. CHF"
    )

    metrics["assets_under_management"] = match_row_value(
        t_mj + t_au,
        [r"^Betreute Vermögenswerte", r"^Valeurs patrimoniales sous gestion", r"^Assets under management\b"],
        y, rt, "Mio. CHF", prefer_unit="Mio. CHF",
        exclude_patterns=[r"mit umfassenden|ohne umfassende|eigenverwalteten|Netto-Neugeld"]
    )
    metrics["net_new_money"] = match_row_value(
        t_au, [r"Netto-Neugeld-Zufluss.*betreute", r"davon betreute Vermögenswerte"], y, rt, "TCHF", prefer_unit="TCHF"
    )
    metrics["free_cash_flow"] = match_row_value(
        t_mj, [r"^Free-Cash-Flow", r"^Free cash flow", r"^Netto erarbeitete Mittel"], y, rt, "Mio. CHF", fixed_unit="Mio. CHF"
    )
    metrics["share_price_eoy"] = match_row_value(
        t_ak + t_mj, [r"^Jahresend$", r"^Jahresendkurs Namenaktie", r"^Cours en fin d'année$", r"^Cours en fin d’année$", r"^Year-end price\b"],
        y, rt, "CHF", fixed_unit="CHF"
    )
    metrics["dividend_per_share"] = match_row_value(
        t_ak + t_mj,
        [
            r"^Dividende.*Namenaktie",
            r"^Dividende\s*\(in CHF\)\s*je Namenaktie",
            r"^Dividendeje Namenaktie",
            r"^Dividende par action",
            r"^Dividendper registered share",
        ],
        y, rt, "CHF", exclude_patterns=[r"Sonderdividende|199\d"], fixed_unit="CHF"
    )
    metrics["payout_ratio_pct"] = match_row_value(
        t_ak, [r"^Ausschüttungsquote$"], y, rt, "%", fixed_unit="%"
    )
    metrics["fte_count"] = match_row_value(
        t_mj + t_ak,
        [
            r"^Mitarbeitende\s*\(teilzeitbereinigt\)",
            r"^Mitarbeiterinnen und Mitarbeiter.*teilzeitbereinigt",
            r"^Anzahl Stellen teilzeitbereinigt",
            r"^Collaboratrices et collaborateurs",
        ],
        y, rt, "FTE", fixed_unit="FTE"
    )
    metrics["headcount"] = match_row_value(
        t_mj + t_ak, [r"^Personalbestand", r"^Effectif du personnel$"], y, rt, "Personen", fixed_unit="Personen"
    )
    metrics["branch_count"] = match_row_value(
        t_mj + t_ak, [r"^Anzahl Standorte$", r"^Anzahl Niederlassungen$", r"^Nombre de sièges$"], y, rt, "Anzahl", fixed_unit="Anzahl"
    )
    metrics["taxes_public_mio"] = match_row_value(
        t_mj + t_ak,
        [r"^Bundes-,?\s*Staats- und Gemeindesteuern$", r"^Impôts fédéraux, cantonaux et communaux$", r"^Federal, State and local community taxes$"],
        y, rt, "Mio. CHF", fixed_unit="Mio. CHF"
    )
    metrics["dividend_canton_mio"] = match_row_value(
        t_mj + t_ak,
        [r"^Dividende an den Kanton$", r"^Ertrag\s*auf Investition des Kantons", r"^Produit sur investissement du canton", r"^Revenue on canton[’']s investment"],
        y, rt, "Mio. CHF", fixed_unit="Mio. CHF"
    )
    metrics["canton_guarantee_fee_mio"] = match_row_value(
        t_mj + t_ak,
        [r"^Abgeltung\s*Staatsgarantie", r"^Rémunération de la garantie de l'Etat", r"^Compensation to the canton for the State guarantee$"],
        y, rt, "Mio. CHF", fixed_unit="Mio. CHF"
    )

    excerpt_lines = [
        l.strip() for l in chunks.get("lagebericht_strategie", "").splitlines()
        if l.strip() and not l.strip().startswith("#") and len(l.strip()) > 60
    ]
    return {
        "report_file": meta["source_file"],
        "stem": meta["stem"],
        "report_type": rt,
        "year": y,
        "period": meta["period"],
        "extraction_backend": "local_deterministic",
        "metrics": metrics,
        "strategy_highlights": excerpt_lines[:6],
    }


def extract_semester_local(payload: dict) -> dict:
    meta = payload["meta"]
    chunks = payload["chunks"]
    y = meta["year"]
    rt = meta["report_type"]
    side_sem = y == 2018

    t_bil = parse_markdown_tables(chunks.get("bilanz", ""))
    t_er = parse_markdown_tables(chunks.get("erfolgsrechnung", ""))

    dep_sem = match_row_value(
        t_bil, [r"^Verpflichtungen aus Kundeneinlagen$", r"^Verpflichtungen\s*gegenüber\s*Kunden$"],
        y, rt, "TCHF", exclude_patterns=[r"Spar"], allow_side_by_side=side_sem, fixed_unit="TCHF"
    )
    if dep_sem is None:
        dep_spar = match_row_value(
            t_bil, [r"^Verpflichtungen\s*gegenüber\s*Kunden\s*in\s*Spar"], y, rt, "TCHF", allow_side_by_side=side_sem, fixed_unit="TCHF"
        )
        dep_oth = match_row_value(
            t_bil, [r"^Übrige\s*Verpflichtungen\s*gegenüber\s*Kunden$"], y, rt, "TCHF", allow_side_by_side=side_sem, fixed_unit="TCHF"
        )
        if dep_spar and dep_oth:
            vp = (
                (dep_spar["value_prior_year"] + dep_oth["value_prior_year"])
                if (dep_spar["value_prior_year"] is not None and dep_oth["value_prior_year"] is not None)
                else None
            )
            dep_sem = {
                "value_current": dep_spar["value_current"] + dep_oth["value_current"],
                "value_prior_year": vp,
                "unit": "TCHF",
                "source_quote": f"{dep_spar['source_quote']} + {dep_oth['source_quote']}"[:220],
            }

    metrics = {
        "total_assets": match_row_value(t_bil, [r"^Total\s*Aktiven$", r"^TOTAL\s*AKTIVEN$"], y, rt, "TCHF", allow_side_by_side=side_sem, fixed_unit="TCHF"),
        "mortgage_loans": match_row_value(t_bil, [r"^Hypothekarforderungen$"], y, rt, "TCHF", allow_side_by_side=side_sem, fixed_unit="TCHF"),
        "customer_loans_other": match_row_value(t_bil, [r"^Forderungen\s*gegenüber\s*Kunden$"], y, rt, "TCHF", allow_side_by_side=side_sem, fixed_unit="TCHF"),
        "customer_deposits": dep_sem,
        "reserves_banking_risks": match_row_value(t_bil, [r"^Reserven für allgemeine Bankrisiken$"], y, rt, "TCHF", allow_side_by_side=side_sem, fixed_unit="TCHF"),
        "net_interest_income": match_row_value(
            t_er,
            [
                r"^Subtotal\s*Netto-?Erfolg\s*Zinsen-?\s*geschäft$",
                r"^Netto-?Erfolg\s*aus\s*dem\s*Zinsen-?\s*geschäft$",
                r"^Netto-?Zinserfolg$",
                r"^Subtotal\s*Erfolg\s*Zinsen-?\s*geschäft$",
            ],
            y, rt, "TCHF", fixed_unit="TCHF"
        ),
        "commission_income": match_row_value(
            t_er, [r"^Erfolg\s*aus\s*dem\s*Kommissions-?\s*und\s*Dienstleistungs-?\s*geschäft$", r"^Subtotal\s*Erfolg\s*Kommissions-"], y, rt, "TCHF", fixed_unit="TCHF"
        ),
        "trading_income": match_row_value(
            t_er, [r"^Erfolg\s*aus\s*dem\s*Handelsgeschäft(?:\s+und\s+der\s+Fair-Value-Option)?$"], y, rt, "TCHF", fixed_unit="TCHF"
        ),
        "total_operating_income": match_row_value(
            t_er, [r"^Geschäftsertrag$", r"^Betriebsertrag\s*netto$"], y, rt, "TCHF", exclude_patterns=[r"vor Erfolg"], fixed_unit="TCHF"
        ),
        "total_operating_expenses": match_row_value(
            t_er, [r"^Subtotal\s*Geschäftsaufwand$", r"^Geschäftsaufwand$"], y, rt, "TCHF", fixed_unit="TCHF"
        ),
        "operating_profit": match_row_value(
            t_er, [r"^Geschäftserfolg$", r"^Bruttogewinn$"], y, rt, "TCHF", exclude_patterns=[r"vor Erfolg"], fixed_unit="TCHF"
        ),
        "reserves_change": match_row_value(
            t_er, [r"^Veränderungen von Reserven für allgemeine Bankrisiken$"], y, rt, "TCHF", fixed_unit="TCHF"
        ),
        "taxes": match_row_value(t_er, [r"^Steuern$"], y, rt, "TCHF", fixed_unit="TCHF"),
        "net_profit": match_row_value(
            t_er, [r"^Halbjahresgewinn$", r"^Zwischengewinn$", r"^Gewinn$"],
            y, rt, "TCHF", exclude_patterns=[r"vor Steuern"], fixed_unit="TCHF"
        ),
    }

    excerpt_lines = [
        l.strip() for l in chunks.get("lagebericht_strategie", "").splitlines()
        if l.strip() and not l.strip().startswith("#") and len(l.strip()) > 60
    ]
    return {
        "report_file": meta["source_file"],
        "stem": meta["stem"],
        "report_type": rt,
        "year": y,
        "period": meta["period"],
        "extraction_backend": "local_deterministic",
        "metrics": metrics,
        "strategy_highlights": excerpt_lines[:4],
    }


def extract_offenlegung_local(payload: dict) -> dict:
    meta = payload["meta"]
    chunks = payload["chunks"]
    y = meta["year"]
    rt = meta["report_type"]

    t_km1 = parse_markdown_tables(chunks.get("km1_eigenmittel", ""))
    t_ov1 = parse_markdown_tables(chunks.get("ov1_rwa", ""))
    all_t = t_km1 + t_ov1

    metrics = {
        "cet1_capital": match_row_value(
            t_km1, [r"^1\s+Hartes Kernkapital", r"Hartes Kernkapital\s*\(net CET1\)", r"^29\s+=?\s*hartes Kernkapital"],
            y, rt, "TCHF", exclude_patterns=[r"Quote|Puffer|Anforderung|Zielquote"], allow_row_num_col=True, fixed_unit="TCHF"
        ),
        "total_capital": match_row_value(
            t_km1, [r"^3\s+Gesamtkapital total", r"Gesamtkapital\s*\(net total capital\)", r"Anrechenbare Gesamteigenmittel", r"^59\s+=?\s*(?:Gesamtkapital|regulatorisches Kapital)"],
            y, rt, "TCHF", allow_row_num_col=True, fixed_unit="TCHF"
        ),
        "rwa_total": match_row_value(
            all_t, [r"^4\s+RWA$", r"Total risikogewichtete Positionen", r"^60\s+Summe der risikogewichteten Positionen", r"Total\s*\(.*RWA.*\)"],
            y, rt, "TCHF", exclude_patterns=[r"Mindesteigenmittel|Quote|Puffer"], allow_row_num_col=True, fixed_unit="TCHF"
        ),
        "cet1_ratio_pct": match_row_value(
            t_km1, [r"^5\s+CET1-?Quote", r"^61\s+CET1-?Quote"],
            y, rt, "%", allow_row_num_col=True, fixed_unit="%"
        ),
        "total_capital_ratio_pct": match_row_value(
            t_km1, [r"^7\s+Gesamtkapitalquote", r"^63\s+(?:Gesamtkapitalquote|Quote bzgl\. des regulatorischen Kapitals)"],
            y, rt, "%", allow_row_num_col=True, fixed_unit="%"
        ),
        "leverage_ratio_pct": match_row_value(
            t_km1, [r"^14\s+Levera[gt]e Ratio", r"^14\s+Basel III Leverage Ratio", r"^22\s+Leverage Ratio"],
            y, rt, "%", exclude_patterns=[r"^14[a-e]\b", r"ohne Auswirkung", r"Mindesteigenmittel", r"Gesamtengagement\s*\("], allow_row_num_col=True, fixed_unit="%"
        ),
        "lcr_pct": match_row_value(
            t_km1, [r"^17\s+LCR", r"^17\s+Liquiditätsquote", r"^23\s*Quote für kurzfristige Liquidität"],
            y, rt, "%", allow_row_num_col=True, fixed_unit="%"
        ),
        "nsfr_pct": match_row_value(
            t_km1, [r"^20\s+(?:Finanzierungsquote,?\s*)?NSFR", r"NSFR\s*\(%\)"],
            y, rt, "%", allow_row_num_col=True, fixed_unit="%"
        ),
    }

    return {
        "report_file": meta["source_file"],
        "stem": meta["stem"],
        "report_type": rt,
        "year": y,
        "period": meta["period"],
        "extraction_backend": "local_deterministic",
        "metrics": metrics,
        "strategy_highlights": [],
    }


def call_gemini_hydrogen(chunk_name: str, chunk_text: str, meta: dict, api_key: str, model: str) -> dict:
    """Ruft Gemini Hydrogen via REST API im strikten JSON-Modus auf (Map-Phase)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    user_prompt = (
        f"Bericht: {meta['stem']} (Typ: {meta['report_type']}, Jahr: {meta['year']}, Periode: {meta['period']})\n"
        f"Chunk: {chunk_name}\n"
        f"Textausschnitt:\n---\n{chunk_text}\n---\n"
        "Gib ein JSON-Objekt mit dem Feld 'metrics' zurück. Jeder Eintrag unter 'metrics' hat "
        "{'value_current': number|null, 'value_prior_year': number|null, 'unit': string, 'source_quote': string}."
    )
    body = {
        "systemInstruction": {"parts": [{"text": HYDROGEN_SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    raw_text = res["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw_text)


def extract_with_gemini(payload: dict, api_key: str, model: str) -> dict:
    meta = payload["meta"]
    merged_metrics = {}
    for chunk_name, chunk_text in payload["chunks"].items():
        if chunk_name == "lagebericht_strategie":
            continue
        parsed = call_gemini_hydrogen(chunk_name, chunk_text, meta, api_key, model)
        for k, v in parsed.get("metrics", {}).items():
            if v and v.get("value_current") is not None and k not in merged_metrics:
                merged_metrics[k] = v

    excerpt_lines = [
        l.strip() for l in payload["chunks"].get("lagebericht_strategie", "").splitlines()
        if l.strip() and not l.strip().startswith("#") and len(l.strip()) > 60
    ]
    return {
        "report_file": meta["source_file"],
        "stem": meta["stem"],
        "report_type": meta["report_type"],
        "year": meta["year"],
        "period": meta["period"],
        "extraction_backend": f"gemini:{model}",
        "metrics": merged_metrics,
        "strategy_highlights": excerpt_lines[:6],
    }


def main():
    parser = argparse.ArgumentParser(description="Stufe 2: Atomare Extraktion aus BEKB-Chunks.")
    parser.add_argument("--backend", choices=["auto", "local", "gemini"], default="auto")
    parser.add_argument("--model", default=DEFAULT_HYDROGEN_MODEL, help="Gemini-Hydrogen-Modell-ID")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "")
    backend = args.backend
    if backend == "auto":
        backend = "gemini" if api_key else "local"
    if backend == "gemini" and not api_key:
        raise RuntimeError("--backend gemini gewählt, aber GEMINI_API_KEY ist nicht gesetzt.")

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    chunk_files = sorted(p for p in CHUNKS_DIR.glob("*.json") if p.name != "manifest.json")

    for cf in chunk_files:
        payload = json.loads(cf.read_text(encoding="utf-8"))
        rt = payload["meta"]["report_type"]
        if backend == "gemini":
            result = extract_with_gemini(payload, api_key, args.model)
        else:
            if rt == "annual":
                result = extract_annual_local(payload)
            elif rt == "semester":
                result = extract_semester_local(payload)
            else:
                result = extract_offenlegung_local(payload)

        out_path = EXTRACTED_DIR / cf.name
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] {len(chunk_files)} Berichte mit Backend '{backend}' nach {EXTRACTED_DIR}/ extrahiert.")


if __name__ == "__main__":
    main()
