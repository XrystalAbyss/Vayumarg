"""Clean branding and encoding in hackathon documents."""

from pathlib import Path

files = list(Path("hackathon").glob("*.md")) + [Path("start_vayumarg.ps1")]
for f in files:
    if not f.is_file():
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    text = text.replace("SIH 2026", "NOOR 2K26")
    text = text.replace("â€”", "—")
    text = text.replace("â€¢", "•")
    text = text.replace("Â°", "°")
    text = text.replace("Â²", "²")
    f.write_text(text, encoding="utf-8")
    print(f"Updated {f.name}")
