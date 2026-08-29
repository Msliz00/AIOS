-- Lado do disparo: transforma telefone em link de opt-in pronto para SMS/ligacao.
-- Projeto: experts-painel (jqfpfkublwshpgtqkmeo). service_role only.

-- Upsert de lead por telefone. Nunca sobrescreve dado existente com nulo.
create or replace function public.registrar_lead(
  p_telefone text,
  p_nome     text default null,
  p_email    text default null,
  p_origem   text default 'crm_base_fria'
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_norm text;
  v_lead uuid;
begin
  v_norm := nullif(regexp_replace(coalesce(p_telefone, ''), '\D', '', 'g'), '');
  if v_norm is null then
    raise exception 'telefone invalido: %', p_telefone using errcode = '22023';
  end if;

  select l.lead_id into v_lead from public.leads_master l where l.telefone_norm = v_norm;

  if v_lead is null then
    insert into public.leads_master (telefone, nome, email, origem)
    values (p_telefone, p_nome, p_email, coalesce(p_origem, 'crm_base_fria'))
    returning lead_id into v_lead;
  else
    update public.leads_master l
       set nome  = coalesce(l.nome, p_nome),
           email = coalesce(l.email, p_email)
     where l.lead_id = v_lead;
  end if;

  return v_lead;
end;
$$;


-- Telefone -> link pronto. E o que o disparo (SMS/ligacao) consome.
create or replace function public.gerar_link_optin(
  p_telefone text,
  p_canal    text default 'sms',
  p_campanha text default null,
  p_nome     text default null,
  p_dias     integer default 30,
  p_bot      text default 'Ribasadm1_bot'
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_lead  uuid;
  v_token text;
begin
  v_lead  := public.registrar_lead(p_telefone, p_nome, null, 'disparo_' || coalesce(p_canal, 'sms'));
  v_token := public.gerar_optin_token(v_lead, p_canal, p_campanha, p_dias);

  return jsonb_build_object(
    'lead_id',  v_lead,
    'telefone', p_telefone,
    'token',    v_token,
    'link',     'https://t.me/' || p_bot || '?start=' || v_token
  );
end;
$$;


-- Lote: recebe [{"telefone":"...","nome":"..."}] e devolve uma linha por lead.
create or replace function public.gerar_links_lote(
  p_leads    jsonb,
  p_canal    text default 'sms',
  p_campanha text default null,
  p_dias     integer default 30,
  p_bot      text default 'Ribasadm1_bot'
)
returns table (lead_id uuid, telefone text, token text, link text)
language plpgsql
security definer
set search_path = ''
as $$
declare
  r jsonb;
  v jsonb;
begin
  for r in select value from jsonb_array_elements(p_leads)
  loop
    v := public.gerar_link_optin(r->>'telefone', p_canal, p_campanha, r->>'nome', p_dias, p_bot);
    lead_id  := (v->>'lead_id')::uuid;
    telefone := v->>'telefone';
    token    := v->>'token';
    link     := v->>'link';
    return next;
  end loop;
end;
$$;


-- Telemetria do funil de opt-in.
create or replace view public.optin_funil
with (security_invoker = true) as
select
  count(*)                                                          as leads_total,
  count(*) filter (where telegram_id is not null)                   as com_telegram,
  count(*) filter (where optin_telegram)                            as com_optin,
  count(*) filter (where telefone_norm is not null
                     and telegram_id is not null)                   as ponte_completa,
  (select count(*) from public.optin_tokens)                        as tokens_gerados,
  (select count(*) from public.optin_tokens where usado_em is not null) as tokens_usados
from public.leads_master;

revoke all on public.optin_funil from anon, authenticated;

revoke all on function public.registrar_lead(text, text, text, text)              from public, anon, authenticated;
revoke all on function public.gerar_link_optin(text, text, text, text, integer, text) from public, anon, authenticated;
revoke all on function public.gerar_links_lote(jsonb, text, text, integer, text)   from public, anon, authenticated;
grant execute on function public.registrar_lead(text, text, text, text)              to service_role;
grant execute on function public.gerar_link_optin(text, text, text, text, integer, text) to service_role;
grant execute on function public.gerar_links_lote(jsonb, text, text, integer, text)   to service_role;
