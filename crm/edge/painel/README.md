# Edge Function `painel`

Dashboard vivo do funil lead_id, servido pelo Supabase (experts-painel).

- URL: `https://jqfpfkublwshpgtqkmeo.supabase.co/functions/v1/painel?k=<TOKEN>`
- Lê os agregados via RPC `painel_dados()` com a `service_role` (injetada como
  env var na edge function — nunca vai pro cliente). Só agregados, zero PII.
- `verify_jwt = false` + gate por token de query (`?k=`). Para rotacionar o
  token: troque a constante `TOKEN` no `index.ts` e redeploy.
- Atualiza sozinho a cada 60s (`<meta refresh>`), sem biblioteca externa.

Deploy (via MCP Supabase `deploy_edge_function`, ou CLI):
`supabase functions deploy painel --no-verify-jwt`

O `index.ts` neste diretório é a fonte da versão deployada.

## Nota (03/09): render bloqueado

O Supabase serve respostas de edge function como `text/plain`, então o
navegador exibe o HTML como texto cru em vez de renderizar. Nao ha header
que contorne (politica da plataforma). A `painel_dados()` (RPC) continua
util como fonte de dados; para visualizacao o painel vive como Artifact
(`crm/painel_artifact.html`), atualizado sob demanda. Se um dia precisar
de painel vivo hospedado, o caminho e Vercel/Cloudflare Pages lendo a RPC,
ou um workflow n8n que responde HTML.
