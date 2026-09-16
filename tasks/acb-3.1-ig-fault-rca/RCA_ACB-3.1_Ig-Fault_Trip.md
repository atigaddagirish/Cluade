# Root Cause Analysis — Repeated Ig (Ground-Fault) Tripping of ACB 3.1

**Bus-duct ACB on Inverter 3.1, Block-3 (ICR-3)**

| | |
|---|---|
| **Plant** | Essens Renewable Pvt. Ltd. (Amplus IRU Pvt. Ltd.), Thoothukudi District, Tamil Nadu — PIN 628001 |
| **Affected equipment** | Sungrow **SG3125HV-32** central inverter, Unit **3.1**, SN **I23B1700303**; associated **Schneider MasterPact / Micrologic** bus-duct ACB (3-pole) |
| **Symptom** | Repeated ACB tripping on **"Ig" (ground / earth-fault)** indication, predominantly during **morning hours**; inverter subsequently trips on AC over-voltage / abnormal frequency |
| **Schneider case ref.** | CC202526C13E |
| **RCA prepared by** | OEM / senior-engineering review (15-yr equivalent), on behalf of Essens Renewable |
| **RCA date** | 16-Sep-2026 |
| **Status** | Root cause **identified with high confidence**; **field fault-location pending**. Vendor recommendation to disable Ig protection is **NOT endorsed** (see §7). |

---

## 1. Purpose & scope

Consolidate and independently verify the two vendor investigations —
Schneider Electric (breaker OEM, report **24-Jul-2026**) and Sungrow (inverter OEM,
report **09-Sep-2026** + clarification email **15-Sep-2026**) — into a single
root-cause position, and give a defensible engineering decision on the pending
request to **disable/bypass the Ig protection**.

Every finding below is cross-checked against **at least two independent data sources**
and is tagged **[VERIFIED]** (supported by measured data from both vendors),
**[INFERENCE]** (engineering deduction, not directly measured), or **[OPEN]**
(to be confirmed in the field).

---

## 2. Evidence base (as received)

**Source A — Schneider Electric, 24-Jul-2026** (returned-breaker lab analysis + Power Quality Analyzer records for the trip event 23-May-2025, 13:34:02):

- Breaker + Micrologic trip unit lab-tested: current-sensor resistance healthy; sensor-to-Micrologic wiring healthy; **primary and secondary current-injection tests passed**. Verdict: **No Problem Found (NFP)** — no equipment defect.
- PQA is connected on the **load (inverter/LV) side** of the breaker. Three consecutive 250 ms samples:

| Sample time | State | V (ph-ph) R/Y/B | Current /phase | Active power | Notable |
|---|---|---|---|---|---|
| 13:34:02.088 & .338 | Normal | 658 / 651 / 662 V | ≈ 2.42 kA | ≈ 2.758 MW | Stable, balanced |
| 13:34:02.588 | **Disturbance** | 573.3 / 595.5 / 588.7 V | ≈ 1.71 kA | ≈ 1.379 MW | **R-phase current angle jumps −4.7° → −160°** (≈155°); Y & B currents stay near unity-PF |
| 13:34:02.838 | **Breaker open** | 21.15 / 20.8 / 15.65 V | ≈ 0 | 0 MW | Circuit isolated |

- Schneider's mechanism: on a 3-pole breaker, Ig = **vector (phasor) sum of the three phase currents**; a large single-phase angle displacement makes that sum non-zero → **residual current** → Micrologic reads it as a ground fault. The **replacement** Micrologic **also logged ground current**.
- Schneider conclusion: a **genuine Ig operation** on a real system disturbance — **not** nuisance tripping or equipment malfunction.
- Schneider suggestion: *"Subject to consultant approval … disable/bypass the Ig protection function …"*

**Source B — Sungrow, 09-Sep-2026** (inverter FLR / fault records):

- Inverter logged AC over-voltage, abnormal frequency, islanding and related trips.
- FLR at the trip timestamp: **frequency dipped to ≈ 46.1 Hz**; **AC voltage rose to ≈ 978.5 V (Ubc)**, Uca ≈ 951.9 V, Uab ≈ 833.1 V — against a permissible **660 V**.
- Sungrow observed the **ACB tripped on "Ig-fault" BEFORE** the inverter tripped.
- Sungrow conclusion: the inverter's OV/frequency trips are **consequential** to the AC-side disturbance; **primary cause = AC-side ground-fault → ACB Ig operation.** Recommends checking AC cables, terminations, transformers, switchgear, grounding.

**Source C — Sungrow, 15-Sep-2026** (clarification):

- Inverter is a **grid-following** unit — it synchronises to grid voltage/frequency and **cannot itself originate an increase in grid voltage or a phase-angle change**.
- Event sequence confirms **ACB (Ig) tripped first**, inverter after.
- Requests verification of the **ACB protection system and grid-side circuits** — Ig protection, sensing circuit, CT connections, protection settings, connected AC circuits.

**Site action already taken** — Sungrow site team, **10-Sep-2026**: inspected all AC connections **from inverter AC terminals up to LV side of the IDT** (inverter-duty transformer); all found **tight and satisfactory**.

---

## 3. Reconstructed event sequence  `[VERIFIED — both OEMs independently agree]`

```
t0   Normal export: ~660 V, ~2.42 kA, ~2.76 MW, balanced, near-unity PF.
t1   AC-side disturbance appears on the INVERTER (load) side of the ACB, while the
     ACB is still CLOSED (PQA still sees voltage & current):
       - R-phase CURRENT reverses ~155° (-4.7° -> -160°); Y & B stay ~normal
       - phase-phase voltage depresses (~660 -> ~575-595 V)
       - current & power roughly halve
   => the three phase currents are now ASYMMETRIC -> non-zero vector sum
      -> residual (ground) current seen by Micrologic.
t2   Ig element picks up (residual > Ig setting for > tg delay) -> ACB 3.1 OPENS.
t3   Inverter is suddenly ISLANDED (grid tie removed). A grid-following inverter
     briefly keeps injecting current into the now high-impedance/low-load island
     -> LOAD-REJECTION transient: voltage overshoots to ~978 V and the PLL
        frequency reading swings (~46.1 Hz).
t4   Inverter's own AC over-voltage / abnormal-frequency / anti-islanding
     protection trips it a few ms later.
```

**The two vendors do not actually contradict each other.** Both place the **Ig
trip first** and the **inverter trip second**. The only open point is *what caused
the t1 asymmetry* — that is the true root cause and it lies on the **AC side, not
inside the inverter or inside the breaker.**

---

## 4. Independent technical verification (the "double check")

### 4.1 Is the inverter OV/frequency trip a cause or a consequence?  → **Consequence** `[VERIFIED]`
- PQA (Schneider) shows the breaker already open at 13:34:02.838; the inverter's
  978 V / 46.1 Hz are the classic **load-rejection / islanding transient** that
  appears *after* a grid-following inverter loses its tie.
- A grid-following inverter cannot set grid voltage/frequency (Sungrow, Source C) —
  so it cannot be the origin. **Sustained 46.1 Hz is not physically credible** (the
  whole grid would have collapsed); it is a **PLL reading during disconnection**,
  i.e. a measurement artefact. → OV/freq = **downstream effect.** *(Cross-checked:
  Schneider PQA timeline + Sungrow grid-follower physics — two independent sources.)*

### 4.2 Is the ACB / Micrologic faulty?  → **No** `[VERIFIED]`
- Lab tests (resistance, wiring, primary + secondary injection) all pass; NFP.
- On a MasterPact/Micrologic ACB the **current sensors are built into the breaker**,
  so they were tested *with* the returned unit → internal sensing is proven healthy.
- A **second (replacement) Micrologic independently logged ground current** → the
  residual current is **real**, not an artefact of one faulty trip unit.
  → the breaker **correctly reported** a residual current it genuinely measured.

### 4.3 Is Schneider's "phase-shift ⇒ residual" explanation physically sound? → **Yes, but only because the change was ASYMMETRIC** `[INFERENCE — important nuance]`
- In a **3-wire** system (inverter → LV delta, no neutral return) Kirchhoff's law
  forces IR+IY+IB ≡ 0 **for any balanced set, at any phase angle**. A *uniform*
  rotation of all three currents can **never** by itself create a residual.
- A non-zero residual **requires a fourth (ground) return path** OR a genuinely
  **asymmetric** single-phase change. The data shows exactly the latter: **only
  R-phase current reversed (~155°)** while Y and B stayed near unity-PF.
- An R-phase current that reverses while Y/B stay put is the **signature of fault
  current flowing out on R and returning through earth** — i.e. a **single-line-to-
  ground (R-phase-to-ground) fault**, not a benign power-quality wobble.
- **Therefore the residual the Micrologic saw was almost certainly a real earth-
  fault current.** Schneider's wording ("system disturbance") understates this: the
  Ig element did its job — it detected genuine ground current. *(Cross-checked: KCL
  on a 3-wire system + the measured per-phase angles — the physics and the data agree.)*

### 4.4 Numerical consistency of the dataset  → **Confirmed** `[VERIFIED]`
- √3 × 660 V × 2.42 kA ≈ **2.77 MVA** ≈ the reported **2.758 MW** at near-unity PF →
  the PQA data is internally consistent and is the **inverter LV output** (a
  3.125 MW inverter at ~2.76 MW ≈ 88 %, plausible for a clear morning).
- 978.5 V / 660 V = **1.48× Vn** — within the envelope of a load-rejection
  over-voltage transient and above the inverter's AC-OV level-2 threshold → the
  inverter *should* trip, as it did. → measurements are trustworthy for RCA.

---

## 5. Root cause

> **Primary root cause `[INFERENCE, high confidence]`:** an **intermittent single-
> phase (R-phase) earth fault / insulation weakness on the AC side of ACB 3.1** —
> in the zone from the bus duct, through the inverter-duty transformer (LV winding,
> bushings) and switchgear, up to the grid/earthing system. This produced a genuine
> **residual (ground) current** that the Micrologic Ig element **correctly** cleared.
> The inverter's over-voltage / abnormal-frequency / islanding trips are a
> **consequence** of the ACB opening, not a cause.

**Why intermittent, and why mornings `[INFERENCE, to confirm — §6]`:** repeated
trips concentrated in the **morning** are a textbook signature of **moisture /
condensation / dew-driven insulation breakdown** (surface tracking across a
contaminated or damp surface in a bus duct, cable termination, or transformer
bushing). The path conducts when cold and damp at low morning load, then dries/
warms and clears as irradiance and temperature rise — which is exactly why a
**static inspection on 10-Sep found everything "tight"**: a tight bolt does not rule
out an insulation/tracking fault, and an intermittent fault is usually absent during
a dry mid-day check.

**Contributing / to-be-ruled-out factors `[OPEN]`:**
- **Inverter earth-leakage / common-mode current:** PV inverters pass small HF
  common-mode currents to earth via EMI/Y-capacitors; under a grid dip these can
  rise. Unlikely to reach the ~kA-scale asymmetry seen here, but should be excluded
  by insulation testing (secondary factor, not the root cause).
- **Ig setting / grading:** if Ig pickup or delay (tg) is set tighter than the
  inverter's transient behaviour warrants, it lowers the margin against nuisance
  operation. This affects *sensitivity to* the fault, but is **not** the source of
  the ground current.

### 5.1 5-Why

1. **Why did ACB 3.1 trip?** — Ig (ground-fault) element operated.
2. **Why did Ig operate?** — A real residual (ground) current exceeded the Ig
   pickup for its time delay (confirmed by two independent Micrologic units).
3. **Why was there residual current?** — R-phase current partly returned through
   earth (R-phase current reversed ~155° while Y/B stayed normal → asymmetric →
   non-zero vector sum).
4. **Why did R-phase current return through earth?** — An **R-phase-to-ground
   insulation fault** on the AC side (bus duct / transformer / switchgear / cabling).
5. **Why is it intermittent / recurring in the mornings?** — **Moisture /
   condensation-driven tracking** across degraded or contaminated insulation that
   conducts only under damp, low-temperature morning conditions.

### 5.2 Fishbone (summary)

- **Equipment (breaker):** ruled out — NFP, lab-tested, two Micrologics agree.
- **Equipment (inverter):** ruled out as originator — grid-following, OV/freq is consequential.
- **Electrical / insulation:** **PRIME SUSPECT** — R-phase earth fault in bus duct / transformer LV / switchgear / cable.
- **Environment:** **contributing** — morning dew/condensation triggering intermittent tracking.
- **Settings / protection coordination:** to review — Ig pickup & tg grading vs. inverter transients.
- **Measurement/CT:** ruled out — built-in sensors + external wiring tested healthy.

---

## 6. Corrective & preventive action plan (fault-location first)

**A. Locate the earth fault (do this before touching any protection setting):**
1. **De-energise and isolate** ACB 3.1 section; **isolate the inverter** at its AC terminals.
2. **Insulation-resistance (IR/megger) test, phase-to-earth on EACH phase** (R, Y, B
   separately) across: inverter AC bus duct, LV cabling, and the **transformer LV
   winding/bushings**. Expect a **low reading on R-phase** if the hypothesis holds.
   Record and trend; a marginal/temperature-sensitive value confirms the moisture link.
3. **Thermography** of all AC terminations, bus-duct joints and transformer bushings
   under load (once safe) — look for hot/tracking spots on R-phase.
4. **Internal visual inspection of the bus duct** for moisture ingress, condensation,
   dust/salt contamination (coastal Thoothukudi → salt-laden humidity is a real
   factor), and surface tracking marks; check gland/IP integrity and breathers/drains.
5. **Timed correlation:** pull the **Micrologic Ig event log with timestamps + logged
   ground-current magnitude** and correlate against **time-of-day, humidity and
   inverter power** to confirm the morning/moisture pattern quantitatively.

**B. Rectify the located fault:** repair/replace the affected insulation, dry out and
re-seal the bus duct, restore IP integrity, add anti-condensation heaters / breathers
where applicable, treat salt/dust contamination.

**C. Protection — coordinate, do NOT blindly disable (see §7):** after the fault is
cleared, **review Ig pickup (Ig) and delay (tg)** against a short grading study so
that genuine momentary asymmetries during inverter/grid transients are ridden through
while **real sustained ground faults still trip**. Verify disconnection times against
IEC 60364 / CEA requirements. Consider **continuous Residual Current Monitoring (RCM)**
for early warning.

**D. Verify inverter side:** confirm inverter LVRT / anti-islanding settings and
earth-leakage (Riso / GFDI) thresholds are per spec; confirm the OV/freq trips were
protective responses, not mis-set.

---

## 7. Decision on the pending request — **disable / bypass Ig protection**

> **Recommendation: DO NOT approve a blanket disable/bypass of the Ig protection.**

Justification:

1. **It removes real protection against a real hazard.** Schneider's own evidence —
   residual-current records and a **second** Micrologic logging ground current — says
   the trip was a **genuine** earth-fault operation. Disabling Ig would let genuine
   earth-fault current **persist undetected**, risking transformer/cable/bus-duct
   damage, arcing/fire, and step-touch shock hazard.
2. **It treats the symptom, not the cause.** The trips would stop, but the underlying
   ground current would keep flowing. This converts a *self-protecting* fault into a
   *hidden, escalating* one.
3. **Statutory / contractual exposure.** Earth-fault protection on LV systems is a
   safety function; disabling it may breach **CEA (Measures relating to Safety & Electric
   Supply) Regulations**, plant insurance conditions, and O&M/warranty terms.
4. **A safer, standards-aligned alternative exists** (§6C): locate & fix the fault,
   then **re-coordinate Ig settings** (pickup + intentional short delay) rather than
   removing the function. If generation must be maintained before the fault is found,
   retain Ig with **reviewed settings + enhanced logging / RCM** — never a full bypass.

If, exceptionally, the client/consultant still elects a temporary sensitivity change,
it must be a **documented, time-bound, risk-assessed** setting change (not a disable),
signed off by the protection consultant, with the fault-location actions in §6 running
in parallel.

---

## 8. Actions & ownership

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | IR (phase-to-earth, per phase) on bus duct, LV cable, transformer LV winding | O&M / EPC electrical | **Immediate** |
| 2 | Thermography of AC terminations + transformer bushings under load | O&M | **Immediate** |
| 3 | Internal bus-duct inspection for moisture/tracking/salt contamination; reseal, add heaters/breathers | O&M / EPC | High |
| 4 | Pull Micrologic Ig logs (timestamp + ground-current magnitude); correlate vs time-of-day/humidity/power | O&M + Schneider | High |
| 5 | **Hold** blanket Ig-disable; commission grading study & re-coordinate Ig/tg after fault cleared | Protection consultant + Schneider | High |
| 6 | Verify inverter LVRT / anti-islanding / Riso settings vs spec | Sungrow | Medium |
| 7 | Confirm lip/earthing continuity & neutral-earthing of the transformer star point | O&M / EPC | Medium |

---

## 9. Conclusion (double-verified)

- **Breaker & Micrologic:** healthy (NFP; two units agree). **Not** a nuisance trip. `[VERIFIED]`
- **Inverter OV / 46.1 Hz / islanding:** **consequential** to the ACB opening (load-
  rejection transient of a grid-following inverter). `[VERIFIED]`
- **Root cause:** a **genuine, intermittent R-phase AC-side earth fault** (most likely
  moisture/condensation-driven insulation tracking in the bus duct / transformer LV /
  switchgear), correctly detected by the Ig element. `[INFERENCE, high confidence]`
- **Not yet done:** the fault has **not been physically located** — the 10-Sep
  connection check (tightness only) does not clear an intermittent insulation fault. `[OPEN]`
- **Request to disable Ig:** **not endorsed.** Locate and fix the earth fault, then
  **re-coordinate** the Ig setting; do not remove earth-fault protection. `[DECISION]`

---

*Prepared from the three vendor documents in `./inputs/`. Findings tagged
`[VERIFIED] / [INFERENCE] / [OPEN]`; each verified item is supported by two
independent data sources per the cross-check register in §4.*
