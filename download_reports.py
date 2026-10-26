#!/usr/bin/env python3
"""
BEKB Geschäftsberichte Downloader
Downloads all available BEKB annual reports (Geschäftsberichte) into /pdf and ./pdf.
"""

import os
import sys
import time
import urllib.request
import json
import re

TARGET_DIRS = ["/pdf", "pdf"]

# Selected Wayback Machine snapshots for BEKB Geschäftsberichte per year
YEAR_SNAPSHOTS = {
    2003: "https://web.archive.org/web/20041017232327id_/http://www.bekb.ch:80/de/geschaeftsbericht_2003.pdf",
    2004: "https://web.archive.org/web/20061104223357id_/http://www.bekb.ch:80/de/bekb_geschaeftsbericht_2004_gesamt.pdf",
    2005: "https://web.archive.org/web/20061024033735id_/http://www.bekb.ch:80/fr/gb2005_gesamt_deutsch_2005.pdf",
    2006: "https://web.archive.org/web/20081206211758id_/http://www.bekb.ch/en/geschaeftsbericht_2006_kurz.pdf",
    2007: "https://web.archive.org/web/20081206204007id_/http://www.bekb.ch/de/geschaeftsbericht_2007_kurz.pdf",
    2008: "https://web.archive.org/web/20100107103139id_/http://www.bekb.ch:80/de/bekb-geschaeftsbericht_2008_gesamt.pdf",
    2009: "https://web.archive.org/web/20260210094323id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2009.pdf?vs=1&sc_lang=de&hash=9B265D4A063D4BAE85E59B0DA524E365",
    2010: "https://web.archive.org/web/20260618044719id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2010.pdf?la=de&vs=1&hash=756748648B343392CB91D8F56D539BC2725BC425",
    2011: "https://web.archive.org/web/20260210091002id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2011.pdf?vs=1&sc_lang=de&hash=5DF5FBB9A95165727DFDF44DB1ECBF78",
    2012: "https://web.archive.org/web/20260519152937id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2012.pdf?la=de&vs=1&hash=49B7AF6121EF4ADA090A70B5F178DB012813C829",
    2013: "https://web.archive.org/web/20260210094624id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2013.pdf?vs=1&sc_lang=de&hash=F086EFC69E2D98FAA6F6DFFC5920D9AC",
    2014: "https://web.archive.org/web/20260210094206id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2014.pdf?vs=1&sc_lang=de&hash=BEDA35278B2C50625DEDE726C8223F88",
    2015: "https://web.archive.org/web/20240910115336id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2015.pdf?la=de&vs=1",
    2016: "https://web.archive.org/web/20260210082041id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2016.pdf?vs=1&sc_lang=de&hash=A1821F82FEB66659F6C65B1D816B5420",
    2017: "https://web.archive.org/web/20260210083548id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2017.pdf?vs=2&sc_lang=de&hash=8C528DDCA713FCCFFCC6002F8510EA1D",
    2018: "https://web.archive.org/web/20260210083959id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2018.pdf?vs=1&sc_lang=de&hash=BBC72F50DB9149E9A8C29BA46A6F6267",
    2019: "https://web.archive.org/web/20260210090742id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2019.pdf?vs=1&sc_lang=de&hash=73EF41222F3BB4406B7DE1A1BAF71C80",
    2020: "https://web.archive.org/web/20260210094836id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2020.pdf?vs=1&sc_lang=de&hash=A5B65776E96EFD1943B73019E076C24F",
    2021: "https://web.archive.org/web/20260210083156id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/berichte-2021-und-2022/geschaeftsbericht-2021.pdf?vs=1&sc_lang=de&hash=B31C042B22EA65BFB1282864CA155A56",
    2022: "https://web.archive.org/web/20260210084738id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2022.pdf?vs=1&sc_lang=de&hash=2DC1DE426E3CEBB4E2CF908605DE7CA8",
    2023: "https://web.archive.org/web/20260210084218id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2023.pdf?vs=1&sc_lang=de&hash=2E1E4618E8B88756AA6BAE1F476B5A36",
    2024: "https://web.archive.org/web/20260210080114id_/https://www.bekb.ch/-/media/bekb/portal/documents/ueber-bekb/publikationen/berichterstattung/bekb-geschaeftsbericht-2024.pdf?vs=1&sc_lang=de&hash=513419D8D9B7D4D0DE493798D183D788",
}


def download_file(url, target_filename):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(5):
        try:
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
                if data.startswith(b"%PDF"):
                    for d in TARGET_DIRS:
                        os.makedirs(d, exist_ok=True)
                        filepath = os.path.join(d, target_filename)
                        with open(filepath, "wb") as f:
                            f.write(data)
                    print(f"[OK] Downloaded {target_filename} ({len(data)} bytes)")
                    return True
                else:
                    print(f"[WARNING] Non-PDF response for {target_filename} (Magic: {data[:20]})")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {target_filename}: {e}")
            time.sleep(3)
    return False


def main():
    print("Starting download of BEKB Geschäftsberichte...")
    for target_dir in TARGET_DIRS:
        os.makedirs(target_dir, exist_ok=True)

    success_count = 0
    total = len(YEAR_SNAPSHOTS)

    for year in sorted(YEAR_SNAPSHOTS.keys()):
        url = YEAR_SNAPSHOTS[year]
        filename = f"bekb-geschaeftsbericht-{year}.pdf"
        print(f"\nDownloading year {year} -> {filename}...")
        if download_file(url, filename):
            success_count += 1

    print(f"\nCompleted: {success_count}/{total} files downloaded successfully.")


if __name__ == "__main__":
    main()
