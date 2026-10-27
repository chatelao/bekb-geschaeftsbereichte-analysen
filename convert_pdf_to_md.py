#!/usr/bin/env python3
"""
BEKB PDF to Markdown Converter
Converts PDF documents in pdf/ to Markdown files in .md/ with extracted images.
"""

import argparse
import glob
import os
import sys
import pymupdf4llm


def convert_pdf(pdf_path, output_dir=".md", images_base_dir=".md/images", force=False):
    pdf_filename = os.path.basename(pdf_path)
    stem = os.path.splitext(pdf_filename)[0]
    target_md_path = os.path.join(output_dir, f"{stem}.md")
    target_img_dir = os.path.join(images_base_dir, stem)

    if os.path.exists(target_md_path) and not force:
        print(f"[SKIP] {target_md_path} already exists. Use --force to overwrite.")
        return True

    print(f"[CONVERTING] {pdf_path} -> {target_md_path}...")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(target_img_dir, exist_ok=True)

    try:
        md_text = pymupdf4llm.to_markdown(
            pdf_path,
            write_images=True,
            image_path=target_img_dir,
            image_format="png"
        )
        # Fix image paths in markdown to be relative to the .md directory
        # pymupdf4llm prefixes image path with the target_img_dir passed to it
        md_text = md_text.replace(f"{target_img_dir}/", f"images/{stem}/")
        md_text = md_text.replace(f"{images_base_dir}/", "images/")

        with open(target_md_path, "w", encoding="utf-8") as f:
            f.write(md_text)

        print(f"[OK] Successfully converted {pdf_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to convert {pdf_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert BEKB PDF reports to Markdown.")
    parser.add_argument("--files", nargs="*", help="Specific PDF file paths to convert.")
    parser.add_argument("--pattern", type=str, help="Glob pattern to match PDF files in pdf/ (e.g. 'bekb-semesterbericht-201*').")
    parser.add_argument("--force", action="store_true", help="Overwrite existing Markdown files.")
    args = parser.parse_args()

    files_to_convert = []
    if args.files:
        files_to_convert = args.files
    elif args.pattern:
        files_to_convert = sorted(glob.glob(os.path.join("pdf", args.pattern)))
        if not files_to_convert and not args.pattern.startswith("pdf/"):
            files_to_convert = sorted(glob.glob(args.pattern))
    else:
        files_to_convert = sorted(glob.glob("pdf/*.pdf"))

    if not files_to_convert:
        print("No PDF files found to convert.")
        sys.exit(0)

    print(f"Found {len(files_to_convert)} file(s) to convert.")
    success_count = 0
    for pdf_path in files_to_convert:
        if convert_pdf(pdf_path, force=args.force):
            success_count += 1

    print(f"\nDone: {success_count}/{len(files_to_convert)} files processed.")


if __name__ == "__main__":
    main()
