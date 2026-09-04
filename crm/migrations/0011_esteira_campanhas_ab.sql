-- Amarração pré-start da rotação de bots + campanhas/eventos + teste A/B.
-- Baseado no levantamento "Rotação Segura de Bots no Telegram" (Ilha B, opt-in).
-- Tudo se liga pelo lead_id. RLS travado (service_role bypassa; anon/auth sem acesso).

-- Esteira de bots (pai/filhos/reservas). Tokens ficam em app_config (token_ref).
create table if not exists public.bots(
  id         text primary key,
  nome       text,
  papel      text not null default 'filho' check (papel in ('pai','filho','reserva')),
  variante   text,
  status     text not null default 'ativo' check (status in ('ativo','reserva','quarentena','restrito','inativo')),
  token_ref  text,
  observacao text,
  criado_em  timestamptz not null default now()
);
alter table public.bots enable row level security;
alter table public.bots force row level security;
revoke all on public.bots from anon, authenticated;
insert into public.bots(id,nome,papel,status,token_ref) values
  ('pai','@Ribasadm1_bot','pai','ativo','telegram_bot_token')
  on conflict (id) do nothing;

-- Campanhas / eventos aplicados, com snapshot da base congelado no momento.
create table if not exists public.campanhas(
  id           uuid primary key default gen_random_uuid(),
  nome         text not null,
  objetivo     text,
  tipo         text not null default 'telegram_captura'
               check (tipo in ('telegram_captura','telegram_broadcast','crm_sms','crm_email','crm_ligacao','outro')),
  variante     text,
  copy_texto   text,
  bot_id       text references public.bots(id),
  canal        text,
  payload      text,
  status       text not null default 'planejada'
               check (status in ('planejada','ativa','concluida','pausada')),
  base_snapshot jsonb,
  criado_em    timestamptz not null default now(),
  iniciada_em  timestamptz,
  concluida_em timestamptz
);
alter table public.campanhas enable row level security;
alter table public.campanhas force row level security;
revoke all on public.campanhas from anon, authenticated;

-- Disparo por lead (broadcast/CRM). Captura de grupo usa telegram_capturas.
create table if not exists public.disparos(
  id          bigint generated always as identity primary key,
  campanha_id uuid references public.campanhas(id),
  lead_id     uuid,
  bot_id      text,
  status      text not null default 'enviado'
              check (status in ('enviado','entregue','bloqueado','denuncia','erro','convertido')),
  em          timestamptz not null default now(),
  unique (campanha_id, lead_id)
);
create index if not exists disparos_camp_idx on public.disparos (campanha_id);
create index if not exists disparos_lead_idx on public.disparos (lead_id);
alter table public.disparos enable row level security;
alter table public.disparos force row level security;
revoke all on public.disparos from anon, authenticated;

-- Liga a captura ao A/B (variante) e à campanha.
alter table public.telegram_capturas add column if not exists variante text;
alter table public.telegram_capturas add column if not exists campanha_id uuid;

-- capturar_start aceita payload com variante: 'g7' ou 'g7_vA'.
create or replace function public.capturar_start(
  p_telegram_id bigint, p_codigo text, p_username text default null, p_nome text default null
) returns jsonb language plpgsql security definer set search_path='' as $$
declare g public.telegram_grupos%rowtype; v_lead uuid; v_tel text; v_cod text; v_var text;
begin
  if p_telegram_id is null then return jsonb_build_object('status','sem_telegram_id'); end if;
  v_cod := split_part(p_codigo, '_v', 1);
  v_var := nullif(split_part(p_codigo, '_v', 2), '');
  select * into g from public.telegram_grupos t where t.codigo = v_cod;
  if not found then
    insert into public.telegram_capturas (telegram_id, grupo_codigo, evento, resultado, variante)
    values (p_telegram_id, v_cod, 'start', 'grupo_invalido', v_var);
    return jsonb_build_object('status','grupo_invalido');
  end if;
  select l.lead_id, l.telefone_norm into v_lead, v_tel from public.leads_master l where l.telegram_id = p_telegram_id;
  if v_lead is null then
    insert into public.leads_master (telegram_id, telegram_username, nome, origem, origem_detalhe)
    values (p_telegram_id, nullif(p_username,''), nullif(p_nome,''), 'telegram_grupo', g.nome)
    returning lead_id into v_lead;
  else
    update public.leads_master l
       set telegram_username = coalesce(l.telegram_username, nullif(p_username,'')),
           nome = coalesce(l.nome, nullif(p_nome,'')) where l.lead_id = v_lead;
  end if;
  insert into public.telegram_capturas (telegram_id, grupo_codigo, evento, lead_id, resultado, variante)
  values (p_telegram_id, v_cod, 'start', v_lead, case when v_tel is not null then 'ja_tinha_telefone' else 'ok' end, v_var);
  return jsonb_build_object('status','ok','lead_id',v_lead,'grupo',g.nome,'variante',v_var,'ja_tem_telefone', v_tel is not null);
end; $$;
revoke all on function public.capturar_start(bigint, text, text, text) from public, anon, authenticated;
grant execute on function public.capturar_start(bigint, text, text, text) to service_role;

-- Resultado A/B por canal e variante.
create or replace view public.ab_resultado with (security_invoker=true) as
select tc.grupo_codigo as canal, tc.variante,
  count(distinct tc.telegram_id) as cliques,
  count(distinct tc.telegram_id) filter (where exists (
     select 1 from public.telegram_capturas x
      where x.telegram_id = tc.telegram_id and x.evento='contato'
        and x.resultado not in ('telefone_invalido','conflito_telegram'))) as deram_telefone
from public.telegram_capturas tc
where tc.evento='start' and tc.variante is not null
group by tc.grupo_codigo, tc.variante
order by tc.grupo_codigo, tc.variante;
revoke all on public.ab_resultado from anon, authenticated;
