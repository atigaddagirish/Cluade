# Telangana rain proxy — option 3 for Weather Watch

Telangana's official state network (TSDPS/TGDPS) publishes **dense mandal-level
AWS data** (rainfall, temperature, humidity, wind, pressure) at
`tgdps.telangana.gov.in` / `tsdps.telangana.gov.in`. But that server **firewalls
out non-Indian / datacenter IPs** and its pages send **no CORS headers**, so
neither the GitHub-Actions relay (US cloud IP) nor the phone browser can read it
directly. This tiny **zero-dependency Node proxy**, run from an *India-reachable*
host, fetches those pages and re-serves them as **CORS-open JSON** the app can use.

## ⚠️ Do the reachability test FIRST (before any real setup)
The big unknown is whether the host you deploy on can reach TSDPS at all — their
firewall may block **all** datacenter IPs, not just non-Indian ones. So:

1. Run the proxy somewhere and hit `/health`:
   ```
   node proxy.mjs         # needs Node 18+
   curl http://localhost:8080/health
   ```
2. Read the result:
   - `{"reachable": true, ...}` → that host works. 🎉 Continue below.
   - `timeout` / `reachable: false` → that host's IP is blocked. Try a different
     host (see options), ideally a **residential Indian connection**.

**Tip:** your own laptop/phone on home Indian internet *already* reaches TSDPS
(that's where you saw the data), so running it there proves the parser instantly.
A cloud host is only for keeping it always-on.

## Where to host (most→least likely to work)
1. **A device on your home/office network** (old Android via Termux, a Raspberry
   Pi, a mini-PC) exposed with a free tunnel — **guaranteed** residential Indian
   IP, so it *will* reach TSDPS:
   ```
   # on the device
   node proxy.mjs
   # in another shell — free public HTTPS URL via Cloudflare Tunnel:
   cloudflared tunnel --url http://localhost:8080
   ```
   Use the `https://….trycloudflare.com` URL it prints. (ngrok works too.)
2. **A cloud VM/serverless in an Indian region** — may work if TSDPS only geo-blocks:
   - Google **Cloud Run**, region `asia-south1` (Mumbai): `gcloud run deploy tg-rain --source . --region asia-south1 --allow-unauthenticated`
   - **Oracle Cloud** always-free VM, Hyderabad/Mumbai region: run `node proxy.mjs` behind the VM's public IP.
   - AWS **Lambda** `ap-south-1` + Function URL (wrap the handler) — Mumbai IPs.
   Deploy, then `curl https://YOUR-URL/health`. If `reachable:true`, you're set.

## Once `/health` is green
Grab a sample so I can finalise the app integration:
```
curl "https://YOUR-PROXY-URL/rain?d=4"     # a district's mandal table as JSON
curl "https://YOUR-PROXY-URL/live"         # today's state live rain
```
Send me that JSON (or the raw page via `/raw`). Then I:
- confirm the exact column layout the parser returns,
- add a **coordinate → Telangana mandal** lookup, and
- add a **"Telangana state gauge"** card to Weather Watch that appears for
  Telangana locations, reading from your proxy URL (set in ⚙ Settings).

## Endpoints
| Route | Returns |
|---|---|
| `GET /health` | `{reachable, status, ms, bytes}` — can this host reach TSDPS? |
| `GET /rain?d=<districtId>` | parsed mandal rainfall table (`tgdps mandaldata.jsp?s1=<id>`) |
| `GET /live` | parsed `tsdps liverain.jsp` |
| `GET /raw?u=<tsdps-url>` | raw HTML of an allow-listed TSDPS page (debugging) |

All responses send `Access-Control-Allow-Origin: *`. Set `TG_INSECURE=1` only if
`/health` fails with a TLS certificate error (traffic stays HTTPS-encrypted).

## Notes
- TSDPS data is **mandal-aggregated**, not the individual "Lanco Hills" sensor —
  so you'll get the Manikonda/Gandipet *mandal* rainfall, which is still far more
  local than IMD's nearest gauge for Telangana points.
- Keep this proxy pointed only at TSDPS/TGDPS (it's allow-listed) — it's a
  read-only pass-through, no keys or personal data involved.
