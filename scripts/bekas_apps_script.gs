/**
 * BEKAS - preenche LINK (coluna C) e pinta de azul as linhas que estao
 * na aba "MEDIANO E EXCELENTE".
 *
 * COMO USAR
 *   1. Abrir a planilha > Extensoes > Apps Script
 *   2. Apagar o conteudo e colar este arquivo
 *   3. Rodar BEKAS_conferirAbas   -> confirma em quais abas vai mexer
 *   4. Rodar BEKAS_simular        -> mostra o resultado sem gravar nada
 *   5. Rodar BEKAS_executar       -> grava
 *   (ver o resultado em Execucoes > Registros)
 *
 * Extras: BEKAS_preencherLinks() | BEKAS_pintarLinhas() | BEKAS_limparPintura()
 */

// ======================================================================
// ABAS QUE O SCRIPT PODE ALTERAR. Nada fora desta lista e tocado.
// Para nao mexer em alguma, basta apagar a linha dela.
// ======================================================================
var ABAS_DESTINO = [
  'S36 · 31/08–06/09 -> MARQUES',   // aba MARQUES da semana 36
  'marques descarte',               // aba de descarte
  'MARQUES'                         // copia avulsa da aba MARQUES  <-- apague se nao quiser
];

// Abas usadas so como FONTE de link. Nunca sao alteradas.
var ABAS_FONTE = [
  'MEDIANO E EXCELENTE S36 · 31/08–06/09 -> MARQUES',
  'APENAS LINKS S36 · 31/08–06/09 -> MARQUES'
];

// Aba que define QUAIS linhas sao pintadas de azul.
var ABA_REF_PINTURA = 'MEDIANO E EXCELENTE S36 · 31/08–06/09 -> MARQUES';

// ----------------------------------------------------------------------
var COL_NOME = 1;    // A
var COL_LINK = 3;    // C
var COL_FIM  = 14;   // N  (ate onde pinta)
var LINHA_INICIAL = 2;
var AZUL = '#a4c2f4';

// Links que nao existem em nenhuma aba (reserva). Pode ir crescendo.
var LINKS_EXTRA = {
  'AD 3 - 50X (23-07-26).mp4':     'https://drive.google.com/file/d/1JMSLyll__p_q0mYVqYA0o3q-NFAIxqxV/view',
  'AD 4 - 30X (23_07_26).mp4':     'https://drive.google.com/file/d/1f-avaTspHsy8-f8m2u4uG6G3RbOodxCa/view',
  'AD 5 - 100X (23-07-26).mp4':    'https://drive.google.com/file/d/1FLpf6KgIPwHZoL6b-BVqcTmM1iWdWQ5Q/view',
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
function BEKAS_executar()       { rodar(false, true, true); }
function BEKAS_simular()        { rodar(true,  true, true); }
function BEKAS_preencherLinks() { rodar(false, true, false); }
function BEKAS_pintarLinhas()   { rodar(false, false, true); }

/** Mostra exatamente quais abas serao alteradas e quais serao so lidas. */
function BEKAS_conferirAbas() {
  var ss = SpreadsheetApp.getActive();
  var l = ['ABAS QUE SERAO ALTERADAS:'];
  ABAS_DESTINO.forEach(function (n) {
    var sh = acharAba(ss, n);
    l.push('  ' + (sh ? 'OK   ' + sh.getName() : 'NAO ENCONTRADA -> ' + n));
  });
  l.push('', 'ABAS USADAS SO COMO FONTE (nao alteradas):');
  ABAS_FONTE.forEach(function (n) {
    var sh = acharAba(ss, n);
    l.push('  ' + (sh ? 'OK   ' + sh.getName() : 'NAO ENCONTRADA -> ' + n));
  });
  l.push('', 'TODAS AS ABAS DA PLANILHA:');
  ss.getSheets().forEach(function (sh) {
    var alvo = ABAS_DESTINO.some(function (n) { return mesmaAba(n, sh.getName()); });
    l.push('  ' + (alvo ? '[ALTERA] ' : '[intacta] ') + sh.getName());
  });
  Logger.log(l.join('\n'));
  SpreadsheetApp.getUi().alert(l.join('\n'));
}

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
  var destinos = abasDestino(ss);
  if (!destinos.length) {
    Logger.log('ERRO: nenhuma aba de ABAS_DESTINO foi encontrada. Rode BEKAS_conferirAbas.');
    return;
  }

  var mapa = montarMapaDeLinks(ss);
  var pintaveis = nomesParaPintar(ss);
  var log = [];

  Logger.log('Links disponiveis: ' + Object.keys(mapa).length);
  Logger.log('Nomes que devem ser pintados: ' + Object.keys(pintaveis).length);

  destinos.forEach(function (sh) {
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
        ocupada++;                    // celula com texto (headline): nao sobrescreve
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

  Logger.log('\n=== RESUMO ' + (simular ? '(SIMULACAO, nada gravado)' : '') + ' ===\n' + log.join('\n'));
  SpreadsheetApp.getActive().toast(
    simular ? 'Simulacao concluida. Veja Execucoes > Registros.'
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

/** Compara nome de aba ignorando caixa, barras e espacos repetidos. Exato, nao parcial. */
function mesmaAba(a, b) {
  return normalizar(a) === normalizar(b);
}

function acharAba(ss, nome) {
  var achada = null;
  ss.getSheets().forEach(function (sh) {
    if (!achada && mesmaAba(nome, sh.getName())) achada = sh;
  });
  return achada;
}

function abasDestino(ss) {
  var saida = [];
  ABAS_DESTINO.forEach(function (n) {
    var sh = acharAba(ss, n);
    if (sh) saida.push(sh);
    else Logger.log('AVISO: aba de destino nao encontrada -> ' + n);
  });
  Logger.log('Abas que serao alteradas: ' + saida.map(function (s) { return s.getName(); }).join(' | '));
  return saida;
}

function montarMapaDeLinks(ss) {
  var mapa = {};
  // 1) abas fonte tem prioridade
  ABAS_FONTE.forEach(function (n) {
    var sh = acharAba(ss, n);
    if (sh) colher(sh, mapa);
    else Logger.log('AVISO: aba fonte nao encontrada -> ' + n);
  });
  // 2) as proprias abas de destino tambem servem de fonte
  abasDestino(ss).forEach(function (sh) { colher(sh, mapa); });
  // 3) reserva fixa
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
  var sh = acharAba(ss, ABA_REF_PINTURA);
  if (!sh) { Logger.log('AVISO: aba de referencia da pintura nao encontrada.'); return alvo; }
  var ult = sh.getLastRow();
  if (ult < LINHA_INICIAL) return alvo;
  sh.getRange(LINHA_INICIAL, COL_NOME, ult - LINHA_INICIAL + 1, 1)
    .getValues()
    .forEach(function (r) {
      var n = String(r[0] || '').trim();
      if (n) alvo[normalizar(n)] = true;
    });
  return alvo;
}
