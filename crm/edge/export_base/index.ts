import "jsr:@supabase/functions-js/edge-runtime.d.ts";

// Exporta segmentos da leads_master como CSV. Auth por token (?k=). service_role
// fica no servidor (env) — nunca no painel. Segmentos são whitelist (sem injeção).
// Rotacione trocando TOKEN e redeployando.
const TOKEN = "exp-r1b4s-7h2k9x4m3q";

const COLS = "lead_id,nome,telefone_norm,email,origem,origem_detalhe,optin_sms,optin_ligacao,optin_telegram,telegram_id,telegram_username,data_optin";

// segmento -> filtro PostgREST (vazio = base inteira)
const SEGS: Record<string, string> = {
  todos: "",
  com_telefone: "telefone_norm=not.is.null",
  com_email: "email=not.is.null",
  sms: "optin_sms=is.true",
  ligacao: "optin_ligacao=is.true",
  email_consent: "email=not.is.null&optin_ligacao=is.true",
  com_telegram: "telegram_id=not.is.null",
  ponte: "telefone_norm=not.is.null&telegram_id=not.is.null",
  sem_consentimento: "optin_sms=is.false&optin_ligacao=is.false&telefone_norm=not.is.null",
};

const PAGE = 10000;

Deno.serve(async (req: Request) => {
  const url = new URL(req.url);
  if (url.searchParams.get("k") !== TOKEN) return new Response("nao autorizado", { status: 401 });
  const seg = url.searchParams.get("seg") || "todos";
  if (!(seg in SEGS)) return new Response("segmento invalido", { status: 400 });

  const base = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  let q = `${base}/rest/v1/leads_master?select=${COLS}&order=criado_em.asc`;
  if (SEGS[seg]) q += `&${SEGS[seg]}`;

  // paginação guiada pelo total real (count=exact na 1a página); passo = o que o
  // servidor de fato devolveu, então não trunca mesmo se houver limite de linhas menor.
  let offset = 0, out = "", total = Infinity;
  while (offset < total) {
    const r = await fetch(q, {
      headers: {
        apikey: key, Authorization: `Bearer ${key}`, Accept: "text/csv",
        "Range-Unit": "items", Range: `${offset}-${offset + PAGE - 1}`,
        Prefer: offset === 0 ? "count=exact" : "count=none",
      },
    });
    if (!r.ok && r.status !== 206) return new Response("erro ao exportar: " + (await r.text()), { status: 500 });
    const txt = await r.text();
    const nl = txt.indexOf("\n");
    if (offset === 0) { out = txt; }
    else if (nl >= 0) { const body = txt.slice(nl + 1); if (body.length) out += (out.endsWith("\n") ? "" : "\n") + body; }

    const cr = r.headers.get("content-range") || ""; // "0-9999/176428" ou "0-9999/*"
    const m = cr.match(/^(\d+)-(\d+)\/(\d+|\*)/);
    if (!m) break;
    const end = parseInt(m[2], 10);
    if (m[3] !== "*") total = parseInt(m[3], 10);
    if (end < offset) break;        // nada novo
    offset = end + 1;
    if (offset > 2000000) break;    // trava de segurança
  }

  const fn = `base_${seg}_${new Date().toISOString().slice(0, 10)}.csv`;
  return new Response(out, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${fn}"`,
      "Cache-Control": "no-store",
    },
  });
});
