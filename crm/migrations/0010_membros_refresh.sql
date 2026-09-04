-- Item 6: atualização automática (24h) da contagem de membros dos grupos.
-- O workflow n8n "ATUALIZAR MEMBROS 24H" lê o token do bot em app_config,
-- busca os grupos com chat_ref, chama getChatMemberCount e grava via set_membros.
-- Canais públicos usam @username; privados dependem do chat_id (capturado por channel_post).

-- identificadores de canal
alter table public.telegram_grupos add column if not exists chat_ref text; -- @username OU chat_id (texto) usado pela API
alter table public.telegram_grupos add column if not exists chat_id bigint; -- id numérico do canal (privados)

-- públicos já conhecidos (pelo link t.me/<username>)
update public.telegram_grupos set chat_ref='@mentoriajogarslot' where codigo='g4' and chat_ref is null;
update public.telegram_grupos set chat_ref='@analistaswolf'     where codigo='g5' and chat_ref is null;
update public.telegram_grupos set chat_ref='@oslot888'          where codigo='g8' and chat_ref is null;

-- atualiza a contagem de um grupo (chamado pelo n8n)
create or replace function public.set_membros(p_codigo text, p_n int)
returns void language plpgsql security definer set search_path='' as $$
begin
  update public.telegram_grupos set membros = p_n, aferido_em = current_date where codigo = p_codigo;
end;$$;
revoke all on function public.set_membros(text,int) from public, anon, authenticated;
grant execute on function public.set_membros(text,int) to service_role;

-- descoberta de chat_id de canais privados via channel_post do bot
create table if not exists public.telegram_canais_descobertos(
  chat_id  bigint primary key,
  title    text,
  visto_em timestamptz not null default now()
);
alter table public.telegram_canais_descobertos enable row level security;
alter table public.telegram_canais_descobertos force row level security;
revoke all on public.telegram_canais_descobertos from anon, authenticated;

create or replace function public.registrar_chat_id(p_chat_id bigint, p_title text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_cod text;
begin
  if p_chat_id is null then return jsonb_build_object('status','sem_chat_id'); end if;
  insert into public.telegram_canais_descobertos(chat_id, title) values (p_chat_id, nullif(p_title,''))
    on conflict (chat_id) do update set title = coalesce(excluded.title, public.telegram_canais_descobertos.title), visto_em = now();
  update public.telegram_grupos set chat_id = p_chat_id, chat_ref = coalesce(chat_ref, p_chat_id::text)
    where chat_id is null and (nome = p_title or nome_base = p_title) returning codigo into v_cod;
  return jsonb_build_object('status','ok','ligado_a', v_cod);
end;$$;
revoke all on function public.registrar_chat_id(bigint,text) from public, anon, authenticated;
grant execute on function public.registrar_chat_id(bigint,text) to service_role;

-- config chave-valor (guarda o token do bot para o n8n ler em runtime)
create table if not exists public.app_config(
  chave text primary key,
  valor text,
  atualizado_em timestamptz not null default now()
);
alter table public.app_config enable row level security;
alter table public.app_config force row level security;
revoke all on public.app_config from anon, authenticated;

create or replace function public.get_config(p_chave text)
returns jsonb language sql security definer set search_path='' as $$
  select jsonb_build_object('valor', (select valor from public.app_config where chave = p_chave));
$$;
revoke all on function public.get_config(text) from public, anon, authenticated;
grant execute on function public.get_config(text) to service_role;

insert into public.app_config(chave, valor) values ('telegram_bot_token', null)
  on conflict (chave) do nothing;
