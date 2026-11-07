"""Clean encoding artifacts and update branding in src/vayumarg/ui/index.html."""

from pathlib import Path

p = Path("src/vayumarg/ui/index.html")
# Read raw bytes and decode
raw = p.read_bytes()
text = raw.decode("utf-8", errors="replace")

replacements = [
    ("â€”", "—"),
    ("â€¢", "•"),
    ("Â°", "°"),
    ("Â²", "²"),
    ("âš ï¸ ", "⚠️"),
    ("âš ", "⚠️"),
    ("ðŸŒ€", "🌀"),
    ("ðŸš€", "🚀"),
    ("ðŸ›°ï¸ ", "🛰️"),
    ("ðŸ›°", "🛰️"),
    ("âš–ï¸ ", "⚖️"),
    ("âš–", "⚖️"),
    ("ðŸŽ¯", "🎯"),
    ("ðŸ“Š", "📊"),
    ("ðŸ”¬", "🔬"),
    ("âœ“", "✓"),
    ("âœ•", "✗"),
    ("â—¾", "◼"),
    ("Â±", "±"),
    ("SIH 2026", "NOOR 2K26"),
]

for old, new in replacements:
    text = text.replace(old, new)

# Also ensure REMAL walkthrough button is present if desired
if "Walkthrough D: REMAL" not in text:
    old_btns = '<button class="btn-scenario" id="btn-demo-c" onclick="launchWalkthrough(\'walkthrough_c\')">\n      <span>⚖️</span> Walkthrough C: DANA (Scientific Data Governance)\n    </button>'
    new_btns = (
        old_btns
        + '\n    <button class="btn-scenario" id="btn-demo-d" onclick="launchWalkthrough(\'walkthrough_d\')">\n      <span>🌪️</span> Walkthrough D: REMAL (Multi-Horizon Validation)\n    </button>'
    )
    text = text.replace(old_btns, new_btns)

    old_logic = "if (id === 'walkthrough_a') {"
    new_logic = """if (id === 'walkthrough_d') {
        await selectStorm('REMAL');
        switchTab('forecast');
      } else if (id === 'walkthrough_a') {"""
    text = text.replace(old_logic, new_logic)

p.write_text(text, encoding="utf-8")
print(f"Successfully cleaned {p} ({len(text)} chars)")
