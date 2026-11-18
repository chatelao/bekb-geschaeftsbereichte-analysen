#!/usr/bin/env python3
"""
BEKB Berichte Downloader
Downloads all available BEKB Geschäftsberichte, Semesterberichte, and Offenlegungsberichte into /pdf and ./pdf.
"""

import os
import sys
import time
import urllib.request

TARGET_DIRS = ["/pdf", "pdf"]

# Selected URLs for BEKB Geschäftsberichte per year
GESCHAEFTSBERICHTE_URLS = {
    2003: "https://web.archive.org/web/20041017232327id_/http://www.bekb.ch:80/de/geschaeftsbericht_2003.pdf",
    2004: "https://web.archive.org/web/20061104223357id_/http://www.bekb.ch:80/de/bekb_geschaeftsbericht_2004_gesamt.pdf",
    2005: "https://web.archive.org/web/20061024033735id_/http://www.bekb.ch:80/fr/gb2005_gesamt_deutsch_2005.pdf",
    2006: "https://web.archive.org/web/20081206211758id_/http://www.bekb.ch/en/geschaeftsbericht_2006_kurz.pdf",
    2007: "https://web.archive.org/web/20081206204007id_/http://www.bekb.ch/de/geschaeftsbericht_2007_kurz.pdf",
    2008: "https://web.archive.org/web/20100107103139id_/http://www.bekb.ch:80/de/bekb-geschaeftsbericht_2008_gesamt.pdf",
    2009: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2009.pdf?vs=1&sc_lang=de",
    2010: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2010.pdf?vs=1&sc_lang=de",
    2011: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2011.pdf?vs=1&sc_lang=de",
    2012: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2012.pdf?vs=1&sc_lang=de",
    2013: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2013.pdf?vs=1&sc_lang=de",
    2014: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2014.pdf?vs=1&sc_lang=de",
    2015: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2015.pdf?vs=1&sc_lang=de",
    2016: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2016.pdf?vs=1&sc_lang=de",
    2017: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2017.pdf?vs=2&sc_lang=de",
    2018: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2018.pdf?vs=1&sc_lang=de",
    2019: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2019.pdf?vs=1&sc_lang=de",
    2020: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2020.pdf?vs=1&sc_lang=de",
    2021: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/berichte-2021-und-2022/geschaeftsbericht-2021.pdf?vs=1&sc_lang=de",
    2022: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2022.pdf?vs=1&sc_lang=de",
    2023: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2023.pdf?vs=1&sc_lang=de",
    2024: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2024.pdf?vs=1&sc_lang=de",
    2025: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2025.pdf?vs=1&sc_lang=de",
}

# Selected Wayback Machine snapshots for BEKB Semesterberichte per year
SEMESTER_SNAPSHOTS = {
    2013: "https://web.archive.org/web/20260210080829id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterbericht-2013.pdf?la=de&vs=1&hash=AB74DD18945B2908919A8D21BC4797553155199B",
    2014: "https://web.archive.org/web/20260210081014id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterbericht-2014.pdf?la=de&vs=1&hash=27970F7EEEA7A526A6C0DFB5C7A68CA7BC91478E",
    2015: "https://web.archive.org/web/20260210080644id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterbericht-2015.pdf?la=de&vs=1&hash=1C8DC081D2A2A8884106A7FA05104346AE640794",
    2016: "https://web.archive.org/web/20260210080512id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterbericht-2016.pdf?la=de&vs=1&hash=65F9D1420F562C0EDAB32CE506EBB167F837218D",
    2017: "https://web.archive.org/web/20260210080313id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterbericht-2017.pdf?la=de&vs=1&hash=8D9AA1F9C47E50295B2C69C24FCDE528691B384A",
    2018: "https://web.archive.org/web/20260210092807id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterergebnis-2018.pdf?vs=1&sc_lang=de&hash=3508BE681433595BE68433501C74E20C",
    2019: "https://web.archive.org/web/20260210094927id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterergebnis-2019.pdf?vs=2&sc_lang=de&hash=0C6DF5E836786BFF9A1380322D9BC2A2",
    2020: "https://web.archive.org/web/20201201023502id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterergebnis-2020.pdf?la=de&vs=2&hash=FA702BD5E8DDE2733D073D86A94160D93E6F807A",
    2021: "https://web.archive.org/web/20260119014127id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-semesterergebnis-2021.pdf?vs=2&sc_lang=de&hash=BE6BBE277CE1ACF386BF7BDFA4ADA01C",
    2022: "https://web.archive.org/web/20260210083314id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/berichte-2021-und-2022/semesterergebnis-220728-einzelseiten.pdf?vs=2&sc_lang=de&hash=D6D82799A82AD52EAA3E5147A72B525B",
    2023: "https://web.archive.org/web/20231031232058id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/bekb-semesterbericht-2023.pdf?la=de&vs=2&hash=B1EAE504633A86C1250B808EB66DCBD159036094",
    2024: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/bekb-semesterbericht-2024.pdf?vs=3&sc_lang=de",
    2025: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/bekb-semesterbericht-2025.pdf?vs=1&sc_lang=de",
    2026: "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/bekb-semesterbericht-2026.pdf?vs=2&sc_lang=de",
}

# Selected URLs for BEKB Offenlegungsberichte
OFFENLEGUNG_SNAPSHOTS = {
    # Annual reports (Jahres-Offenlegungsberichte)
    "bekb-offenlegungsbericht-2015.pdf": "https://web.archive.org/web/20231031232458id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2015.pdf",
    "bekb-offenlegungsbericht-2016.pdf": "https://web.archive.org/web/20231031231535id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2016.pdf",
    "bekb-offenlegungsbericht-2017.pdf": "https://web.archive.org/web/20231031231438id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2017.pdf",
    "bekb-offenlegungsbericht-2018.pdf": "https://web.archive.org/web/20231031231637id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2018.pdf",
    "bekb-offenlegungsbericht-2019.pdf": "https://web.archive.org/web/20231031231803id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2019.pdf",
    "bekb-offenlegungsbericht-2020.pdf": "https://web.archive.org/web/20231031231554id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2020.pdf",
    "bekb-offenlegungsbericht-2021.pdf": "https://web.archive.org/web/20231031231919id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/berichte-2021-und-2022/offenlegungsbericht-2021.pdf",
    "bekb-offenlegungsbericht-2022.pdf": "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2022-1.pdf?vs=1&sc_lang=de",
    "bekb-offenlegungsbericht-2023.pdf": "https://web.archive.org/web/20250519045210id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/offenlegungsbericht-2023.pdf?la=de&vs=1&hash=7A569AE3256CF8A40849CF597CA69652564F25FC",
    "bekb-offenlegungsbericht-2024.pdf": "https://web.archive.org/web/20260210095037id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2024.pdf?vs=2&sc_lang=de&hash=6B457092BB594F16B5FD4BA50BAB0EA5",
    "bekb-offenlegungsbericht-2025.pdf": "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-2025.pdf?vs=2&sc_lang=de",
    # Semi-annual reports (Semester-Offenlegungsberichte per mid-year 06)
    "bekb-offenlegungsbericht-06-2018.pdf": "https://web.archive.org/web/20231031231635id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-06-2018.pdf",
    "bekb-offenlegungsbericht-06-2019.pdf": "https://web.archive.org/web/20231031231420id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-06-2019.pdf",
    "bekb-offenlegungsbericht-06-2020.pdf": "https://web.archive.org/web/20231031232832id_/http://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-06-2020.pdf",
    "bekb-offenlegungsbericht-06-2021.pdf": "https://web.archive.org/web/20231031231943id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-offenlegungsbericht-06-2021.pdf",
    "bekb-offenlegungsbericht-06-2022.pdf": "https://web.archive.org/web/20231031232244id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/berichte-2021-und-2022/offenlegung-semester-2022.pdf",
    "bekb-offenlegungsbericht-06-2023.pdf": "https://web.archive.org/web/20260210101158id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/bekb-offenlegung-semester-2023.pdf?vs=1&sc_lang=de&hash=1ED14F76A6110460481992930C8E7A2B",
    "bekb-offenlegungsbericht-06-2024.pdf": "https://web.archive.org/web/20260210083236id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/bekb-offenlegung-semster-2024.pdf?vs=2&sc_lang=de&hash=86D1C34274CAF429955E0CE03A4A771B",
    "bekb-offenlegungsbericht-06-2025.pdf": "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/bekb-offenlegung-semester-2025.pdf?vs=1&sc_lang=de",
    "bekb-offenlegungsbericht-06-2026.pdf": "https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/portraet/bekb-offenlegung-semester-2026.pdf?vs=2&sc_lang=de",
}


def download_file(url, target_filename):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(10):
        try:
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
                if data.startswith(b"%PDF") and b"%%EOF" in data[-1024:]:
                    for d in TARGET_DIRS:
                        try:
                            os.makedirs(d, exist_ok=True)
                            filepath = os.path.join(d, target_filename)
                            with open(filepath, "wb") as f:
                                f.write(data)
                        except Exception as e:
                            print(f"[WARNING] Could not write to directory {d}: {e}")
                    print(f"[OK] Downloaded {target_filename} ({len(data)} bytes)")
                    return True
                else:
                    print(f"[WARNING] Invalid or truncated PDF response for {target_filename} (size={len(data)}, Magic={data[:20]})")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {target_filename}: {e}")
            time.sleep(3)
    return False


def main():
    print("Starting download of BEKB Berichte...")
    for target_dir in TARGET_DIRS:
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            print(f"[WARNING] Could not create target directory {target_dir}: {e}")

    print("\n--- Geschäftsberichte ---")
    success_gb = 0
    total_gb = len(GESCHAEFTSBERICHTE_URLS)
    for year in sorted(GESCHAEFTSBERICHTE_URLS.keys()):
        url = GESCHAEFTSBERICHTE_URLS[year]
        filename = f"bekb-geschaeftsbericht-{year}.pdf"
        print(f"\nDownloading Geschäftsbericht {year} -> {filename}...")
        if download_file(url, filename):
            success_gb += 1
        time.sleep(1)

    print("\n--- Semesterberichte ---")
    success_semester = 0
    total_semester = len(SEMESTER_SNAPSHOTS)
    for year in sorted(SEMESTER_SNAPSHOTS.keys()):
        url = SEMESTER_SNAPSHOTS[year]
        filename = f"bekb-semesterbericht-{year}.pdf"
        print(f"\nDownloading year {year} -> {filename}...")
        if download_file(url, filename):
            success_semester += 1
        time.sleep(2)

    print("\n--- Offenlegungsberichte ---")
    success_offenlegung = 0
    total_offenlegung = len(OFFENLEGUNG_SNAPSHOTS)
    for filename in sorted(OFFENLEGUNG_SNAPSHOTS.keys()):
        url = OFFENLEGUNG_SNAPSHOTS[filename]
        print(f"\nDownloading Offenlegungsbericht -> {filename}...")
        if download_file(url, filename):
            success_offenlegung += 1
        time.sleep(2)

    print(f"\nCompleted:")
    print(f"  Geschäftsberichte:   {success_gb}/{total_gb}")
    print(f"  Semesterberichte:    {success_semester}/{total_semester}")
    print(f"  Offenlegungsberichte:{success_offenlegung}/{total_offenlegung}")


if __name__ == "__main__":
    main()
