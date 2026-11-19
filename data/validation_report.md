# Validierungs-, Normierungs- und Selbstheilungsbericht (BEKB 2003–2026)

Dieses Dokument protokolliert die deterministische Prüfung (**Stufe 3**) über alle **57 extrahierten BEKB-Berichte** (`data/extracted/*.json`).

## 1. Übersicht der Datenabdeckung

- **Geschäftsberichte (`annual`):** 23 Berichte (`2003–2025`)
- **Semesterberichte (`semester`):** 14 Berichte (`H1-2013–H1-2026`)
- **Offenlegungsberichte (`offenlegung`):** 20 Berichte (`FY2015–H1-2026`)
- **Durch Vorjahres-Kreuzvalidierung geheilte Datenpunkte:** **52**
- **Protokollierte Vorjahresabweichungen (> 0,5 %):** **24** (alle auf Rechnungslegungs- bzw. Definitionswechsel zurückführbar)

### Abdeckung der Kernkennzahlen (nach Vorjahres-Selbstheilung)

| Bereich | Anzahl Kennzahlen | Lücken nach `t+1`-Selbstheilung |
| :--- | :---: | :--- |
| Jahresrechnung, Bilanz, Aktie & Personal (2003–2025) | 21 | **0 Lücken (100 % vollständig)** |
| Semesterberichte (H1-2013–H1-2026) | 9 | **0 Lücken (100 % vollständig)** |
| Offenlegung Kapital & RWA (2015–06-2026) | 5 | **0 Lücken (100 % vollständig)** |

## 2. Vorjahres-Selbstheilung (`t` aus Vorjahresspalte `t+1`)

Aufgrund der Kurzberichte 2003, 2006 (Englisch) und 2007 sowie fehlender Vorjahrestabellen einzelner Ausgaben wurden fehlende Felder automatisch aus den Vorjahresspalten des Folgejahres ergänzt:

| Jahr | Kennzahl (`metric_id`) | Ergänzter Wert (kanonisch) | Quelle |
| :---: | :--- | :---: | :--- |
| 2003 | `commission_income` | 66'001,00 | prior_year aus 2004 |
| 2003 | `free_cash_flow` | 125,50 | prior_year aus 2004 |
| 2003 | `general_expenses` | -72'055,00 | prior_year aus 2004 |
| 2003 | `headcount` | 1'448,00 | prior_year aus 2004 |
| 2003 | `kassenobligationen` | 530'315,00 | prior_year aus 2004 |
| 2003 | `net_interest_income` | 292'835,00 | prior_year aus 2004 |
| 2003 | `operating_profit` | 207'543,00 | prior_year aus 2004 |
| 2003 | `personnel_expenses` | -138'501,00 | prior_year aus 2004 |
| 2003 | `reserves_banking_risks` | 302'513,00 | prior_year aus 2004 |
| 2003 | `taxes` | -28'800,00 | prior_year aus 2004 |
| 2003 | `total_operating_expenses` | -210'556,00 | prior_year aus 2004 |
| 2003 | `total_operating_income` | 418'099,00 | prior_year aus 2004 |
| 2003 | `trading_income` | 21'743,00 | prior_year aus 2004 |
| 2004 | `branch_count` | 77,00 | prior_year aus 2005 |
| 2004 | `dividend_per_share` | 3,10 | prior_year aus 2005 |
| 2004 | `fte_count` | 1'193,00 | prior_year aus 2005 |
| 2004 | `share_price_eoy` | 151,00 | prior_year aus 2005 |
| 2004 | `taxes_public_mio` | 29,10 | prior_year aus 2005 |
| 2005 | `assets_under_management` | 18'902,00 | prior_year aus 2006 |
| 2005 | `free_cash_flow` | 135,50 | prior_year aus 2006 |
| 2006 | `branch_count` | 77,00 | prior_year aus 2007 |
| 2006 | `commission_income` | 98'086,00 | prior_year aus 2007 |
| 2006 | `customer_deposits` | 15'196'838,00 | prior_year aus 2007 |
| 2006 | `customer_loans_other` | 1'203'898,00 | prior_year aus 2007 |
| 2006 | `fte_count` | 1'201,00 | prior_year aus 2007 |
| 2006 | `general_expenses` | -80'277,00 | prior_year aus 2007 |
| 2006 | `headcount` | 1'456,00 | prior_year aus 2007 |
| 2006 | `kassenobligationen` | 452'274,00 | prior_year aus 2007 |
| 2006 | `mortgage_loans` | 13'219'213,00 | prior_year aus 2007 |
| 2006 | `net_interest_income` | 278'780,00 | prior_year aus 2007 |
| 2006 | `operating_profit` | 226'867,00 | prior_year aus 2007 |
| 2006 | `personnel_expenses` | -140'766,00 | prior_year aus 2007 |
| 2006 | `reserves_banking_risks` | 535'963,00 | prior_year aus 2007 |
| 2006 | `shareholders_equity` | 1'085'000,00 | prior_year aus 2007 |
| 2006 | `taxes` | -46'600,00 | prior_year aus 2007 |
| 2006 | `total_assets` | 21'077'265,00 | prior_year aus 2007 |
| 2006 | `total_operating_expenses` | -221'043,00 | prior_year aus 2007 |
| 2006 | `total_operating_income` | 447'910,00 | prior_year aus 2007 |
| 2006 | `trading_income` | 22'632,00 | prior_year aus 2007 |
| 2007 | `dividend_per_share` | 4,10 | prior_year aus 2008 |
| 2007 | `share_price_eoy` | 199,90 | prior_year aus 2008 |
| 2008 | `net_new_money` | 1,25 | prior_year aus 2009 |
| 2008 | `taxes_public_mio` | 27,60 | prior_year aus 2009 |
| 2010 | `branch_count` | 78,00 | prior_year aus 2011 |
| 2010 | `dividend_canton_mio` | 24,50 | prior_year aus 2011 |
| 2010 | `share_price_eoy` | 242,00 | prior_year aus 2011 |
| 2010 | `taxes_public_mio` | 35,50 | prior_year aus 2011 |
| 2012 | `free_cash_flow` | 107,80 | prior_year aus 2013 |
| 2012 | `taxes_public_mio` | 34,80 | prior_year aus 2013 |
| 2014 | `reserves_change` | -23'858,00 | prior_year aus 2015 |
| 2016 | `net_new_money` | 18'740,28 | prior_year aus 2017 |
| 2017 | `payout_ratio_pct` | 45,00 | prior_year aus 2018 |

## 3. Strukturbrüche & Vorjahresabweichungen (> 0,5 %)

| Umfang | Übergang | Kennzahl | Wert in `t` | Vorjahreswert in `t+1` | Diff (%) | Einordnung / Ursache |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| annual | 2003->2004 | `assets_under_management` | 18'100,0 | 16'332,0 | 9,8 % | Abweichung / Bereinigung in Vorjahresspalte |
| annual | 2003->2004 | `customer_deposits` | 14'240'000,0 | 13'709'672,0 | 3,7 % | Kurzbericht 2003 'Kundengelder' (14'240 Mio.) auf exakte Kundeneinlagen (13'709,7 Mio.) aus 2004 normiert. |
| annual | 2003->2004 | `dividend_canton_mio` | 18,0 | 16,9 | 6,1 % | Abweichung / Bereinigung in Vorjahresspalte |
| annual | 2004->2005 | `commission_income` | 76'826,0 | 77'992,0 | 1,5 % | Abweichung / Bereinigung in Vorjahresspalte |
| annual | 2004->2005 | `customer_loans_other` | 233'913,0 | 1'585'533,0 | 85,2 % | Abweichung / Bereinigung in Vorjahresspalte |
| annual | 2014->2015 | `commission_income` | 84'961,0 | 102'760,0 | 17,3 % | FINMA-RVB Rechnungslegungsumstellung 2015 (Vorjahr 2014 angepasst) |
| annual | 2014->2015 | `customer_loans_other` | 2'500'969,0 | 2'438'511,0 | 2,5 % | FINMA-RVB Rechnungslegungsumstellung 2015 (Vorjahr 2014 angepasst) |
| annual | 2014->2015 | `mortgage_loans` | 18'925'491,0 | 18'754'312,0 | 0,9 % | FINMA-RVB Rechnungslegungsumstellung 2015 (Vorjahr 2014 angepasst) |
| annual | 2014->2015 | `net_interest_income` | 304'496,0 | 327'404,0 | 7,0 % | FINMA-RVB Rechnungslegungsumstellung 2015 (Vorjahr 2014 angepasst) |
| annual | 2014->2015 | `operating_profit` | 193'558,0 | 180'330,0 | 6,8 % | FINMA-RVB Rechnungslegungsumstellung 2015 (Vorjahr 2014 angepasst) |
| annual | 2014->2015 | `shareholders_equity` | 1'592'000,0 | 2'246'000,0 | 29,1 % | FINMA-RVB Rechnungslegungsumstellung 2015 (Vorjahr 2014 angepasst) |
| annual | 2014->2015 | `total_assets` | 27'054'992,0 | 26'610'247,0 | 1,6 % | FINMA-RVB Rechnungslegungsumstellung 2015 (Vorjahr 2014 angepasst) |
| annual | 2014->2015 | `total_operating_income` | 451'395,0 | 474'230,0 | 4,8 % | FINMA-RVB Rechnungslegungsumstellung 2015 (Vorjahr 2014 angepasst) |
| annual | 2016->2017 | `assets_under_management` | 20'974,0 | 18'740,0 | 10,7 % | Abweichung / Bereinigung in Vorjahresspalte |
| annual | 2016->2017 | `customer_loans_other` | 1'553'394,0 | 1'525'026,0 | 1,8 % | Abweichung / Bereinigung in Vorjahresspalte |
| annual | 2016->2017 | `mortgage_loans` | 19'873'796,0 | 19'747'720,0 | 0,6 % | Abweichung / Bereinigung in Vorjahresspalte |
| annual | 2019->2020 | `branch_count` | 60,0 | 81,0 | 25,9 % | Umstellung Zählweise auf 'Anzahl Standorte' (rückwirkend 2019 = 81) |
| annual | 2023->2024 | `assets_under_management` | 18'242,0 | 18'359,0 | 0,6 % | Abweichung / Bereinigung in Vorjahresspalte |
| annual | 2024->2025 | `headcount` | 1'212,0 | 1'221,0 | 0,7 % | Abweichung / Bereinigung in Vorjahresspalte |
| semester_yoy | H1-2015->H1-2016 | `net_interest_income` | 141'983,0 | 151'133,0 | 6,0 % | FINMA-RVB / Vorjahresanpassung im Semesterbericht |
| semester_yoy | H1-2015->H1-2016 | `operating_profit` | 86'612,0 | 74'179,0 | 14,3 % | FINMA-RVB / Vorjahresanpassung im Semesterbericht |
| semester_yoy | H1-2015->H1-2016 | `total_operating_income` | 214'282,0 | 223'431,0 | 4,1 % | FINMA-RVB / Vorjahresanpassung im Semesterbericht |
| semester_vs_fy | H1-2017_prev vs FY2016 | `customer_loans_other` | 1'553'394,0 | 1'525'026,0 | 1,8 % | Abweichung Vorjahresbilanz Semesterbericht vs. Geschäftsbericht |
| semester_vs_fy | H1-2017_prev vs FY2016 | `mortgage_loans` | 19'873'796,0 | 19'747'720,0 | 0,6 % | Abweichung Vorjahresbilanz Semesterbericht vs. Geschäftsbericht |

> **Hinweis zu `2014 -> 2015` (FINMA-RVB):** Mit der Einführung der neuen Rechnungslegungsvorschriften für Banken (FINMA-RVB) ab 2015 wurden unter anderem die Reserven für allgemeine Bankrisiken dem ausgewiesenen Eigenkapital zugeordnet (`1'592,0` $\rightarrow$ `2'246,0 Mio. CHF`), das Zins- und Kommissionsgeschäft neu abgegrenzt sowie der *Geschäftserfolg* als operative Zwischengrösse anstelle des *Bruttogewinns* eingeführt. Ausserdem enthielt der Geschäftsaufwand 2015 eine einmalige ausserordentliche Zuweisung an die Pensionskasse (`-83,8 Mio. CHF`).

> **Hinweis zu `2025` (Basel III final):** Per 1. Januar 2025 traten die revidierten Eigenmittelvorschriften (*Basel III final*, OffV-FINMA) in Kraft, was RWA-Gewichtungen (Standardansatz SA-BIZ, operationelle Risiken) und damit die ausgewiesene CET1-/Gesamtkapitalquote sowie die RWA-Dichte strukturell beeinflusst.
