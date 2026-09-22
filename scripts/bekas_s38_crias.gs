/**
 * BEKAS S38 - preenche os links pendentes da coluna C a partir da planilha
 * CRIAS MARQUES - LINK.
 *
 * Confere cada link contra o mapeamento real do Drive e avisa nas divergencias.
 * Nao sobrescreve celula que ja tem link.
 *
 * COMO USAR
 *   1. Abrir a planilha BEKAS > Extensoes > Apps Script
 *   2. Apagar tudo e colar este arquivo
 *   3. Ctrl+S para salvar
 *   4. Rodar S38_simular  -> mostra o que faria, sem gravar
 *   5. Rodar S38_aplicar  -> grava
 *   Resultado em Execucoes > Registros.
 */

// ===================== CONFIG =====================
var ID_BEKAS = '1IpISy5pq1vimkKGqx-KNfj3QX-CKg786vfSy6XW_l2g';
var ID_CRIAS = '1Pt8vO6bClfRH4Gx5BbNkYJUTHhxtlpsv1haw3unlXJ4';

// Planilha gerada pela varredura do Drive. Usada so para CONFERIR os links.
// Deixe '' para desligar a conferencia.
var ID_MAPA_DRIVE = '18QuXwGwpkWiLd8CTojXdgOWN6j91U2J27A_5YCzH-yk';

// Aba de destino na BEKAS. Se souber o ID (gid), preencha e o nome e ignorado.
var ID_ABA_S38 = 0;
var NOME_ABA_S38 = 'S38 · 14–20/09 -> MARQUES';

// Quando a CRIAS e o Drive discordam: false usa a CRIAS (o que voce pediu),
// true usa o link real do Drive.
var PREFERIR_DRIVE = false;

// Colunas
var COL_NOME = 1;   // A nas duas planilhas
var COL_LINK = 3;   // C nas duas planilhas
var LINHA_INICIAL = 2;

// Repinta a coluna A: verde com link, vermelho sem. Desligado por padrao.
var REPINTAR_COLUNA_A = false;
var VERDE = '#b6d7a8';
var VERMELHO = '#ea9999';
// ==================================================

function S38_simular() { rodar(true); }
function S38_aplicar() { rodar(false); }

/** Lista nome + ID de cada aba da BEKAS. Use se a aba S38 nao for encontrada. */
function S38_listarAbas() {
  var l = ['ABAS DA BEKAS (ID -> nome):'];
  SpreadsheetApp.openById(ID_BEKAS).getSheets().forEach(function (sh) {
    l.push('  ' + sh.getSheetId() + '  ' + sh.getName());
  });
  Logger.log(l.join('\n'));
}

// ---------------------------------------------------------------- MOTOR
function rodar(simular) {
  var bekas = SpreadsheetApp.openById(ID_BEKAS);
  var destino = acharS38(bekas);
  if (!destino) return;

  var crias = lerCrias();
  var drive = lerMapaDrive();

  var log = ['=== ' + (simular ? 'SIMULACAO (nada gravado)' : 'GRAVANDO') + ' ===',
             'Destino: ' + destino.getName() + '  (ID ' + destino.getSheetId() + ')',
             'CRIAS: ' + crias.total + ' midias com link',
             'Mapa do Drive: ' + drive.total + ' midias' + (drive.total ? '' : ' (conferencia desligada)'),
             'Em caso de divergencia usa: ' + (PREFERIR_DRIVE ? 'DRIVE' : 'CRIAS'),
             ''];

  var ult = destino.getLastRow();
  if (ult < LINHA_INICIAL) { Logger.log('Aba de destino vazia.'); return; }
  var qtd = ult - LINHA_INICIAL + 1;

  var nomes = destino.getRange(LINHA_INICIAL, COL_NOME, qtd, 1).getValues();
  var rgLink = destino.getRange(LINHA_INICIAL, COL_LINK, qtd, 1);
  var links = rgLink.getValues();

  var preenchidos = 0, jaTinha = 0, protegidos = 0, semFonte = 0;
  var det = [], aprox = [], diverg = [];

  for (var i = 0; i < qtd; i++) {
    var nome = String(nomes[i][0] || '').trim();
    if (!nome) continue;
    var linha = LINHA_INICIAL + i;
    var atual = String(links[i][0] || '').trim();

    if (atual.indexOf('http') === 0) { jaTinha++; continue; }
    if (atual) { protegidos++; det.push('  C' + linha + '  PROTEGIDA  ' + nome + '  (celula tem texto)'); continue; }

    var achado = buscar(crias, nome);
    if (!achado) { semFonte++; continue; }
    if (achado.aproximado) aprox.push('  C' + linha + '  ' + nome + '  ~  ' + achado.nomeFonte);

    var link = achado.link;
    var noDrive = drive.total ? buscar(drive, nome) : null;
    if (noDrive && idDoDrive(noDrive.link) !== idDoDrive(link)) {
      diverg.push('  C' + linha + '  ' + nome
                + '\n        CRIAS: ' + link
                + '\n        DRIVE: ' + noDrive.link);
      if (PREFERIR_DRIVE) link = noDrive.link;
    }

    links[i][0] = link;
    preenchidos++;
    det.push('  C' + linha + '  PREENCHIDO  ' + nome);
  }

  if (!simular) {
    rgLink.setValues(links);
    if (REPINTAR_COLUNA_A) {
      var rgColA = destino.getRange(LINHA_INICIAL, COL_NOME, qtd, 1);
      var fundos = rgColA.getBackgrounds();
      for (var j = 0; j < qtd; j++) {
        if (!String(nomes[j][0] || '').trim()) continue;
        fundos[j][0] = String(links[j][0] || '').trim().indexOf('http') === 0 ? VERDE : VERMELHO;
      }
      rgColA.setBackgrounds(fundos);
    }
    SpreadsheetApp.flush();
  }

  log.push(preenchidos + ' preenchidos | ' + jaTinha + ' ja tinham link | '
         + protegidos + ' protegidos | ' + semFonte + ' sem correspondencia na CRIAS');
  log.push('');
  if (det.length)     log.push('DETALHE:', det.join('\n'), '');
  if (aprox.length)   log.push('MATCH APROXIMADO (confira estes):', aprox.join('\n'), '');
  if (diverg.length)  log.push('*** DIVERGENCIA CRIAS x DRIVE — o link da CRIAS aponta para outro arquivo ***',
                               diverg.join('\n'),
                               'Gravado o link da ' + (PREFERIR_DRIVE ? 'DRIVE' : 'CRIAS') + '.', '');

  Logger.log(log.join('\n'));
  bekas.toast(simular ? 'Simulacao pronta. Veja Execucoes > Registros.'
                      : preenchidos + ' links preenchidos, ' + diverg.length + ' divergencias.', 'S38', 8);
}

// ---------------------------------------------------------------- FONTES
/** Le a CRIAS: coluna A = nome, coluna C = link. */
function lerCrias() {
  var sh = SpreadsheetApp.openById(ID_CRIAS).getSheets()[0];
  var m = novoMapa();
  colher(sh, m);
  return m;
}

/** Le todas as abas do mapeamento do Drive: coluna A = nome, coluna B = link. */
function lerMapaDrive() {
  var m = novoMapa();
  if (!ID_MAPA_DRIVE) return m;
  SpreadsheetApp.openById(ID_MAPA_DRIVE).getSheets().forEach(function (sh) {
    colher(sh, m, 1, 2);
  });
  return m;
}

function novoMapa() { return { exato: {}, solto: {}, total: 0 }; }

function colher(sh, m, colNome, colLink) {
  colNome = colNome || COL_NOME;
  colLink = colLink || COL_LINK;
  var ult = sh.getLastRow();
  if (ult < LINHA_INICIAL) return;
  var larg = Math.max(colNome, colLink);
  var vals = sh.getRange(LINHA_INICIAL, 1, ult - LINHA_INICIAL + 1, larg).getValues();
  for (var i = 0; i < vals.length; i++) {
    var nome = String(vals[i][colNome - 1] || '').trim();
    var link = String(vals[i][colLink - 1] || '').trim();
    if (!nome || link.indexOf('http') !== 0) continue;
    var k = chave(nome);
    if (!m.exato[k]) { m.exato[k] = { link: link, nomeFonte: nome }; m.total++; }
    var s = solta(nome);
    if (!m.solto[s]) m.solto[s] = { link: link, nomeFonte: nome };
  }
}

/** Procura pelo nome normalizado; so entao tenta o casamento solto. */
function buscar(m, nome) {
  var a = m.exato[chave(nome)];
  if (a) return { link: a.link, nomeFonte: a.nomeFonte, aproximado: false };
  var b = m.solto[solta(nome)];
  if (b) return { link: b.link, nomeFonte: b.nomeFonte, aproximado: true };
  return null;
}

// ---------------------------------------------------------------- APOIO
function acharS38(ss) {
  var abas = ss.getSheets();
  var achada = null;

  if (ID_ABA_S38) {
    abas.forEach(function (sh) { if (sh.getSheetId() === ID_ABA_S38) achada = sh; });
    if (achada) return achada;
    Logger.log('Aba de ID ' + ID_ABA_S38 + ' nao existe. Tentando pelo nome.');
  }

  abas.forEach(function (sh) { if (!achada && chave(sh.getName()) === chave(NOME_ABA_S38)) achada = sh; });
  if (achada) return achada;

  // Ultimo recurso: aba que fale de S38 e MARQUES, sem ser descarte nem mediano.
  var cand = abas.filter(function (sh) {
    var n = chave(sh.getName());
    return n.indexOf('s38') >= 0 && n.indexOf('marques') >= 0
        && n.indexOf('descarte') < 0 && n.indexOf('mediano') < 0;
  });
  if (cand.length === 1) {
    Logger.log('Aba encontrada por aproximacao: ' + cand[0].getName() + ' (ID ' + cand[0].getSheetId() + ')');
    return cand[0];
  }

  var l = ['ERRO: nao consegui identificar a aba S38 com seguranca.'];
  if (cand.length > 1) {
    l.push('Candidatas:');
    cand.forEach(function (sh) { l.push('  ' + sh.getSheetId() + '  ' + sh.getName()); });
  }
  l.push('', 'Todas as abas (ID -> nome):');
  abas.forEach(function (sh) { l.push('  ' + sh.getSheetId() + '  ' + sh.getName()); });
  l.push('', 'Copie o ID certo para ID_ABA_S38 no topo do script e rode de novo.');
  Logger.log(l.join('\n'));
  return null;
}

/** Normaliza nomes: caixa, extensao, barra do Drive e espacos. */
function chave(s) {
  return String(s || '').trim().toLowerCase()
    .replace(/\.(mp4|mov)$/, '')
    .replace(/\//g, '-')
    .replace(/\s+/g, ' ');
}

/** Casamento solto: so letras e numeros. Pega espaco e underscore fora do lugar. */
function solta(s) {
  return chave(s).replace(/[^a-z0-9]/g, '');
}

function idDoDrive(url) {
  var m = String(url || '').match(/[-\w]{25,}/);
  return m ? m[0] : String(url || '');
}
