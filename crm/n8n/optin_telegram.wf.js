import { workflow, node, trigger, sticky, newCredential, ifElse, switchCase, nodeJson, expr } from '@n8n/workflow-sdk';

const gatilhoStart = trigger({
  type: 'n8n-nodes-base.telegramTrigger',
  version: 1.5,
  config: {
    name: 'Telegram /start',
    parameters: { updates: ['message'] },
    credentials: { telegramApi: newCredential('Telegram Ribasadm1') },
    position: [0, 0]
  },
  output: [{ message: { chat: { id: 555000111 }, from: { id: 555000111, username: 'fulano', first_name: 'Fulano' }, text: '/start Ab3-x9Zq_LmN0pQrS1tUvW' } }]
});

const extrairPayload = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Extrair Payload',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'chat-id', name: 'chat_id', value: expr('{{ $json.message.chat.id }}'), type: 'string' },
          { id: 'telegram-id', name: 'telegram_id', value: expr('{{ $json.message.from.id }}'), type: 'number' },
          { id: 'username', name: 'username', value: expr('{{ $json.message.from.username || "" }}'), type: 'string' },
          { id: 'primeiro-nome', name: 'primeiro_nome', value: expr('{{ $json.message.from.first_name || "" }}'), type: 'string' },
          { id: 'payload', name: 'payload', value: expr("{{ ($json.message.text || '').startsWith('/start ') ? $json.message.text.substring(7).trim() : '' }}"), type: 'string' }
        ]
      }
    },
    position: [220, 0]
  },
  output: [{ chat_id: '555000111', telegram_id: 555000111, username: 'fulano', primeiro_nome: 'Fulano', payload: 'Ab3-x9Zq_LmN0pQrS1tUvW' }]
});

const temToken = ifElse({
  version: 2.2,
  config: {
    name: 'Tem Payload?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.payload }}'), operator: { type: 'string', operation: 'notEmpty' } }
        ],
        combinator: 'and'
      }
    },
    position: [440, 0]
  }
});

const resolverOptin = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Resolver Opt-in',
    parameters: {
      method: 'POST',
      url: 'https://jqfpfkublwshpgtqkmeo.supabase.co/rest/v1/rpc/resolver_optin',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpTemplatedCustomAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: {
        parameters: [
          { name: 'Content-Type', value: 'application/json' }
        ]
      },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ { "p_token": $json.payload, "p_telegram_id": $json.telegram_id, "p_username": $json.username } }}'),
      options: { response: { response: { neverError: true, responseFormat: 'json' } }, timeout: 15000 }
    },
    credentials: { httpTemplatedCustomAuth: newCredential('Supabase experts-painel') },
    position: [660, -120]
  },
  output: [{ status: 'ok', lead_id: '5f1c9c2e-0a1b-4c3d-8e9f-2a3b4c5d6e7f' }]
});

const rotearStatus = switchCase({
  version: 3.4,
  config: {
    name: 'Rotear Status',
    parameters: {
      mode: 'rules',
      rules: {
        values: [
          {
            renameOutput: true,
            outputKey: 'vinculado',
            conditions: {
              options: { caseSensitive: false, leftValue: '', typeValidation: 'loose' },
              conditions: [
                { leftValue: expr('{{ $json.status }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'ok' }
              ],
              combinator: 'and'
            }
          },
          {
            renameOutput: true,
            outputKey: 'ja_vinculado',
            conditions: {
              options: { caseSensitive: false, leftValue: '', typeValidation: 'loose' },
              conditions: [
                { leftValue: expr('{{ $json.status }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'ja_vinculado' }
              ],
              combinator: 'and'
            }
          },
          {
            renameOutput: true,
            outputKey: 'link_invalido',
            conditions: {
              options: { caseSensitive: false, leftValue: '', typeValidation: 'loose' },
              conditions: [
                { leftValue: expr('{{ $json.status }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'token_invalido' },
                { leftValue: expr('{{ $json.status }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'token_expirado' },
                { leftValue: expr('{{ $json.status }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'token_usado' },
                { leftValue: expr('{{ $json.status }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'telegram_de_outro_lead' }
              ],
              combinator: 'or'
            }
          }
        ]
      },
      options: { fallbackOutput: 'extra', renameFallbackOutput: 'falha_tecnica' }
    },
    position: [880, -120]
  }
});

const respostaVinculado = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Resposta Vinculado',
    parameters: {
      resource: 'message',
      operation: 'sendMessage',
      chatId: nodeJson(extrairPayload, 'chat_id'),
      text: expr('Cadastro confirmado, {{ $("Extrair Payload").item.json.primeiro_nome }}! Voce ja esta na lista oficial. A partir de agora recebe os avisos por aqui.'),
      additionalFields: { appendAttribution: false }
    },
    position: [1120, -320]
  },
  output: [{ ok: true, result: { message_id: 1 } }]
});

const respostaJaVinculado = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Resposta Ja Vinculado',
    parameters: {
      resource: 'message',
      operation: 'sendMessage',
      chatId: nodeJson(extrairPayload, 'chat_id'),
      text: 'Voce ja esta confirmado. Nao precisa fazer nada, e so aguardar os avisos por aqui.',
      additionalFields: { appendAttribution: false }
    },
    position: [1120, -160]
  },
  output: [{ ok: true, result: { message_id: 2 } }]
});

const respostaLinkInvalido = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Resposta Link Invalido',
    parameters: {
      resource: 'message',
      operation: 'sendMessage',
      chatId: nodeJson(extrairPayload, 'chat_id'),
      text: 'Esse link ja foi usado ou expirou. Peca um link novo no atendimento para confirmar seu cadastro.',
      additionalFields: { appendAttribution: false }
    },
    position: [1120, 0]
  },
  output: [{ ok: true, result: { message_id: 3 } }]
});

const respostaFalha = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Resposta Falha Tecnica',
    parameters: {
      resource: 'message',
      operation: 'sendMessage',
      chatId: nodeJson(extrairPayload, 'chat_id'),
      text: 'Nao consegui confirmar seu cadastro agora. Tente de novo em alguns minutos.',
      additionalFields: { appendAttribution: false }
    },
    position: [1120, 160]
  },
  output: [{ ok: true, result: { message_id: 4 } }]
});

const respostaSemToken = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Resposta Sem Token',
    parameters: {
      resource: 'message',
      operation: 'sendMessage',
      chatId: nodeJson(extrairPayload, 'chat_id'),
      text: 'Para confirmar seu cadastro, use o link que voce recebeu por SMS ou na ligacao.',
      additionalFields: { appendAttribution: false }
    },
    position: [660, 200]
  },
  output: [{ ok: true, result: { message_id: 5 } }]
});

const notaFluxo = sticky(
  '## Opt-in lead_id\nLiga telefone (CRM) ao telegram_id via token do deep-link.\nRPC: resolver_optin em experts-painel. Nada e gravado sem token valido.',
  [gatilhoStart, extrairPayload, temToken],
  { color: 4 }
);

export default workflow('optin-lead-id', 'OPT-IN lead_id · Telegram (experts-painel)')
  .add(gatilhoStart)
  .to(extrairPayload)
  .to(temToken
    .onTrue(resolverOptin.to(rotearStatus
      .onCase(0, respostaVinculado)
      .onCase(1, respostaJaVinculado)
      .onCase(2, respostaLinkInvalido)
      .onCase(3, respostaFalha)))
    .onFalse(respostaSemToken))
  .add(notaFluxo);
