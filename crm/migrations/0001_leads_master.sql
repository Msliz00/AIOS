-- lead_id: chave única que liga telefone (CRM) <-> telegram_id (bot)
-- Projeto: experts-painel (jqfpfkublwshpgtqkmeo)
-- Acesso: service_role only. RLS on, zero policies => anon/authenticated bloqueados.

create extension if not exists pgcrypto;

create table if not exists public.leads_master (
  lead_id            uuid primary key default gen_random_uuid(),

  -- mundo CRM
  telefone           text,
  telefone_norm      text generated always as (nullif(regexp_replace(coalesce(telefone,''), '\D', '', 'g'), '')) stored,
  email              text,
  nome               text,

  -- mundo Telegram
  telegram_id        bigint,
  telegram_username  text,

  -- proveniencia
  origem             text not null default 'desconhecida',
  origem_detalhe     text,

  -- consentimento (LGPD)
  optin_telegram     boolean not null default false,
  optin_sms          boolean not null default false,
  optin_ligacao      boolean not null default false,
  data_optin         timestamptz,
  optin_fonte        text,
  optout_em          timestamptz,

  criado_em          timestamptz not null default now(),
  atualizado_em      timestamptz not null default now(),

  constraint leads_master_tem_chave check (telefone is not null or telegram_id is not null or email is not null)
);

-- unicidade parcial: so vale quando a coluna existe
create unique index if not exists leads_master_telefone_uidx  on public.leads_master (telefone_norm) where telefone_norm is not null;
create unique index if not exists leads_master_telegram_uidx  on public.leads_master (telegram_id)   where telegram_id is not null;
create unique index if not exists leads_master_email_uidx     on public.leads_master (lower(email))  where email is not null;

-- lead com os dois mundos costurados = o alvo do projeto
create index if not exists leads_master_ponte_idx on public.leads_master (criado_em)
  where telefone_norm is not null and telegram_id is not null;

create or replace function public.tg_atualizado_em()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.atualizado_em := now();
  return new;
end;
$$;

drop trigger if exists leads_master_atualizado_em on public.leads_master;
create trigger leads_master_atualizado_em
  before update on public.leads_master
  for each row execute function public.tg_atualizado_em();

alter table public.leads_master enable row level security;
alter table public.leads_master force row level security;

revoke all on public.leads_master from anon, authenticated;
revoke all on function public.tg_atualizado_em() from anon, authenticated;

comment on table  public.leads_master     is 'Lead unico do funil. lead_id e a ponte telefone<->telegram_id. service_role only.';
comment on column public.leads_master.telefone_norm is 'Somente digitos, gerada. Base da unicidade de telefone.';
comment on column public.leads_master.data_optin    is 'Momento do /start no bot ou do aceite no disparo.';
