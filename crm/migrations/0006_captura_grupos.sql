-- Captura nos grupos: payload por grupo (reutilizavel, nao consumivel) +
-- telefone verificado via request_contact do Telegram. Fecha a ponte pelo lado
-- do Telegram, sem depender de SMS. Alvo: 46 mil membros em 3 canais que nunca
-- tiveram um lead capturado.

alter table public.telegram_grupos add column if not exists codigo text;
update public.telegram_grupos set codigo = 'g' || grupo_id where codigo is null;
alter table public.telegram_grupos alter column codigo set not null;
create unique index if not exists telegram_grupos_codigo_uidx on public.telegram_grupos (codigo);

create table if not exists public.telegram_capturas (
  id            bigint generated always as identity primary key,
  telegram_id   bigint not null,
  grupo_codigo  text,
  evento        text not null check (evento in ('start','contato','recusou')),
  telefone      text,
  lead_id       uuid,
  resultado     text,
  criado_em     timestamptz not null default now()
);
create index if not exists telegram_capturas_tg_idx    on public.telegram_capturas (telegram_id);
create index if not exists telegram_capturas_grupo_idx on public.telegram_capturas (grupo_codigo, evento);

alter table public.telegram_capturas enable row level security;
alter table public.telegram_capturas force row level security;
revoke all on public.telegram_capturas from anon, authenticated;

comment on table public.telegram_capturas is 'Evento de cada /start<grupo> e contato compartilhado. Base do funil de captura.';

-- /start g<n>: captura o telegram_id assim que o lead entra no bot, antes do telefone.
create or replace function public.capturar_start(
  p_telegram_id bigint, p_codigo text, p_username text default null, p_nome text default null
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare g public.telegram_grupos%rowtype; v_lead uuid; v_tel text;
begin
  if p_telegram_id is null then return jsonb_build_object('status','sem_telegram_id'); end if;
  select * into g from public.telegram_grupos t where t.codigo = p_codigo;
  if not found then
    insert into public.telegram_capturas (telegram_id, grupo_codigo, evento, resultado)
    values (p_telegram_id, p_codigo, 'start', 'grupo_invalido');
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
  insert into public.telegram_capturas (telegram_id, grupo_codigo, evento, lead_id, resultado)
  values (p_telegram_id, p_codigo, 'start', v_lead, case when v_tel is not null then 'ja_tinha_telefone' else 'ok' end);
  return jsonb_build_object('status','ok','lead_id',v_lead,'grupo',g.nome,'ja_tem_telefone', v_tel is not null);
end; $$;

-- Contato compartilhado: telefone verificado pelo Telegram. Merge inverso — a versao
-- final desta funcao (deriva o grupo do ultimo /start) esta em 0007.
-- [corpo inicial omitido aqui: ver 0007 para a versao vigente]

create or replace view public.captura_grupos with (security_invoker = true) as
select g.codigo, g.nome, g.membros,
  count(distinct c.telegram_id) filter (where c.evento = 'start') as clicaram,
  count(distinct c.telegram_id) filter (where c.evento = 'contato'
    and c.resultado not in ('telefone_invalido','conflito_telegram')) as deram_telefone,
  count(*) filter (where c.evento = 'contato' and c.resultado = 'fundido') as fundidos_com_crm
from public.telegram_grupos g
left join public.telegram_capturas c on c.grupo_codigo = g.codigo
group by g.codigo, g.nome, g.membros, g.grupo_id order by g.grupo_id;
revoke all on public.captura_grupos from anon, authenticated;

revoke all on function public.capturar_start(bigint, text, text, text) from public, anon, authenticated;
grant execute on function public.capturar_start(bigint, text, text, text) to service_role;
