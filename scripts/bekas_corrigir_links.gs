/**
 * BEKAS - preenche e CORRIGE a coluna C (LINK) com os links reais do Drive,
 * colhidos pela varredura da pasta FINALIZADOS RODRI NOVA REGULAMENTACAO.
 *
 * Substitui os links errados de CXL_AD02..AD08, em que as variantes _SL e
 * nao-_SL apontavam para o mesmo arquivo.
 *
 * COMO USAR
 *   1. Planilha BEKAS > Extensoes > Apps Script
 *   2. Apagar tudo e colar este arquivo
 *   3. Rodar BEKAS_listarAbas  -> mostra nome + ID de cada aba (so se precisar ajustar ABAS)
 *   4. Rodar BEKAS_simular     -> mostra o que faria, sem gravar nada
 *   5. Rodar BEKAS_aplicar     -> grava
 *   Resultado em Execucoes > Registros.
 */

// ===================== CONFIG =====================
// ID da planilha BEKAS. Deixe preenchido para rodar de qualquer projeto
// Apps Script. Se o script estiver vinculado a planilha, pode deixar ''.
var ID_PLANILHA = '1IpISy5pq1vimkKGqx-KNfj3QX-CKg786vfSy6XW_l2g';

// IDs das abas que o script pode alterar. Nada fora desta lista e tocado.
var ABAS = [
  552723389,    // MEDIANO E EXCELENTE S36 · 31/08-06/09 -> MARQUES
  2106965851    // MARQUES
];

var COL_NOME = 1;        // A
var COL_LINK = 3;        // C
var LINHA_INICIAL = 2;

// Repinta a coluna A depois de gravar: verde = tem link, vermelho = sem link.
// A pintura azul das linhas (A ate N) nao e alterada.
var REPINTAR_COLUNA_A = true;
var VERDE = '#b6d7a8';
var VERMELHO = '#ea9999';
// ==================================================

var MAPA = {
  // ---- CAIXINHA (16)
  'CXL_AD01_SL-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1CrhsPR3LOGUqurgnDlojqCu-YgGdo9Bq/view',
  'CXL_AD01-compliance-31/ago.mp4':    'https://drive.google.com/file/d/19Q_roMKZ3zpStXD7m8k7suU1SMrY2K2Z/view',
  'CXL_AD02_SL-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1CEHxfzJeQfDjzx814GyAKDbIStRolJvZ/view',
  'CXL_AD02-compliance-31/ago.mp4':    'https://drive.google.com/file/d/1TU9VnKjWDUY0AdoQ6L6aE0tTj8POsWCT/view',
  'CXL_AD03_SL-compliance-31/ago.mp4': 'https://drive.google.com/file/d/15Ib0uShgoaJwjG_YIbQeGXePi64rtKc9/view',
  'CXL_AD03-compliance-31/ago.mp4':    'https://drive.google.com/file/d/1TA-a6IBYE1WzxBvq2VXHWqwVV-KSVjiU/view',
  'CXL_AD04_SL-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1Tp6BvFzS1hO8GoOB3G96uS2cgj9yEtNb/view',
  'CXL_AD04-compliance-31/ago.mp4':    'https://drive.google.com/file/d/1GO0c3HafP0uKis8z8qj3XoYNn2vLzGO5/view',
  'CXL_AD05_SL-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1kwHK-q6CCVU_coZ6CskjBL1Rw94eS3kX/view',
  'CXL_AD05-compliance-31/ago.mp4':    'https://drive.google.com/file/d/1WoHvev3eF7oK3OnY9vrtXJMzH5aW3gdF/view',
  'CXL_AD06_SL-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1N2QK4n41sEKRHpaq7cSOGt6NVX_0IHOk/view',
  'CXL_AD06-compliance-31/ago.mp4':    'https://drive.google.com/file/d/1P9dCC5yPDpCNK6c3xL2mXPmgUi4p03OB/view',
  'CXL_AD07_SL-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1QJOz8R-unlwMWOZ0pUjcZQIFBfiaqZQ6/view',
  'CXL_AD07-compliance-31/ago.mp4':    'https://drive.google.com/file/d/19bNBieNM0B6TjB9yr1Wz5FfqQc9UYei5/view',
  'CXL_AD08_SL-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1j3BBxE-6TGX7dUjW6pntPzazKrrX9m9m/view',
  'CXL_AD08-compliance-31/ago.mp4':    'https://drive.google.com/file/d/1YNPARtpObqtAsFyk8oj6JxHKmFS6dCD0/view',

  // ---- AD 14 - GRAVACAO DE TELA 20X (8)
  'AD14_CX01-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1yjyRe7z0TxIJv5t8cP_q2UpIUOXyVsY7/view',
  'AD14_CX02-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1hFo1MDEps5zIuiSp4mm4SwROU2qgJtON/view',
  'AD14_CX03-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1rwdQC5b9fBZ9GVkY5Wfn5E2zXSPX1GbI/view',
  'AD14_CX04-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1hYIKoFyTl-ofwN-0p2FyGabx-tsQ9_yZ/view',
  'AD14_CX05-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1qI8NzWitUme93Ci27tzSnt_qCt7otZYB/view',
  'AD14_CX06-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1vm4A9wEXjxgPPY36_BUsHb6Xb6vrBElO/view',
  'AD14_CX07-compliance-31/ago.mp4': 'https://drive.google.com/file/d/15-1MWHM3td-guefOZLbEP4Tz0MHFKn2C/view',
  'AD14_CX08-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1Pj5dTkSclIq3lLqUlLtURd0_Ph8Gdcag/view',

  // ---- AD 13 - NARRACAO 100X - HOOK CAIXINHA (8)
  'AD13_HOOK_CX01-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1dJLHOQcdTp_Ru80sH1f-Zh8mdQhShS3C/view',
  'AD13_HOOK_CX02-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1B-Jlmw_-0VtTMf_k_NbINWmtprAKqzQZ/view',
  'AD13_HOOK_CX03-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1po2JB3i_Hk5K32tNozQzXyUv8VAkzENk/view',
  'AD13_HOOK_CX04-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1PSZINM98yZWMSXCXsLot55L3UT5Ad-uC/view',
  'AD13_HOOK_CX05-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1HwrIPoJdCH_g66VMtAMQ2OaQJyoax_zK/view',
  'AD13_HOOK_CX06-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1KjPabpl2g7bQ8r1Gsz85CrJd6JZO6WR3/view',
  'AD13_HOOK_CX07-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1I0oVdwdBODzQgWaX83rIX_72Eg817MeI/view',
  'AD13_HOOK_CX08-compliance-31/ago.mp4': 'https://drive.google.com/file/d/12ZBo52Et4eYwxFuc9JYRXzJsRw7B7iPr/view',

  // ---- AD 12 - NARRACAO 50X (8)
  'AD12_HOOK_CX01-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1RsexVMgw22QY0wZKTSpF0r2l-hv7ejac/view',
  'AD12_HOOK_CX02-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1KpZrId4KHY8GenA-kQlUGbW6TKqLI3_w/view',
  'AD12_HOOK_CX03-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1jXmsyR7fkhNBxH0_wlylbZsuEDdQVmVK/view',
  'AD12_HOOK_CX04-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1cgbL1UER8fC0nmQg3yXSYw4xOgmYRtW1/view',
  'AD12_HOOK_CX05-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1jFq-H2UaCu01FzWo1L7wgnHz8g6mD3z3/view',
  'AD12_HOOK_CX06-compliance-31/ago.mp4': 'https://drive.google.com/file/d/12EFNFK5mHlgawRmcHj_XwUeq7wGkD-gD/view',
  'AD12_HOOK_CX07-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1k3PAxBlEB5EDb7v-sCU19Gecn_bhg-9y/view',
  'AD12_HOOK_CX08-compliance-31/ago.mp4': 'https://drive.google.com/file/d/1Zw79yUO-qRb2rjPCowHjPyJCKYTfsw8R/view'
};

// ---------------------------------------------------------------- ENTRADA
function BEKAS_simular() { rodar(true); }
function BEKAS_aplicar() { rodar(false); }

function BEKAS_listarAbas() {
  var l = ['ABAS DESTA PLANILHA (nome -> ID):'];
  planilha().getSheets().forEach(function (sh) {
    var alvo = ABAS.indexOf(sh.getSheetId()) >= 0;
    l.push('  ' + (alvo ? '[ALTERA]  ' : '[intacta] ') + sh.getSheetId() + '  ' + sh.getName());
  });
  Logger.log(l.join('\n'));
}

// ---------------------------------------------------------------- MOTOR
function rodar(simular) {
  var ss = planilha();

  var mapa = {};
  for (var k in MAPA) mapa[chave(k)] = MAPA[k];

  var log = ['=== ' + (simular ? 'SIMULACAO (nada gravado)' : 'GRAVANDO') + ' ===',
             'Links disponiveis no mapa: ' + Object.keys(mapa).length, ''];
  var totalNovos = 0, totalCorrigidos = 0;

  ABAS.forEach(function (id) {
    var sh = abaPorId(ss, id);
    if (!sh) { log.push('AVISO: aba de ID ' + id + ' nao encontrada.'); return; }

    var ult = sh.getLastRow();
    if (ult < LINHA_INICIAL) { log.push(sh.getName() + ': vazia.'); return; }
    var qtd = ult - LINHA_INICIAL + 1;

    var nomes = sh.getRange(LINHA_INICIAL, COL_NOME, qtd, 1).getValues();
    var rgLink = sh.getRange(LINHA_INICIAL, COL_LINK, qtd, 1);
    var links = rgLink.getValues();

    var novos = 0, corrigidos = 0, iguais = 0, protegidos = 0, foraDoMapa = 0;
    var det = [];

    for (var i = 0; i < qtd; i++) {
      var nome = String(nomes[i][0] || '').trim();
      if (!nome) continue;

      var novo = mapa[chave(nome)];
      if (!novo) { foraDoMapa++; continue; }

      var atual = String(links[i][0] || '').trim();
      var linha = LINHA_INICIAL + i;

      if (!atual) {
        links[i][0] = novo; novos++;
        det.push('  C' + linha + '  NOVO       ' + nome);
      } else if (atual.indexOf('http') !== 0) {
        protegidos++;                       // texto/headline: nao sobrescreve
        det.push('  C' + linha + '  PROTEGIDA  ' + nome + '  (celula tem texto, nao link)');
      } else if (idDoDrive(atual) === idDoDrive(novo)) {
        iguais++;
      } else {
        links[i][0] = novo; corrigidos++;
        det.push('  C' + linha + '  CORRIGIDO  ' + nome);
        det.push('             de: ' + atual);
        det.push('             pa: ' + novo);
      }
    }

    if (!simular) rgLink.setValues(links);

    // ---- repinta a coluna A conforme tem ou nao link
    var pintadas = 0;
    if (REPINTAR_COLUNA_A && !simular) {
      var rgColA = sh.getRange(LINHA_INICIAL, COL_NOME, qtd, 1);
      var fundos = rgColA.getBackgrounds();
      for (var j = 0; j < qtd; j++) {
        if (!String(nomes[j][0] || '').trim()) continue;
        var temLink = String(links[j][0] || '').trim().indexOf('http') === 0;
        var cor = temLink ? VERDE : VERMELHO;
        if (fundos[j][0] !== cor) { fundos[j][0] = cor; pintadas++; }
      }
      rgColA.setBackgrounds(fundos);
    }

    totalNovos += novos;
    totalCorrigidos += corrigidos;

    log.push(sh.getName() + '  (ID ' + id + ')');
    log.push('  ' + novos + ' novos | ' + corrigidos + ' corrigidos | ' + iguais + ' ja corretos | '
             + protegidos + ' protegidos | ' + foraDoMapa + ' fora do mapa | ' + pintadas + ' celulas repintadas');
    if (det.length) log.push(det.join('\n'));
    log.push('');
  });

  if (!simular) SpreadsheetApp.flush();

  log.push('TOTAL: ' + totalNovos + ' novos, ' + totalCorrigidos + ' corrigidos.');
  Logger.log(log.join('\n'));
  ss.toast(simular
    ? 'Simulacao pronta. Veja Execucoes > Registros.'
    : totalNovos + ' novos, ' + totalCorrigidos + ' corrigidos.', 'BEKAS', 8);
}

// ---------------------------------------------------------------- APOIO
/** Abre a planilha pelo ID; cai para a planilha ativa se ID_PLANILHA estiver vazio. */
function planilha() {
  var ss = ID_PLANILHA ? SpreadsheetApp.openById(ID_PLANILHA) : SpreadsheetApp.getActive();
  if (!ss) throw new Error('Planilha nao encontrada. Preencha ID_PLANILHA no topo do script.');
  return ss;
}

/** Normaliza nomes: caixa, extensao, barra do Drive e espacos. */
function chave(s) {
  return String(s || '').trim().toLowerCase()
    .replace(/\.(mp4|mov)$/, '')
    .replace(/\//g, '-')
    .replace(/\s+/g, ' ');
}

/** Extrai o file id de uma URL do Drive, para comparar links iguais com formatos diferentes. */
function idDoDrive(url) {
  var m = String(url || '').match(/[-\w]{25,}/);
  return m ? m[0] : String(url || '');
}

function abaPorId(ss, id) {
  var r = null;
  ss.getSheets().forEach(function (sh) { if (!r && sh.getSheetId() === id) r = sh; });
  return r;
}
