// Telangana TSDPS/TGDPS rainfall proxy — zero dependencies (Node 18+).
//
// Why this exists: Telangana's state weather network (dense mandal-level AWS:
// rainfall, temp, humidity, wind, pressure) is published at
// tgdps.telangana.gov.in / tsdps.telangana.gov.in, but that server firewalls
// out non-Indian / datacenter IPs and its pages send no CORS headers — so
// neither a GitHub-Actions relay (US cloud IP) nor the phone browser can read
// it directly. This tiny proxy, run from an INDIA-reachable host, fetches those
// pages server-side and re-serves them as CORS-open JSON that Weather Watch can
// consume.
//
// Run:   node proxy.mjs            (listens on $PORT, default 8080)
// Test:  curl http://localhost:8080/health
//        curl "http://localhost:8080/rain?d=4"
//
// Endpoints (all send Access-Control-Allow-Origin: *):
//   GET /health        -> {reachable, status, ms, bytes}  (can THIS host reach TSDPS?)
//   GET /rain?d=<id>   -> parsed mandal rainfall table from tgdps mandaldata.jsp?s1=<id>
//   GET /live          -> parsed tsdps liverain.jsp
//   GET /raw?u=<url>   -> raw HTML of an allow-listed TSDPS page (for debugging/parser work)

import http from 'node:http';
import https from 'node:https';

const PORT = process.env.PORT || 8080;
const TIMEOUT = 25000;
// Some Indian govt hosts ship an incomplete TLS chain; set TG_INSECURE=1 only if
// /health fails with a certificate error (traffic is still HTTPS-encrypted).
const INSECURE = process.env.TG_INSECURE === '1';

const HOSTS = {
  tgdps: 'https://tgdps.telangana.gov.in',
  tsdps: 'https://www.tsdps.telangana.gov.in',
};
const UA = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36';

function fetchUpstream(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: { 'User-Agent': UA, 'Referer': HOSTS.tgdps + '/', 'Accept': 'text/html' },
      rejectUnauthorized: !INSECURE,
      timeout: TIMEOUT,
    }, res => {
      let body = '';
      res.setEncoding('utf8');
      res.on('data', c => { body += c; if (body.length > 4_000_000) req.destroy(); });
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });
    req.on('timeout', () => req.destroy(new Error('upstream timeout (host likely blocks this IP)')));
    req.on('error', reject);
  });
}

// Very small HTML-table parser: returns the largest table as headers + rows.
function parseTables(html) {
  const tables = [...html.matchAll(/<table[\s\S]*?<\/table>/gi)].map(m => m[0]);
  if (!tables.length) return { headers: [], rows: [] };
  const table = tables.sort((a, b) => b.length - a.length)[0];   // the biggest table
  const trs = [...table.matchAll(/<tr[\s\S]*?<\/tr>/gi)].map(m => m[0]);
  const cells = tr => [...tr.matchAll(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi)]
    .map(c => c[1].replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim());
  const rows = trs.map(cells).filter(r => r.length);
  let headers = [];
  if (rows.length && rows[0].some(c => /rain|mandal|district|normal|temp|humid|wind|date/i.test(c))) {
    headers = rows.shift();
  }
  return { headers, rows };
}

function send(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Cache-Control': 'public, max-age=300',
  });
  res.end(body);
}

http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  if (req.method === 'OPTIONS') { res.writeHead(204, { 'Access-Control-Allow-Origin': '*' }); return res.end(); }

  try {
    if (u.pathname === '/health') {
      const t = Date.now();
      const r = await fetchUpstream(`${HOSTS.tgdps}/mandaldata.jsp?s1=4`);
      return send(res, 200, { reachable: r.status === 200, status: r.status,
        ms: Date.now() - t, bytes: r.body.length,
        note: r.status === 200 ? 'this host can reach TSDPS' : 'reached but non-200' });
    }
    if (u.pathname === '/rain') {
      const d = (u.searchParams.get('d') || '4').replace(/\D/g, '') || '4';
      const r = await fetchUpstream(`${HOSTS.tgdps}/mandaldata.jsp?s1=${d}`);
      const p = parseTables(r.body);
      return send(res, 200, { ok: r.status === 200, source: `tgdps mandaldata.jsp?s1=${d}`,
        status: r.status, headers: p.headers, rows: p.rows.slice(0, 400), rawBytes: r.body.length });
    }
    if (u.pathname === '/live') {
      const r = await fetchUpstream(`${HOSTS.tsdps}/liverain.jsp`);
      const p = parseTables(r.body);
      return send(res, 200, { ok: r.status === 200, source: 'tsdps liverain.jsp',
        status: r.status, headers: p.headers, rows: p.rows.slice(0, 400), rawBytes: r.body.length });
    }
    if (u.pathname === '/raw') {                       // debugging aid (allow-listed hosts only)
      const target = u.searchParams.get('u') || `${HOSTS.tgdps}/mandaldata.jsp?s1=4`;
      if (!Object.values(HOSTS).some(h => target.startsWith(h)))
        return send(res, 400, { error: 'url not on TSDPS/TGDPS allow-list' });
      const r = await fetchUpstream(target);
      res.writeHead(r.status, { 'Content-Type': 'text/plain; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
      return res.end(r.body.slice(0, 200000));
    }
    return send(res, 200, { service: 'telangana-rain-proxy',
      endpoints: ['/health', '/rain?d=<districtId>', '/live', '/raw?u=<tsdps-url>'] });
  } catch (e) {
    return send(res, 502, { error: String(e.message || e),
      hint: 'timeout/connection-refused usually means this host\'s IP is firewalled by TSDPS — try a residential Indian connection.' });
  }
}).listen(PORT, () => console.log(`telangana-rain-proxy on :${PORT}`));
