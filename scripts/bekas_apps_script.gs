/**
 * BEKAS - preenche LINK (coluna C) e pinta de azul as linhas que estao
 * na aba "MEDIANO E EXCELENTE".
 *
 * COMO USAR
 *   1. Abrir a planilha > Extensoes > Apps Script
 *   2. Apagar o conteudo e colar este arquivo
 *   3. Selecionar a funcao BEKAS_executar e clicar em Executar
 *   4. Autorizar quando pedir (e a sua propria conta)
 *
 * Funcoes soltas, se quiser rodar separado:
 *   BEKAS_simular()        -> so mostra o que faria, nao escreve nada
 *   BEKAS_preencherLinks() -> so preenche a coluna C
 *   BEKAS_pintarLinhas()   -> so pinta
 *   BEKAS_limparPintura()  -> remove a pintura das abas de destino
 */

// ---------------------------------------------------------------- CONFIG
var ABAS_FONTE   = ['MEDIANO E EXCELENTE', 'APENAS LINKS'];      // de onde tirar links
var ABAS_DESTINO = ['-> MARQUES', 'MARQUES', 'marques descarte']; // onde preencher/pintar
var ABA_REF_PINTURA = 'MEDIANO E EXCELENTE';                      // quem define o que pintar

var COL_NOME = 1;    // A
var COL_LINK = 3;    // C
var COL_FIM  = 14;   // N  (ate onde pinta)
var LINHA_INICIAL = 2;
var AZUL = '#a4c2f4';

// Links que nao estao em nenhuma aba (fallback). Pode ir crescendo.
var LINKS_EXTRA = {
  'AD 3 - 50X (23-07-26).mp4':    'https://drive.google.com/file/d/1JMSLyll__p_q0mYVqYA0o3q-NFAIxqxV/view',
  'AD 4 - 30X (23_07_26).mp4':    'https://drive.google.com/file/d/1f-avaTspHsy8-f8m2u4uG6G3RbOodxCa/view',
  'AD 5 - 100X (23-07-26).mp4':   'https://drive.google.com/file/d/1FLpf6KgIPwHZoL6b-BVqcTmM1iWdWQ5Q/view',
  'CXL_AD02-compliance-31-ago':    'https://drive.google.com/file/d/1dOYhOI2FO5a6eejM4QtUqLFzoWedtBQN/view',
  'CXL_AD02_SL-compliance-31-ago': 'https://drive.google.com/file/d/1dOYhOI2FO5a6eejM4QtUqLFzoWedtBQN/view',
  'CXL_AD03-compliance-31-ago':    'https://drive.google.com/file/d/1vO35FPjyEd5ZsIwwNDoMhuKTd6G0LWj7/view',
  'CXL_AD03_SL-compliance-31-ago': 'https://drive.google.com/file/d/1vO35FPjyEd5ZsIwwNDoMhuKTd6G0LWj7/view',
  'CXL_AD04-compliance-31-ago':    'https://drive.google.com/file/d/1ARIefT5xh6InKJiP92-C0PwFOPwX2FSV/view',
  'CXL_AD04_SL-compliance-31-ago': 'https://drive.google.com/file/d/1ARIefT5xh6InKJiP92-C0PwFOPwX2FSV/view',
  'CXL_AD05-compliance-31-ago':    'https://drive.google.com/file/d/1SW15-dw_SQCzy3Ov9-Y-DoBKNELVlB4-/view',
  'CXL_AD05_SL-compliance-31-ago': 'https://drive.google.com/file/d/1SW15-dw_SQCzy3Ov9-Y-DoBKNELVlB4-/view',
  'CXL_AD08-compliance-31-ago':    'https://drive.google.com/file/d/12eoeF5dIkLpYGblGZ2ciD4RjGFPZzJNc/view',
  'CXL_AD08_SL-compliance-31-ago': 'https://drive.google.com/file/d/12eoeF5dIkLpYGblGZ2ciD4RjGFPZzJNc/view'
};

// ---------------------------------------------------------------- ENTRADA
function BEKAS_executar()      { rodar(false, true, true); }
function BEKAS_simular()       { rodar(true,  true, true); }
function BEKAS_preencherLinks(){ rodar(false, true, false); }
function BEKAS_pintarLinhas()  { rodar(false, false, true); }

function BEKAS_limparPintura() {
  var ss = SpreadsheetApp.getActive();
  abasDestino(ss).forEach(function (sh) {
    var ult = sh.getLastRow();
    if (ult >= LINHA_INICIAL) {
      sh.getRange(LINHA_INICIAL, 1, ult - LINHA_INICIAL + 1, COL_FIM).setBackground(null);
    }
    Logger.log('pintura removida: ' + sh.getName());
  });
  SpreadsheetApp.getActive().toast('Pintura removida.', 'BEKAS', 5);
}

// ---------------------------------------------------------------- MOTOR
function rodar(simular, preencher, pintar) {
  var ss = SpreadsheetApp.getActive();
  var mapa = montarMapaDeLinks(ss);
  var pintaveis = nomesParaPintar(ss);
  var log = [];

  Logger.log('Links disponiveis: ' + Object.keys(mapa).length);
  Logger.log('Nomes que devem ser pintados: ' + Object.keys(pintaveis).length);

  abasDestino(ss).forEach(function (sh) {
    var ult = sh.getLastRow();
    if (ult < LINHA_INICIAL) return;
    var qtd = ult - LINHA_INICIAL + 1;

    var nomes = sh.getRange(LINHA_INICIAL, COL_NOME, qtd, 1).getValues();
    var rgLinks = sh.getRange(LINHA_INICIAL, COL_LINK, qtd, 1);
    var links = rgLinks.getValues();

    var novos = 0, jaTinha = 0, ocupada = 0, semLink = 0, pintadas = 0;

    for (var i = 0; i < qtd; i++) {
      var nome = String(nomes[i][0] || '').trim();
      if (!nome) continue;
      var chave = normalizar(nome);
      var atual = String(links[i][0] || '').trim();

      // ---- link
      if (atual.indexOf('http') === 0) {
        jaTinha++;
      } else if (atual) {
        ocupada++; // celula com texto (headline) - nao sobrescreve
      } else if (mapa[chave]) {
        links[i][0] = mapa[chave];
        novos++;
      } else {
        semLink++;
      }

      // ---- pintura
      if (pintaveis[chave]) {
        pintadas++;
        if (pintar && !simular) {
          sh.getRange(LINHA_INICIAL + i, 1, 1, COL_FIM).setBackground(AZUL);
        }
      }
    }

    if (preencher && !simular) rgLinks.setValues(links);

    var linha = sh.getName() + ': +' + novos + ' links novos | ' + jaTinha + ' ja tinham | '
              + ocupada + ' com texto (preservadas) | ' + semLink + ' sem link | '
              + pintadas + ' linhas azuis';
    log.push(linha);
    Logger.log(linha);
  });

  var msg = (simular ? '[SIMULACAO] ' : '') + log.join('\n');
  Logger.log('\n=== RESUMO ===\n' + msg);
  SpreadsheetApp.getActive().toast(simular ? 'Simulacao concluida. Veja Execucoes > Registros.'
                                          : 'Concluido. Veja Execucoes > Registros.', 'BEKAS', 8);
}

// ---------------------------------------------------------------- APOIO
function normalizar(s) {
  return String(s || '')
    .trim()
    .toLowerCase()
    .replace(/\.(mp4|mov)$/, '')
    .replace(/\//g, '-')
    .replace(/\s+/g, ' ');
}

function abasDestino(ss) {
  var vistas = {}, saida = [];
  ss.getSheets().forEach(function (sh) {
    var nome = sh.getName();
    // nunca mexe nas abas fonte
    for (var f = 0; f < ABAS_FONTE.length; f++) {
      if (nome.indexOf(ABAS_FONTE[f]) === 0) return;
    }
    for (var d = 0; d < ABAS_DESTINO.length; d++) {
      if (nome.indexOf(ABAS_DESTINO[d]) !== -1 && !vistas[nome]) {
        vistas[nome] = true; saida.push(sh); return;
      }
    }
  });
  Logger.log('Abas de destino: ' + saida.map(function (s) { return s.getName(); }).join(' | '));
  return saida;
}

function montarMapaDeLinks(ss) {
  var mapa = {};
  // 1) abas fonte primeiro (tem prioridade)
  ABAS_FONTE.forEach(function (prefixo) {
    ss.getSheets().forEach(function (sh) {
      if (sh.getName().indexOf(prefixo) !== 0) return;
      colher(sh, mapa);
    });
  });
  // 2) demais abas com nome/link
  ss.getSheets().forEach(function (sh) { colher(sh, mapa); });
  // 3) fallback fixo
  for (var k in LINKS_EXTRA) {
    var c = normalizar(k);
    if (!mapa[c]) mapa[c] = LINKS_EXTRA[k];
  }
  return mapa;
}

function colher(sh, mapa) {
  var ult = sh.getLastRow();
  if (ult < LINHA_INICIAL || sh.getLastColumn() < COL_LINK) return;
  var vals = sh.getRange(LINHA_INICIAL, 1, ult - LINHA_INICIAL + 1, COL_LINK).getValues();
  for (var i = 0; i < vals.length; i++) {
    var nome = String(vals[i][COL_NOME - 1] || '').trim();
    var link = String(vals[i][COL_LINK - 1] || '').trim();
    if (nome && link.indexOf('http') === 0) {
      var c = normalizar(nome);
      if (!mapa[c]) mapa[c] = link;
    }
  }
}

function nomesParaPintar(ss) {
  var alvo = {};
  ss.getSheets().forEach(function (sh) {
    if (sh.getName().indexOf(ABA_REF_PINTURA) !== 0) return;
    var ult = sh.getLastRow();
    if (ult < LINHA_INICIAL) return;
    sh.getRange(LINHA_INICIAL, COL_NOME, ult - LINHA_INICIAL + 1, 1)
      .getValues()
      .forEach(function (r) {
        var n = String(r[0] || '').trim();
        if (n) alvo[normalizar(n)] = true;
      });
  });
  return alvo;
}
