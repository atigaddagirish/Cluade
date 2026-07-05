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

## Site rain watch (weather.html)
Mobile weather app for the solar site at **16.0879°N 78.1000°E** (Jogulamba Gadwal, TG),
showing **official IMD data only** — past-24 h rainfall, 7-day forecast, 3-h nowcast
warnings, Hyderabad Doppler radar and INSAT satellite rain imagery.

**Data path (all numbers originate from IMD):**
Since mid-2026 IMD's JSON APIs (`mausam.imd.gov.in/api`, `city.imd.gov.in/api`) return
**HTTP 401 "IP needs to be whitelisted"** to the public — verified 2026-07-04 from GitHub
runners. The app therefore works relay-first in practice:
1. `.github/workflows/imd-weather.yml` runs `scripts/fetch_imd.py` every 30 min on GitHub
   Actions. It still tries the JSON APIs (self-heals if IMD reopens them), then falls back
   to **IMD's public city weather page** `city.imd.gov.in/citywx/citywxnew.php?id=43213`
   (Kurnool — past-24 h obs incl. rainfall + 7-day forecast), parses it, and pushes
   `imd.json` to the orphan branch `weather-data`.
2. The page reads that JSON from `raw.githubusercontent.com` (CORS-open). Each card's badge
   shows LIVE vs RELAY and the data age; the Info tab has per-source diagnostics.
3. Optional upgrade: register (free) at `api.imd.gov.in`, add the key as repo secret
   `IMD_API_KEY` — the relay then also pulls the new official gateway (incl. nowcast).
   `scripts/probe_imd.py` re-checks what IMD serves publicly if things break again.

**Put it on your phone:** host the repo on GitHub Pages (Settings → Pages → deploy from
branch), open `https://<user>.github.io/Cluade/weather.html` in Chrome, then
⋮ → *Add to Home screen*. It installs as a standalone app icon. (A true Android
home-screen *widget* needs a native app — a web page can't provide one; the installed
PWA icon + this app is the closest web equivalent.)

**Important setup notes:**
- The **schedule only runs from the repo's default branch** — merge the workflow there,
  then test it once via Actions → "IMD weather relay" → *Run workflow*.
- Nowcast: the Jogulamba Gadwal **district ID** is not pre-filled (unverified). Find it at
  `mausam.imd.gov.in` → Nowcast page (the district dropdown's value), then enter it in the
  app's ⚙ Settings and in the workflow's `--district` argument.
- Official IMD mobile apps (zero setup, same data): **Mausam** (forecasts + nowcast),
  **Meghdoot** (agromet), **Damini** (lightning alerts — relevant for MMS sites).

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
