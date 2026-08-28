-- optin_tokens: payload unico que amarra o /start no bot ao telefone de origem.
-- Projeto: experts-painel (jqfpfkublwshpgtqkmeo). service_role only.
-- Limite do Telegram: deep-link start payload <= 64 chars, [A-Za-z0-9_-].

create table if not exists public.optin_tokens (
  token          text primary key,
  lead_id        uuid not null references public.leads_master(lead_id) on delete cascade,
  canal          text not null default 'sms',          -- sms | ligacao | manual
  campanha       text,
  criado_em      timestamptz not null default now(),
  expira_em      timestamptz not null default now() + interval '30 days',
  usado_em       timestamptz,
  telegram_id    bigint,                                -- quem deu /start com este token
  tentativas     integer not null default 0,
  constraint optin_tokens_formato check (token ~ '^[A-Za-z0-9_-]{16,64}$'),
  constraint optin_tokens_uso_coerente check ((usado_em is null) = (telegram_id is null)),
  constraint optin_tokens_validade check (expira_em > criado_em)
);

-- 1 token vivo por lead: evita disparar 3 links pro mesmo telefone
create unique index if not exists optin_tokens_lead_vivo_uidx
  on public.optin_tokens (lead_id) where usado_em is null;

create index if not exists optin_tokens_lead_idx on public.optin_tokens (lead_id);

alter table public.optin_tokens enable row level security;
alter table public.optin_tokens force row level security;
revoke all on public.optin_tokens from anon, authenticated;

comment on table public.optin_tokens is 'Token do deep-link t.me/<bot>?start=<token>. Resolve telegram_id -> lead_id.';


-- Gera token para um lead. Invalida o token vivo anterior do mesmo lead.
create or replace function public.gerar_optin_token(
  p_lead_id  uuid,
  p_canal    text default 'sms',
  p_campanha text default null,
  p_dias     integer default 30
)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_token text;
begin
  if not exists (select 1 from public.leads_master l where l.lead_id = p_lead_id) then
    raise exception 'lead_id % inexistente', p_lead_id using errcode = '23503';
  end if;

  -- token vivo antigo morre: so o ultimo link enviado vale
  delete from public.optin_tokens t where t.lead_id = p_lead_id and t.usado_em is null;

  v_token := translate(encode(extensions.gen_random_bytes(18), 'base64'), '+/=', '-_');

  insert into public.optin_tokens (token, lead_id, canal, campanha, expira_em)
  values (v_token, p_lead_id, coalesce(p_canal, 'sms'), p_campanha, now() + make_interval(days => greatest(p_dias, 1)));

  return v_token;
end;
$$;


-- Chamada pelo bot no /start <token>. Idempotente. Nunca sobrescreve vinculo existente.
-- Retorna jsonb: {status, lead_id}
--   status: ok | ja_vinculado | token_invalido | token_expirado | token_usado | telegram_de_outro_lead
create or replace function public.resolver_optin(
  p_token       text,
  p_telegram_id bigint,
  p_username    text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  t          public.optin_tokens%rowtype;
  v_dono     uuid;
begin
  if p_telegram_id is null then
    return jsonb_build_object('status', 'token_invalido', 'lead_id', null);
  end if;

  select * into t from public.optin_tokens o where o.token = p_token for update;
  if not found then
    return jsonb_build_object('status', 'token_invalido', 'lead_id', null);
  end if;

  update public.optin_tokens o set tentativas = o.tentativas + 1 where o.token = p_token;

  -- mesmo usuario reclicando o proprio link: idempotente
  if t.usado_em is not null then
    return jsonb_build_object(
      'status', case when t.telegram_id = p_telegram_id then 'ja_vinculado' else 'token_usado' end,
      'lead_id', case when t.telegram_id = p_telegram_id then t.lead_id else null end
    );
  end if;

  if t.expira_em <= now() then
    return jsonb_build_object('status', 'token_expirado', 'lead_id', null);
  end if;

  -- esse telegram_id ja pertence a outro lead? nao rouba o vinculo
  select l.lead_id into v_dono
    from public.leads_master l
   where l.telegram_id = p_telegram_id;

  if v_dono is not null and v_dono is distinct from t.lead_id then
    return jsonb_build_object('status', 'telegram_de_outro_lead', 'lead_id', v_dono);
  end if;

  update public.leads_master l
     set telegram_id       = p_telegram_id,
         telegram_username = coalesce(p_username, l.telegram_username),
         optin_telegram    = true,
         data_optin        = coalesce(l.data_optin, now()),
         optin_fonte       = coalesce(l.optin_fonte, 'deeplink:' || t.canal)
   where l.lead_id = t.lead_id;

  update public.optin_tokens o
     set usado_em = now(), telegram_id = p_telegram_id
   where o.token = p_token;

  return jsonb_build_object('status', 'ok', 'lead_id', t.lead_id);
end;
$$;

revoke all on function public.gerar_optin_token(uuid, text, text, integer) from public, anon, authenticated;
revoke all on function public.resolver_optin(text, bigint, text)          from public, anon, authenticated;
grant  execute on function public.gerar_optin_token(uuid, text, text, integer) to service_role;
grant  execute on function public.resolver_optin(text, bigint, text)          to service_role;
