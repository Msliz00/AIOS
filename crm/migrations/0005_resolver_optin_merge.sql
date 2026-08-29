-- Descoberto ao preparar a migracao da base: os 21.824 leads vindos dos grupos
-- do Telegram entram sem telefone. Sem merge, todo lead que ja esta num grupo e
-- recebe SMS bateria em 'telegram_de_outro_lead' e teria o vinculo RECUSADO --
-- justamente o caso mais comum. Agora esses dois registros se fundem.
--
-- Tambem corrige a normalizacao para o padrao "55 + 0DDD" (14 digitos) que
-- aparece em 17 registros da crm_base_fria.

create or replace function public.normalizar_telefone(p_telefone text)
returns text
language sql
immutable
strict
set search_path = ''
as $$
  with d as (select regexp_replace(p_telefone, '\D', '', 'g') as v)
  select case
    when length(v) between 10 and 11 then '55' || v
    when length(v) = 14 and v like '550%' then '55' || substring(v from 4)
    else nullif(v, '')
  end
  from d;
$$;

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
  v_dono_tel text;
  v_status   text := 'ok';
begin
  if p_telegram_id is null then
    return jsonb_build_object('status', 'token_invalido', 'lead_id', null);
  end if;

  select * into t from public.optin_tokens o where o.token = p_token for update;
  if not found then
    return jsonb_build_object('status', 'token_invalido', 'lead_id', null);
  end if;

  update public.optin_tokens o set tentativas = o.tentativas + 1 where o.token = p_token;

  if t.usado_em is not null then
    return jsonb_build_object(
      'status', case when t.telegram_id = p_telegram_id then 'ja_vinculado' else 'token_usado' end,
      'lead_id', case when t.telegram_id = p_telegram_id then t.lead_id else null end
    );
  end if;

  if t.expira_em <= now() then
    return jsonb_build_object('status', 'token_expirado', 'lead_id', null);
  end if;

  select l.lead_id, l.telefone_norm into v_dono, v_dono_tel
    from public.leads_master l
   where l.telegram_id = p_telegram_id
     for update;

  if v_dono is not null and v_dono is distinct from t.lead_id then
    if v_dono_tel is not null then
      -- dois telefones diferentes disputando o mesmo telegram: nao decide sozinho
      return jsonb_build_object('status', 'telegram_de_outro_lead', 'lead_id', v_dono);
    end if;

    -- lead so-Telegram: funde no lead do token e some
    update public.leads_master alvo
       set telegram_username = coalesce(alvo.telegram_username, orig.telegram_username),
           nome              = coalesce(alvo.nome, orig.nome),
           origem_detalhe    = coalesce(alvo.origem_detalhe, orig.origem, orig.origem_detalhe)
      from public.leads_master orig
     where alvo.lead_id = t.lead_id and orig.lead_id = v_dono;

    delete from public.leads_master where lead_id = v_dono;
    v_status := 'fundido';
  end if;

  update public.leads_master l
     set telegram_id       = p_telegram_id,
         telegram_username = coalesce(nullif(p_username, ''), l.telegram_username),
         optin_telegram    = true,
         data_optin        = coalesce(l.data_optin, now()),
         optin_fonte       = coalesce(l.optin_fonte, 'deeplink:' || t.canal)
   where l.lead_id = t.lead_id;

  update public.optin_tokens o set usado_em = now(), telegram_id = p_telegram_id where o.token = p_token;

  return jsonb_build_object('status', v_status, 'lead_id', t.lead_id);
end;
$$;

revoke all on function public.resolver_optin(text, bigint, text) from public, anon, authenticated;
grant execute on function public.resolver_optin(text, bigint, text) to service_role;
revoke all on function public.normalizar_telefone(text) from public, anon, authenticated;
grant execute on function public.normalizar_telefone(text) to service_role;
