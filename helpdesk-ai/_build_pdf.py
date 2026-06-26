# -*- coding: utf-8 -*-
"""Convertit CAHIER_DES_CHARGES.md en PDF propre (tableaux, code, accents FR)."""
from pathlib import Path
from markdown_pdf import MarkdownPdf, Section

base = Path(r"C:\projetpfe\helpdesk-ai")
md_path = base / "CAHIER_DES_CHARGES.md"
pdf_path = base / "CAHIER_DES_CHARGES.pdf"

text = md_path.read_text(encoding="utf-8")

css = """
* { font-family: 'Helvetica', 'Arial', sans-serif; }
body { font-size: 10pt; line-height: 1.45; color: #1a1a1a; }
h1 { color: #0b3d91; font-size: 18pt; border-bottom: 2px solid #0b3d91;
     padding-bottom: 4px; margin-top: 18px; }
h2 { color: #0b3d91; font-size: 13.5pt; margin-top: 14px; }
h3 { color: #222; font-size: 11.5pt; margin-top: 10px; }
table { border-collapse: collapse; width: 100%; font-size: 8.5pt; margin: 6px 0; }
th, td { border: 1px solid #9aa6c0; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #e8eefc; color: #0b3d91; }
code { font-family: 'Courier New', monospace; font-size: 9pt; background: #f2f2f2; }
pre { background: #f6f8fa; border: 1px solid #ddd; padding: 8px; font-size: 8.5pt; }
blockquote { border-left: 4px solid #0b3d91; background: #f4f7ff;
             padding: 6px 10px; color: #2a2a2a; }
"""

pdf = MarkdownPdf(toc_level=2, optimize=True)
pdf.add_section(Section(text, toc=True, paper_size="A4"), user_css=css)
pdf.meta["title"] = "Cahier des Charges - Plateforme intelligente de gestion de tickets IT"
pdf.meta["author"] = "Mohamed Amine Toukabri"
pdf.meta["subject"] = "PFE - Intelligence Artificielle"
pdf.save(str(pdf_path))

print("OK ->", pdf_path)
print("Taille:", pdf_path.stat().st_size, "octets")
