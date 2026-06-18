# CLAUDE.md — Trapezoidal Lipped HAT Purlin · IS 801:1975 Design Calculator

Single-file, dependency-free HTML calculator for a cold-formed steel **trapezoidal
lipped top-hat purlin** used in solar MMS. Designs to **IS 801:1975** (working-stress).
Open `index.html` in a browser — no build step, no external libraries.

## How the user works (standing rules — follow these)
- **Cross-check every engineering result twice** before reporting it.
- **Cite the specific IS clause / table / formula** for each check.
- **Flag inferences vs. verified facts** explicitly.
- **Accuracy over token/speed.** Verify before answering.
- **IS 801 is WSM** → use **service / working** load combinations, never LSM-factored.
- The user is a structural engineer (solar EPC). Be concise, technical, justify everything.

## Section geometry (from the shop drawing; authoritative values)
Top-hat, opening down, **feet point outward**, **lip turns UP-and-out**.
- Top flange `B1 = 40 mm`
- Overall height `H = 70 mm`
- **HAT (web) angle `theta = 75°` from horizontal** (= 105° interior at top bend). **Angle governs** (per user) — the drawing's 98 mm bottom width is nominal and NOT used.
- Bottom foot `F = 22 mm` each side
- **Lip `Lp = 10 mm`, lip angle `beta = 45°` from horizontal, pointing UP** (interior foot–lip angle 135°)
- Thickness `t = 0.90 mm`
- Material **G550, Fy = 550 MPa**, E = 200000 MPa
- Derived: web base width 77.5 mm, bottom width (lip-tip) 135.7 mm.
- OPEN ITEM: lip is modeled **up-and-out**. Up-and-in changes Iyy/width only — **Ixx and the deflection verdict are identical** either way. Confirm with user if it matters.

## Verified section properties (lip-up) — REGRESSION TARGETS
Computed by the exact thin-walled polyline method. `validate.py` reproduces these; the
JS engine in `index.html` (`computeProps`) **matches them to the digit** — keep it that way.
```
A      = 224.0   mm^2
ybar   = 31.91   mm   (from foot line y=0)
Ixx    = 161637  mm^4
Iyy    = 295330  mm^4
Ztop   = 4244    mm^3 (top flange, tension fibre under uplift)
Zbot   = 5065    mm^3 (foot line, compression fibre under uplift)
rycf   = 55.0    mm   (radius of gyration of compression flange = feet+lips, about x=0)
web slant = 72.5 mm
```

## Governing load case & current verdict
Uplift (suction) governs. Working loads: WL_uplift 1.128 − DL 0.147 = **w_net 0.981 kN/m**,
simply-supported **span 3.1 m**. Under uplift the purlin hogs → **top flange tension,
bottom (foot) compression**.

| Check | UR | Status | Clause |
|---|---|---|---|
| Bending (governing fibre = top, tension) | 63% | PASS | Cl.6.1 + 6.1.1 (+1/3 wind) |
| Shear | 14% | PASS | Cl.7 |
| LTB (compression-flange method) | no reduction | PASS | Cl.6.2 |
| Edge stiffener (lip) Is≥Imin | OK | PASS | Cl.5.2.2.1 |
| Effective width (all elements fully effective @ service stress) | ρ=1 | PASS | Cl.5.2 |
| **Deflection** | **212%** | **FAIL** | δ=36.5 mm = **L/85** vs L/180 |

**Deflection governs and fails.** Strength is fine. Fixes (need Ixx ×2.1):
`t → ~1.8 mm`, deeper `H`, or **mid-support → span ≈ 2.6 m** (δ ∝ L^4, cheapest).

## IS 801 methodology implemented (in `index.html` `calculate()`)
- **Bending Cl.6.1**: resolve Mz to both fibres (Ztop tension / Zbot compression under uplift); take governing. `+1/3` allowable (Cl.6.1.1) only for wind/seismic combos.
- **Effective width Cl.5.2**: AISI unified Winter λ-method, `ρ=(1−0.22/λ)/λ`, `λ=(1.052/√k)(w/t)√(f/E)`; k=4 stiffened (foot), 0.43 unstiffened (lip), 24 web-gradient. NOTE: this is the modern unified form; IS 801:1975's literal MKS load-formula constants differ slightly (more conservative). If strict 1975-letter compliance is needed, swap in the MKS load formula. Currently all elements are fully effective at service stress, so gross = effective (exact).
- **Edge stiffener Cl.5.2.2.1**: `Is = Lp^3·t·sin²(beta)/12` vs `Imin = max(1.83 t^4 √((w/t)²−4000/Fy_ksi), 9.2 t^4)`.
- **LTB Cl.6.2 — compression-flange method** (deliberate choice): under uplift the compression flange is the bottom feet+lips; treat as a column buckling about x=0 with `rycf`, `Fe = Cb·π²E/(Lb/rycf)²`, then the Cl.6.2 stress transition. The wide outward feet give large rycf → LTB never governs. The rigorous warping/shear-centre (Iw) derivation for this inclined-web+lip shape was intentionally NOT used (would be error-prone and LTB doesn't govern). If LTB ever governs a future geometry, rederive Iw properly.
- **Shear Cl.7**: Fv by web-slant slenderness; Vcap = 2·Fv·H·t (vertical projection).
- **Web crippling Cl.8.1 (EOF)**: included, but **N/A under uplift if feet are bolted** — the support connection (bolts) carries the uplift reaction, not web bearing. Flag the connection check instead. Very weak at t=0.9 for any downward bearing case.
- **Deflection**: STAAD δ if provided, else 5wL^4/384EI (1 kN/m = 1 N/mm — do NOT divide by 1000).

## Input modes (UI)
1. **STAAD forces** (default): unit dropdowns (kN·m / N·mm / kgf·cm; kN / N / kgf) → Mz/My/Fx for uplift & gravity combos, Fy shear, Mx torsion, δ_max; "wind combo" checkbox toggles the +1/3. Axis map: STAAD MZ=strong(Ixx), MY=weak, FY=major shear, MX=torsion. Confirm beta/orientation if Mz↔My could be swapped.
2. **Direct UDL**: w_uplift / w_gravity / w_weak (kN/m); moments via wL²/8.

Axial (Fx≠0) → Cl.6.7.1 combined interaction + compression-stability flag (Fa via ASD column, Q=1). Torsion (Mx≠0) → St-Venant τ flag (open section weak in torsion).

## The engine (do not regress)
`computeProps(g)` = thin-walled polyline: per straight segment, `A=L·t`, centroidal
`Ixx/Iyy` with orientation (`sin²φ/cos²φ`) + parallel axis. Vertex order (full path):
`lipL→footL→webL→topFlange→webR→footR→lipR`. Compression-flange segments for LTB are
indices `0,1,5,6` (the two feet + two lips). After ANY change to the engine, run
`python3 validate.py` and confirm the regression targets above still match.

## Bug history (already fixed — don't reintroduce)
- Deflection units: `w/1000` was wrong (1 kN/m = 1 N/mm); under-reported δ by 1000×.
- Mode toggle: setting `style.display=''` fell back to a CSS `display:none` → panel never showed. Use explicit `'block'`/`'none'`.

## Open items / next steps
- Awaiting the user's **STAAD output** (Mz uplift+gravity, concurrent My/Fx, Fy, Mx, δ, span, Lb, units, which combo is wind, simply-supported vs continuous).
- Likely deliverable after a passing section: **Excel + Word IS 801 calc package** (justification register, clause table, UR verdicts).
- Confirm lip up-in vs up-out (Iyy/width only).
- Optional: swap effective-width to strict IS 801:1975 MKS load formula if letter-compliance required.
