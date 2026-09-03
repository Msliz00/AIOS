-- Fix descoberto no teste ponta a ponta: capturar_contato sobrescrevia o telefone
-- de um lead que ja tinha outro numero. Em captura de grupo comum nao ocorre (o
-- lead do grupo nao tem telefone), mas um lead do CRM que der /start num grupo e
-- compartilhar um numero diferente teria o numero do CRM apagado.
--
-- Correcao no ramo telefone_add: so preenche se o lead ainda nao tem telefone.
--   v_tg_tel is null      -> telefone_add (preenche)
--   v_tg_tel = v_norm     -> ja_completo
--   v_tg_tel <> v_norm    -> telefone_divergente (mantem o original, apenas registra)
--
-- Corpo completo da funcao vigente. Substitui a de 0007.
create or replace function public.capturar_contato(
  p_telegram_id bigint, p_telefone text, p_codigo text default null,
  p_username text default null, p_nome text default null
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_norm text; v_codigo text; v_tel_id uuid; v_tel_tg bigint;
  v_tg_id uuid; v_tg_tel text; v_lead uuid; v_status text; r_tg public.leads_master%rowtype;
begin
  if p_telegram_id is null then return jsonb_build_object('status','sem_telegram_id'); end if;
  v_codigo := coalesce(p_codigo, (
    select c.grupo_codigo from public.telegram_capturas c
     where c.telegram_id = p_telegram_id and c.evento = 'start' and c.grupo_codigo is not null
     order by c.criado_em desc limit 1));
  v_norm := public.normalizar_telefone(coalesce(p_telefone,''));
  if v_norm is null then
    insert into public.telegram_capturas (telegram_id, grupo_codigo, evento, telefone, resultado)
    values (p_telegram_id, v_codigo, 'contato', p_telefone, 'telefone_invalido');
    return jsonb_build_object('status','telefone_invalido');
  end if;
  select l.lead_id, l.telegram_id into v_tel_id, v_tel_tg from public.leads_master l where l.telefone_norm = v_norm for update;
  select l.lead_id, l.telefone_norm into v_tg_id, v_tg_tel from public.leads_master l where l.telegram_id = p_telegram_id for update;

  if v_tel_id is not null and v_tel_id = v_tg_id then
    v_lead := v_tel_id; v_status := 'ja_completo';
  elsif v_tel_id is not null and v_tg_id is not null then
    if v_tel_tg is not null and v_tel_tg is distinct from p_telegram_id then
      insert into public.telegram_capturas (telegram_id, grupo_codigo, evento, telefone, lead_id, resultado)
      values (p_telegram_id, v_codigo, 'contato', v_norm, v_tel_id, 'conflito_telegram');
      return jsonb_build_object('status','conflito_telegram','lead_id',v_tel_id);
    end if;
    select * into r_tg from public.leads_master where lead_id = v_tg_id;
    delete from public.leads_master where lead_id = v_tg_id;
    update public.leads_master crm
       set telegram_id = p_telegram_id,
           telegram_username = coalesce(crm.telegram_username, nullif(p_username,''), r_tg.telegram_username),
           nome = coalesce(crm.nome, nullif(p_nome,''), r_tg.nome),
           origem_detalhe = coalesce(crm.origem_detalhe, r_tg.origem_detalhe)
     where crm.lead_id = v_tel_id;
    v_lead := v_tel_id; v_status := 'fundido';
  elsif v_tg_id is not null then
    if v_tg_tel is null then
      update public.leads_master set telefone = p_telefone,
             telegram_username = coalesce(telegram_username, nullif(p_username,'')),
             nome = coalesce(nome, nullif(p_nome,'')) where lead_id = v_tg_id;
      v_status := 'telefone_add';
    elsif v_tg_tel = v_norm then
      v_status := 'ja_completo';
    else
      v_status := 'telefone_divergente';
    end if;
    v_lead := v_tg_id;
  elsif v_tel_id is not null then
    if v_tel_tg is not null and v_tel_tg is distinct from p_telegram_id then
      insert into public.telegram_capturas (telegram_id, grupo_codigo, evento, telefone, lead_id, resultado)
      values (p_telegram_id, v_codigo, 'contato', v_norm, v_tel_id, 'conflito_telegram');
      return jsonb_build_object('status','conflito_telegram','lead_id',v_tel_id);
    end if;
    update public.leads_master set telegram_id = p_telegram_id,
           telegram_username = coalesce(telegram_username, nullif(p_username,'')),
           nome = coalesce(nome, nullif(p_nome,'')) where lead_id = v_tel_id;
    v_lead := v_tel_id; v_status := 'telegram_add';
  else
    insert into public.leads_master (telefone, telegram_id, telegram_username, nome, origem, origem_detalhe)
    values (p_telefone, p_telegram_id, nullif(p_username,''), nullif(p_nome,''), 'telegram_grupo',
            (select nome from public.telegram_grupos where codigo = v_codigo))
    returning lead_id into v_lead;
    v_status := 'novo';
  end if;

  update public.leads_master l set optin_telegram = true,
         data_optin = coalesce(l.data_optin, now()),
         optin_fonte = coalesce(l.optin_fonte, 'grupo:' || coalesce(v_codigo,'?'))
   where l.lead_id = v_lead;
  insert into public.telegram_capturas (telegram_id, grupo_codigo, evento, telefone, lead_id, resultado)
  values (p_telegram_id, v_codigo, 'contato', v_norm, v_lead, v_status);
  return jsonb_build_object('status', v_status, 'lead_id', v_lead, 'grupo', v_codigo);
end; $$;

revoke all on function public.capturar_contato(bigint, text, text, text, text) from public, anon, authenticated;
grant execute on function public.capturar_contato(bigint, text, text, text, text) to service_role;
