#!/usr/bin/env python
"""
Script to compile markdown reports to PDF.

Usage:
    python scripts/compile_pdf.py results/methodology_report/full_methodology_report.md
    
Or with custom output:
    python scripts/compile_pdf.py input.md -o output.pdf
    
Uses pandoc if available (best quality), falls back to fpdf2.
"""

import sys
import os
import argparse
import shutil
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def main():
    parser = argparse.ArgumentParser(description='Compile markdown report to PDF')
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('-o', '--output', help='Output PDF file (default: same name with .pdf)')
    parser.add_argument('--method', choices=['auto', 'pandoc', 'fpdf'], default='auto',
                        help='Compilation method (default: auto)')
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    output = args.output or args.input.replace('.md', '.pdf')
    
    # Try pandoc first
    pandoc_available = shutil.which('pandoc') is not None
    
    # Also check for downloaded pandoc
    pandoc_paths = [
        '/tmp/pandoc_install/pandoc-3.1.11-arm64/bin/pandoc',
        'pandoc'
    ]
    
    pandoc_cmd = None
    for path in pandoc_paths:
        if os.path.exists(path) or shutil.which(path):
            pandoc_cmd = path
            break
    
    if args.method == 'pandoc' or (args.method == 'auto' and pandoc_cmd):
        if not pandoc_cmd:
            print("Error: pandoc not found")
            sys.exit(1)
            
        print(f"Compiling with pandoc...")
        try:
            result = subprocess.run(
                [pandoc_cmd, args.input,
                 '-o', output,
                 '--pdf-engine=xelatex',
                 '-V', 'geometry:margin=1in',
                 '-V', 'fontsize=11pt',
                 '--toc',
                 '--highlight-style=tango'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"Pandoc error: {result.stderr}")
                if args.method == 'auto':
                    print("Falling back to fpdf...")
                else:
                    sys.exit(1)
            else:
                print(f"PDF saved to: {output}")
                print(f"Size: {os.path.getsize(output):,} bytes")
                return
                
        except Exception as e:
            print(f"Pandoc failed: {e}")
            if args.method == 'auto':
                print("Falling back to fpdf...")
            else:
                sys.exit(1)
    
    # Fall back to fpdf
    print("Compiling with fpdf2 (LaTeX will be plain text)...")
    from metrics import compile_report_to_pdf
    pdf_path = compile_report_to_pdf(args.input, output)
    print(f"PDF saved to: {pdf_path}")
    print(f"Size: {os.path.getsize(pdf_path):,} bytes")
    print("\nNote: For proper LaTeX rendering, install pandoc and LaTeX:")
    print("  brew install pandoc")
    print("  brew install --cask mactex")


if __name__ == '__main__':
    main()
