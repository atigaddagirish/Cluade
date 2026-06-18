#!/usr/bin/env python3
"""
Regression / cross-check harness for the trapezoidal lipped HAT IS 801 calculator.

Source of truth for the section-property engine in index.html (computeProps).
Run:  python3 validate.py
After ANY change to the JS engine, confirm the printed values still match the
targets baked into CLAUDE.md (A=224.0, Ixx=161637, Ztop=4244, Zbot=5065, dN=36.5mm).

Method: exact thin-walled polyline (per-segment A, orientation-aware Ixx/Iyy,
parallel axis). Mirrors index.html computeProps() exactly.
"""
import math

# ---- geometry (drawing; lip UP-and-out) ----
B1, H, theta, F, Lp, beta, t = 40.0, 70.0, 75.0, 22.0, 10.0, 45.0, 0.90
Fy, E = 550.0, 200000.0
# ---- governing load (working) ----
w_net, span, defDiv = 0.981, 3100.0, 180.0   # kN/m, mm, L/180
Lb, Cb = 3100.0, 1.0

def vertices():
    half = B1 / 2
    run = H / math.tan(math.radians(theta))
    wb = half + run                 # web base half-x
    fe = wb + F                     # foot end half-x (feet outward)
    ldx = Lp * math.cos(math.radians(beta))
    ldy = Lp * math.sin(math.radians(beta))   # +ve = lip UP
    lt = fe + ldx
    V = [(-lt, ldy), (-fe, 0), (-wb, 0), (-half, H),
         (half, H), (wb, 0), (fe, 0), (lt, ldy)]
    return V, dict(half=half, run=run, wb=wb, fe=fe, lt=lt, ldy=ldy)

def props():
    V, g = vertices()
    segs = []
    for i in range(len(V) - 1):
        x1, y1 = V[i]; x2, y2 = V[i + 1]
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 1e-9:
            continue
        segs.append((L, (x1 + x2) / 2, (y1 + y2) / 2, math.atan2(y2 - y1, x2 - x1), i))
    A = sum(s[0] * t for s in segs)
    yc = sum(s[0] * t * s[2] for s in segs) / A
    Ixx = Iyy = 0.0
    for L, xm, ym, phi, i in segs:
        a = L * t
        Ixx += (t * L**3 / 12) * math.sin(phi)**2 + (L * t**3 / 12) * math.cos(phi)**2 + a * (ym - yc)**2
        Iyy += (t * L**3 / 12) * math.cos(phi)**2 + (L * t**3 / 12) * math.sin(phi)**2 + a * xm**2
    ymin = min(v[1] for v in V); ymax = max(v[1] for v in V)
    ytop, ybot = ymax - yc, yc - ymin
    Ztop, Zbot = Ixx / ytop, Ixx / ybot
    # compression flange (feet+lips, idx 0,1,5,6) about x=0
    Acf = Iycf = 0.0
    for L, xm, ym, phi, i in segs:
        if i in (0, 1, 5, 6):
            a = L * t; Acf += a
            Iycf += (t * L**3 / 12) * math.cos(phi)**2 + (L * t**3 / 12) * math.sin(phi)**2 + a * xm**2
    rycf = math.sqrt(Iycf / Acf)
    J = sum(s[0] for s in segs) * t**3 / 3
    return dict(A=A, yc=yc, Ixx=Ixx, Iyy=Iyy, Ztop=Ztop, Zbot=Zbot,
                rycf=rycf, J=J, wslant=math.hypot(g['run'], H))

def fbLTB(Fe, Fy):
    if Fe >= 2.78 * Fy: return 0.6 * Fy
    if Fe >= 0.56 * Fy: return (10 * Fy / 9) * (1 - Fy / (5.04 * Fe))
    return Fe / 1.67

def main():
    p = props()
    Fb, Fb_wl = 0.6 * Fy, 0.6 * Fy * 4 / 3
    M = w_net * span**2 / 8 / 1e6                     # kNm
    f_comp = M * 1e6 / p['Zbot']; f_tens = M * 1e6 / p['Ztop']
    f_gov = max(f_comp, f_tens)
    d = 5 * w_net * span**4 / (384 * E * p['Ixx'])
    Fe = Cb * math.pi**2 * E / ((Lb / p['rycf'])**2)
    FbL = min(Fb, fbLTB(Fe, Fy))
    wt = p['wslant'] / t; l1 = 2.89 * math.sqrt(E / Fy); l2 = 5.34 * math.sqrt(E / Fy)
    Fv = 0.4 * Fy if wt <= l1 else (0.664 * math.sqrt(Fy * E) / wt if wt <= l2 else 0.905 * E / wt**2)
    Vcap = 2 * Fv * H * t / 1000; Vmax = w_net * span / 1000 / 2

    print("=== SECTION PROPERTIES (regression targets) ===")
    for k, tgt in [('A', 224.0), ('yc', 31.91), ('Ixx', 161637), ('Iyy', 295330),
                   ('Ztop', 4244), ('Zbot', 5065), ('rycf', 55.0)]:
        print(f"  {k:5} = {p[k]:>10.2f}   target {tgt}")
    print(f"  J     = {p['J']:.1f}   web slant = {p['wslant']:.1f}")
    print()
    print("=== IS 801 VERDICT (uplift, w=0.981 kN/m, L=3.1 m) ===")
    print(f"  Bending : f_gov={f_gov:.1f} MPa (tens-top {f_tens:.1f}, comp-foot {f_comp:.1f}) "
          f"vs Fb(+1/3)={Fb_wl:.0f}  ->  UR {f_gov / Fb_wl * 100:.0f}%   [Cl.6.1]")
    print(f"  Shear   : V={Vmax:.2f} kN vs Vc={Vcap:.2f} kN  ->  UR {Vmax / Vcap * 100:.0f}%   [Cl.7]")
    print(f"  LTB     : Fe={Fe:.0f} MPa (2.78Fy={2.78*Fy:.0f}), Fb_LTB={FbL:.0f} -> "
          f"{'no reduction' if FbL >= Fb else 'REDUCES'}   [Cl.6.2]")
    print(f"  Deflect : d={d:.1f} mm = L/{span/d:.0f} vs L/{int(defDiv)}={span/defDiv:.1f} mm  ->  "
          f"UR {d / (span / defDiv) * 100:.0f}%   [{'FAIL' if d > span/defDiv else 'PASS'}]")

if __name__ == "__main__":
    main()
