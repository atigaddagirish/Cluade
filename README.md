# HAT Purlin IS 801 Calculator — project handoff

Cold-formed **trapezoidal lipped top-hat purlin** designer to **IS 801:1975** (working-stress),
for solar MMS. Single-file HTML, no build, no dependencies.

```
hat-purlin-tool/
├── index.html     the calculator (open in any browser)
├── CLAUDE.md      full context for Claude Code — geometry, verified numbers,
│                  IS 801 methodology, standing rules, open items
├── validate.py    regression test — reproduces the verified section properties
│                  and the IS 801 verdict (the JS engine must match this)
└── README.md      this file
```

## Use the calculator
Open `index.html` in a browser. Two load-input modes: **STAAD forces** (default) and **Direct UDL**.

## Verify the engine
```bash
python3 validate.py
```
Confirms A=224.0, Ixx=161637, Ztop=4244, Zbot=5065 mm and the verdict
(bending 63% PASS, shear 14% PASS, LTB no-govern, deflection L/85 **FAIL**).
Run this after any change to `index.html`'s `computeProps`.

## Continue in Claude Code
1. Put this folder somewhere on your machine (keep the 4 files together).
2. Install Claude Code (pick one):
   - **Native installer (recommended, no Node.js):**
     - macOS / Linux / WSL: `curl -fsSL https://claude.ai/install.sh | bash`
     - Homebrew: `brew install --cask claude-code`
     - Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`
   - **npm (needs Node.js 18+):** `npm install -g @anthropic-ai/claude-code` (do not use sudo)
   - Prefer a GUI? The **Claude Desktop app** (macOS/Windows) runs Claude Code without a terminal.
3. Open a terminal in this folder and start it:
   ```bash
   cd hat-purlin-tool
   claude
   ```
4. Claude Code auto-reads `CLAUDE.md` for context. Good first prompts:
   - "Read CLAUDE.md, run validate.py, and confirm index.html still matches the targets."
   - "Add the lip up-in vs up-out toggle."
   - "Build the Excel + Word IS 801 calc package for the current section."

Docs: https://docs.claude.com/en/docs/claude-code/overview
