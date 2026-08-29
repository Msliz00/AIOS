-- Bug: "+55 11 98888-0001" e "(11) 98888-0001" viravam dois leads distintos.
-- Fix: normalizacao E.164 BR centralizada em uma funcao IMMUTABLE, usada pela
-- coluna gerada E pelo registrar_lead (antes cada um tinha a sua regra).
-- ATENCAO: o DROP CASCADE derruba os indices sobre telefone_norm e a view
-- optin_funil; ambos sao recriados aqui.

create or replace function public.normalizar_telefone(p_telefone text)
returns text
language sql
immutable
strict
set search_path = ''
as $$
  select case
    when length(regexp_replace(p_telefone, '\D', '', 'g')) between 10 and 11
      then '55' || regexp_replace(p_telefone, '\D', '', 'g')
    else nullif(regexp_replace(p_telefone, '\D', '', 'g'), '')
  end;
$$;

alter table public.leads_master drop column telefone_norm cascade;

alter table public.leads_master
  add column telefone_norm text generated always as (public.normalizar_telefone(telefone)) stored;

create unique index leads_master_telefone_uidx on public.leads_master (telefone_norm) where telefone_norm is not null;
create index leads_master_ponte_idx on public.leads_master (criado_em) where telefone_norm is not null and telegram_id is not null;

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
  v_norm := public.normalizar_telefone(coalesce(p_telefone, ''));
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

create or replace view public.optin_funil
with (security_invoker = true) as
select
  count(*)                                                             as leads_total,
  count(*) filter (where telegram_id is not null)                      as com_telegram,
  count(*) filter (where optin_telegram)                               as com_optin,
  count(*) filter (where telefone_norm is not null
                     and telegram_id is not null)                      as ponte_completa,
  (select count(*) from public.optin_tokens)                           as tokens_gerados,
  (select count(*) from public.optin_tokens where usado_em is not null) as tokens_usados
from public.leads_master;

revoke all on public.optin_funil from anon, authenticated;
revoke all on function public.normalizar_telefone(text) from public, anon, authenticated;
grant execute on function public.normalizar_telefone(text) to service_role;

comment on column public.leads_master.telefone_norm is 'E.164 BR sem +: 10-11 digitos recebem prefixo 55. Base da unicidade de telefone.';
