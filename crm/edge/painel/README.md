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
