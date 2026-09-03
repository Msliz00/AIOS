-- painel_dados(): consolida os agregados do painel em um jsonb. Zero PII.
-- Consumido pela edge function 'painel' (crm/edge/painel), que chama com service_role.
create or replace function public.painel_dados()
returns jsonb language sql security definer set search_path = '' stable as $$
  select jsonb_build_object(
    'gerado_em', now(),
    'base', (select jsonb_build_object(
        'total', count(*),
        'com_telefone', count(*) filter (where telefone_norm is not null),
        'com_email', count(*) filter (where email is not null),
        'com_telegram', count(*) filter (where telegram_id is not null),
        'ponte', count(*) filter (where telefone_norm is not null and telegram_id is not null),
        'sem_consentimento', count(*) filter (where not optin_sms and not optin_ligacao and telefone_norm is not null)
      ) from public.leads_master),
    'canais', (select jsonb_build_object(
        'sms', count(*) filter (where optin_sms),
        'ligacao', count(*) filter (where optin_ligacao),
        'email', count(*) filter (where email is not null and optin_ligacao),
        'telegram_optin', count(*) filter (where optin_telegram)
      ) from public.leads_master),
    'captura', (select coalesce(jsonb_agg(jsonb_build_object(
        'codigo', codigo, 'nome', nome, 'membros', membros,
        'clicaram', clicaram, 'deram_telefone', deram_telefone, 'fundidos', fundidos_com_crm
      ) order by membros desc), '[]'::jsonb) from public.captura_grupos),
    'cobertura', (select coalesce(jsonb_agg(jsonb_build_object(
        'nome', nome, 'membros', membros, 'conhecidos', leads_conhecidos, 'pct', cobertura_pct
      ) order by membros desc), '[]'::jsonb) from public.cobertura_grupos),
    'origens', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select jsonb_build_object('origem', origem, 'n', n) as x
        from (select origem, count(*) n from public.leads_master group by origem order by count(*) desc limit 10) t
      ) y)
  );
$$;
revoke all on function public.painel_dados() from public, anon, authenticated;
grant execute on function public.painel_dados() to service_role;
