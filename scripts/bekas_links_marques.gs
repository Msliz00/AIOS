/**
 * BEKAS - copia os links da aba MEDIANO E EXCELENTE para a aba MARQUES.
 *
 * Casa pelo NOME DA MIDIA (coluna A) e grava o link na coluna C.
 * Nao inventa link, nao sobrescreve celula que ja tem conteudo,
 * e nao toca em nenhuma outra aba da planilha.
 *
 * COMO USAR
 *   1. Planilha > Extensoes > Apps Script
 *   2. Apagar o conteudo e colar este arquivo
 *   3. Rodar BEKAS_simular   -> mostra linha a linha o que faria, sem gravar
 *   4. Rodar BEKAS_preencher -> grava
 *   (resultado em Execucoes > Registros)
 */

// ======================================================================
var ABA_FONTE   = 'MEDIANO E EXCELENTE S36 · 31/08–06/09 -> MARQUES';
var ABA_DESTINO = 'MARQUES';
// Se quiser gravar na outra aba MARQUES, troque a linha acima por:
// var ABA_DESTINO = 'S36 · 31/08–06/09 -> MARQUES';

var COL_NOME = 1;        // A = nome da midia
var COL_LINK = 3;        // C = link
var LINHA_INICIAL = 2;   // linha 1 e cabecalho
// ======================================================================

function BEKAS_simular()   { executar(true); }
function BEKAS_preencher() { executar(false); }

function executar(simular) {
  var ss = SpreadsheetApp.getActive();
  var fonte   = acharAba(ss, ABA_FONTE);
  var destino = acharAba(ss, ABA_DESTINO);

  if (!fonte)   { avisar('Aba FONTE nao encontrada: ' + ABA_FONTE + '\n\n' + listarAbas(ss)); return; }
  if (!destino) { avisar('Aba DESTINO nao encontrada: ' + ABA_DESTINO + '\n\n' + listarAbas(ss)); return; }

  // ---- 1. le a fonte: nome -> link
  var mapa = {};
  var vf = fonte.getRange(LINHA_INICIAL, 1, fonte.getLastRow() - LINHA_INICIAL + 1, COL_LINK).getValues();
  for (var i = 0; i < vf.length; i++) {
    var nf = String(vf[i][COL_NOME - 1] || '').trim();
    var lf = String(vf[i][COL_LINK - 1] || '').trim();
    if (nf && lf.indexOf('http') === 0) mapa[chave(nf)] = lf;
  }

  // ---- 2. percorre o destino
  var qtd = destino.getLastRow() - LINHA_INICIAL + 1;
  var nomes = destino.getRange(LINHA_INICIAL, COL_NOME, qtd, 1).getValues();
  var rg    = destino.getRange(LINHA_INICIAL, COL_LINK, qtd, 1);
  var links = rg.getValues();

  var novos = 0, jaTinha = 0, foraDaFonte = 0;
  var det = [];

  for (var j = 0; j < qtd; j++) {
    var nome = String(nomes[j][0] || '').trim();
    if (!nome) continue;
    var linha = LINHA_INICIAL + j;
    var atual = String(links[j][0] || '').trim();
    var link  = mapa[chave(nome)];

    if (!link)      { foraDaFonte++; }
    else if (atual) { jaTinha++; det.push('   C' + linha + '  ' + nome + '  (ja preenchida, mantida)'); }
    else            { links[j][0] = link; novos++; det.push('   C' + linha + '  ' + nome + '  <- ' + link); }
  }

  if (!simular) rg.setValues(links);

  var msg = (simular ? '[SIMULACAO - nada foi gravado]\n\n' : '[GRAVADO]\n\n')
          + 'FONTE:   ' + fonte.getName()   + '  (' + Object.keys(mapa).length + ' midias com link)\n'
          + 'DESTINO: ' + destino.getName() + '\n\n'
          + novos + ' links preenchidos\n'
          + jaTinha + ' ja tinham link (nao alteradas)\n'
          + foraDaFonte + ' midias sem correspondencia na fonte\n\n'
          + det.join('\n');

  Logger.log(msg);
  avisar(msg.length > 1400 ? msg.substring(0, 1400) + '\n\n[...] veja tudo em Execucoes > Registros' : msg);
}

// ---------------------------------------------------------------- apoio
/** Normaliza para comparar nomes: caixa, extensao, barra e espacos. */
function chave(s) {
  return String(s || '').trim().toLowerCase()
    .replace(/\.(mp4|mov)$/, '')
    .replace(/\//g, '-')
    .replace(/\s+/g, ' ');
}

function acharAba(ss, nome) {
  var achada = null;
  ss.getSheets().forEach(function (sh) {
    if (!achada && chave(sh.getName()) === chave(nome)) achada = sh;
  });
  return achada;
}

function listarAbas(ss) {
  return 'Abas da planilha:\n' + ss.getSheets().map(function (s) { return '  ' + s.getName(); }).join('\n');
}

function avisar(texto) {
  try { SpreadsheetApp.getUi().alert(texto); } catch (e) { /* sem UI, so log */ }
}
