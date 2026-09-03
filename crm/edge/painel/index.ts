import "jsr:@supabase/functions-js/edge-runtime.d.ts";

// Painel CRM lead_id — dashboard vivo, so agregados (zero PII).
// Acesso por token de query: ?k=<TOKEN>. Rotacione trocando a constante e redeployando.
const TOKEN = "pnl-r1b4s-9x7k2m8q4z";

const fmt = (n: number) => (n ?? 0).toLocaleString("pt-BR");
const pct = (a: number, b: number) => (b > 0 ? Math.round((a / b) * 1000) / 10 : 0);

function esc(s: string) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));
}

function tile(label: string, value: string, sub = "", accent = false) {
  return `<div class="tile${accent ? " ac" : ""}"><div class="tv">${value}</div><div class="tl">${esc(label)}</div>${sub ? `<div class="ts">${esc(sub)}</div>` : ""}</div>`;
}

function bar(nome: string, val: number, max: number, extra: string, tone: string) {
  const w = max > 0 ? Math.max(2, Math.round((val / max) * 100)) : 0;
  return `<div class="row"><div class="rn">${esc(nome)}</div><div class="rb"><div class="rf ${tone}" style="width:${w}%"></div></div><div class="rx">${extra}</div></div>`;
}

Deno.serve(async (req: Request) => {
  const url = new URL(req.url);
  if (url.searchParams.get("k") !== TOKEN) {
    return new Response("nao autorizado", { status: 401 });
  }

  const base = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const r = await fetch(`${base}/rest/v1/rpc/painel_dados`, {
    method: "POST",
    headers: { "Content-Type": "application/json", apikey: key!, Authorization: `Bearer ${key}` },
    body: "{}",
  });
  if (!r.ok) return new Response("erro ao ler dados: " + (await r.text()), { status: 500 });
  const d = await r.json();

  const b = d.base, c = d.canais;
  const capMax = Math.max(...d.captura.map((g: any) => g.membros), 1);
  const capturados = d.captura.reduce((s: number, g: any) => s + (g.deram_telefone || 0), 0);
  const membrosTotais = d.captura.reduce((s: number, g: any) => s + g.membros, 0);

  const capRows = d.captura.map((g: any) =>
    bar(g.nome, g.membros, capMax,
      `<b>${fmt(g.deram_telefone)}</b> / ${fmt(g.membros)} <span class="mut">(${pct(g.deram_telefone, g.membros)}%)</span>`,
      g.deram_telefone > 0 ? "ok" : "idle")).join("");

  const covRows = d.cobertura.map((g: any) =>
    bar(g.nome, Number(g.pct), 100,
      `${g.pct}% <span class="mut">${fmt(g.conhecidos)}/${fmt(g.membros)}</span>`,
      Number(g.pct) === 0 ? "warn" : "ac")).join("");

  const origens = d.origens.map((o: any) =>
    `<div class="orow"><span>${esc(o.origem)}</span><b>${fmt(o.n)}</b></div>`).join("");

  const gerado = new Date(d.gerado_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });

  const html = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>Painel · lead_id</title>
<style>
:root{--bg:#0e1116;--card:#171b22;--line:#232833;--tx:#e6e9ef;--mut:#8b94a3;--ac:#4f8cff;--ok:#2fbf71;--warn:#e0574a;--idle:#3a4150}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:24px;max-width:1100px;margin:0 auto}
h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:13px;margin-bottom:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:8px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.tile.ac{border-color:var(--ac)}
.tv{font-size:26px;font-weight:700;letter-spacing:-.5px}.tl{color:var(--mut);font-size:12px;margin-top:4px}.ts{color:var(--mut);font-size:11px;margin-top:2px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.5px;color:var(--mut);margin:28px 0 12px;font-weight:600}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.row{display:grid;grid-template-columns:210px 1fr 190px;align-items:center;gap:12px;padding:6px 0}
.rn{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rb{background:#0c0f14;border-radius:6px;height:14px;overflow:hidden}
.rf{height:100%;border-radius:6px}.rf.ok{background:var(--ok)}.rf.ac{background:var(--ac)}.rf.warn{background:var(--warn)}.rf.idle{background:var(--idle)}
.rx{font-size:12px;text-align:right;color:var(--tx)}.mut{color:var(--mut)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:720px){.two{grid-template-columns:1fr}.row{grid-template-columns:120px 1fr;grid-template-rows:auto auto}.rx{grid-column:2}}
.orow{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line);font-size:13px}.orow:last-child{border:0}
footer{color:var(--mut);font-size:12px;margin-top:24px;text-align:center}
</style></head><body>
<h1>Painel · ponte lead_id</h1>
<div class="sub">telefone (CRM) ↔ telegram_id · atualiza a cada 60s · gerado ${esc(gerado)}</div>

<h2>Base</h2>
<div class="grid">
${tile("leads totais", fmt(b.total))}
${tile("com telefone", fmt(b.com_telefone))}
${tile("com e-mail", fmt(b.com_email))}
${tile("com telegram", fmt(b.com_telegram))}
${tile("ponte completa", fmt(b.ponte), "telefone + telegram", true)}
</div>

<h2>Disparável por canal (com consentimento)</h2>
<div class="grid">
${tile("SMS", fmt(c.sms))}
${tile("ligação", fmt(c.ligacao))}
${tile("e-mail", fmt(c.email))}
${tile("opt-in Telegram", fmt(c.telegram_optin), "confirmados no bot", true)}
${tile("sem consentimento", fmt(b.sem_consentimento), "não disparável")}
</div>

<h2>Captura nos grupos — telefone confirmado / membros</h2>
<div class="panel">${capRows}
<div class="row" style="border-top:1px solid var(--line);margin-top:8px;padding-top:10px"><div class="rn"><b>Total</b></div><div></div><div class="rx"><b>${fmt(capturados)}</b> / ${fmt(membrosTotais)} <span class="mut">(${pct(capturados, membrosTotais)}%)</span></div></div>
</div>

<div class="two">
<div><h2>Cobertura conhecida por grupo</h2><div class="panel">${covRows}</div></div>
<div><h2>Top origens da base</h2><div class="panel">${origens}</div></div>
</div>

<footer>experts-painel · atualização automática · dados agregados, sem PII</footer>
</body></html>`;

  return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } });
});
