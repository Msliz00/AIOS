/**
 * Mapeia 100% das midias de "6 - Operacao: Marques (Aviator)" e de todas
 * as subpastas, em qualquer profundidade.
 *
 * Abas geradas:
 *   MIDIAS UNICAS      - nome que aparece uma unica vez
 *   MIDIAS DUPLICADAS  - nome repetido, uma linha por nome
 *   CORTE 100X+        - corte com multiplicador >= 100
 *   CORTE 90-99X       - inclui os 93x
 *   CORTE 60-89X       - inclui os 60x
 *
 * Cada midia entra em UMA faixa so: nada se repete entre abas.
 *
 * A varredura para sozinha antes do limite de 6 min e salva onde parou,
 * inclusive no meio de uma pasta grande.
 *
 * COMO USAR
 *   1. script.google.com > Novo projeto
 *   2. Colar, salvar (Ctrl+S)
 *   3. Rodar MAPEAR_iniciar   -- botao EXECUTAR, nunca Depuracao
 *   4. Enquanto o log pedir, rodar MAPEAR_continuar
 */

// ===================== CONFIG =====================
var PASTAS_RAIZ = [
  '1TIdIapgcIawzQpwvAObFjkud19ITFGk7'   // 6 - Operacao: Marques (Aviator)
];
var NOME_SAIDA = 'MAPEAMENTO MARQUES - COMPLETO';

// Faixas de corte, uma aba cada. A midia entra na PRIMEIRA que servir.
// Para pegar tambem os 50x, acrescente { nome: 'CORTE 50-59X', min: 50, max: 59.999 }
var FAIXAS = [
  { nome: 'CORTE 100X+',  min: 100, max: Infinity },
  { nome: 'CORTE 90-99X', min: 90,  max: 99.999 },
  { nome: 'CORTE 60-89X', min: 60,  max: 89.999 }
];

// true = so video e imagem. false = todo arquivo que nao seja atalho ou pasta.
var SOMENTE_MIDIA = true;

var LIMITE_MS = 4 * 60 * 1000;
var LOTE = 300;
var NIVEL_MAX = 12;
// ==================================================

function MAPEAR_iniciar()  { motor(true); }
function MAPEAR_continuar() { motor(false); }

/** Refaz so as abas finais a partir do que ja foi varrido. */
function MAPEAR_consolidar() {
  var id = PropertiesService.getScriptProperties().getProperty('ssId');
  if (!id) { Logger.log('Nenhuma varredura em andamento. Rode MAPEAR_iniciar.'); return; }
  consolidar(SpreadsheetApp.openById(id));
}

/** Descarta o progresso. A planilha ja gerada continua no Drive. */
function MAPEAR_zerar() {
  PropertiesService.getScriptProperties().deleteProperty('ssId');
  Logger.log('Progresso descartado. MAPEAR_iniciar vai criar uma planilha nova.');
}

// ---------------------------------------------------------------- MOTOR
// _FILA: A=ID  B=CAMINHO  C=STATUS(P|OK|ERRO)  D=NIVEL  E=TOKEN('' | <token> | FIM)
function motor(reiniciar) {
  var t0 = Date.now();
  var props = PropertiesService.getScriptProperties();
  var ss;

  if (reiniciar) {
    ss = SpreadsheetApp.create(NOME_SAIDA + ' - ' + hoje());
    props.setProperty('ssId', ss.getId());

    var f = ss.getSheets()[0];
    f.setName('_FILA');
    f.getRange(1, 1, 1, 5).setValues([['ID', 'CAMINHO', 'STATUS', 'NIVEL', 'TOKEN']]);
    var raizes = PASTAS_RAIZ.map(function (id) {
      return [id, DriveApp.getFolderById(id).getName(), 'P', 0, ''];
    });
    f.getRange(2, 1, raizes.length, 5).setValues(raizes);

    var b = ss.insertSheet('_BRUTO');
    b.getRange(1, 1, 1, 4).setValues([['NOME', 'LINK', 'PASTA', 'FILEID']]);

    Logger.log('Pastas raiz:\n  ' + raizes.map(function (r) { return r[1]; }).join('\n  ')
             + '\n\nPlanilha criada:\n' + ss.getUrl() + '\n');
  } else {
    var id = props.getProperty('ssId');
    if (!id) { Logger.log('Nada para continuar. Rode MAPEAR_iniciar.'); return; }
    ss = SpreadsheetApp.openById(id);
  }

  var shFila = ss.getSheetByName('_FILA');
  var shBruto = ss.getSheetByName('_BRUTO');
  var fila = shFila.getLastRow() > 1
    ? shFila.getRange(2, 1, shFila.getLastRow() - 1, 5).getValues() : [];

  var ctx = { buffer: [], shBruto: shBruto, shFila: shFila, fila: fila };
  var feitas = 0, achados = 0, ignorados = 0, erros = 0, estourou = false;

  for (var i = 0; i < fila.length; i++) {
    if (fila[i][2] !== 'P') continue;
    if (Date.now() - t0 > LIMITE_MS) { estourou = true; break; }

    var pasta;
    try { pasta = DriveApp.getFolderById(fila[i][0]); }
    catch (e) { fila[i][2] = 'ERRO'; erros++; continue; }

    var caminho = fila[i][1], nivel = Number(fila[i][3]) || 0;
    var tk = String(fila[i][4] || '');

    if (tk !== 'FIM') {
      var arq = tk ? DriveApp.continueFileIterator(tk) : pasta.getFiles();
      while (arq.hasNext()) {
        if (Date.now() - t0 > LIMITE_MS) {
          fila[i][4] = arq.getContinuationToken();
          estourou = true;
          break;
        }
        var a = arq.next(), mt = a.getMimeType();
        if (mt === 'application/vnd.google-apps.shortcut') { ignorados++; continue; }
        if (SOMENTE_MIDIA && mt.indexOf('video/') !== 0 && mt.indexOf('image/') !== 0) { ignorados++; continue; }
        ctx.buffer.push([a.getName(), 'https://drive.google.com/file/d/' + a.getId() + '/view',
                         caminho, a.getId()]);
        achados++;
        if (ctx.buffer.length >= LOTE) salvar(ctx);
      }
      if (estourou) break;
      fila[i][4] = 'FIM';
    }

    if (nivel < NIVEL_MAX) {
      var subs = pasta.getFolders();
      while (subs.hasNext()) {
        var s = subs.next();
        fila.push([s.getId(), caminho + ' / ' + s.getName(), 'P', nivel + 1, '']);
      }
    }

    fila[i][2] = 'OK';
    feitas++;
    if (feitas % 5 === 0) salvar(ctx);
  }

  salvar(ctx);

  var pend = fila.filter(function (r) { return r[2] === 'P'; }).length;
  var log = ['Pastas concluidas nesta execucao: ' + feitas,
             'Pastas ainda na fila: ' + pend,
             'Arquivos achados nesta execucao: ' + achados,
             'Arquivos no total ate agora: ' + Math.max(0, shBruto.getLastRow() - 1),
             'Ignorados nesta execucao (atalho ou nao-midia): ' + ignorados,
             'Pastas sem acesso: ' + erros,
             'Tempo usado: ' + Math.round((Date.now() - t0) / 1000) + 's'];

  if (estourou || pend) {
    log.push('', '>>> PAROU NO TEMPO. Rode MAPEAR_continuar (botao EXECUTAR). <<<',
                 'Nada foi perdido: retoma exatamente de onde parou.');
    Logger.log(log.join('\n'));
    try { ss.toast('Faltam ' + pend + ' pastas. Rode MAPEAR_continuar.', 'MAPEAMENTO', 10); } catch (e) {}
    return;
  }

  log.push('', 'Varredura concluida. Consolidando...');
  Logger.log(log.join('\n'));
  consolidar(ss);
}

function salvar(ctx) {
  if (ctx.buffer.length) {
    ctx.shBruto.getRange(ctx.shBruto.getLastRow() + 1, 1, ctx.buffer.length, 4)
       .setValues(ctx.buffer);
    ctx.buffer.length = 0;
  }
  if (ctx.fila.length) {
    ctx.shFila.getRange(2, 1, ctx.fila.length, 5).setValues(ctx.fila);
  }
  SpreadsheetApp.flush();
}

// ---------------------------------------------------------------- SAIDA
function consolidar(ss) {
  var shBruto = ss.getSheetByName('_BRUTO');
  var n = shBruto.getLastRow() - 1;
  if (n < 1) { Logger.log('Nada coletado.'); return; }
  var vals = shBruto.getRange(2, 1, n, 4).getValues();

  // 1) mesmo file id em varias pastas e UM arquivo so
  var porId = {}, ordemId = [];
  vals.forEach(function (r) {
    var fid = r[3];
    if (!fid) return;
    if (!porId[fid]) { porId[fid] = { nome: r[0], link: r[1], pastas: [r[2]] }; ordemId.push(fid); }
    else if (porId[fid].pastas.indexOf(r[2]) < 0) { porId[fid].pastas.push(r[2]); }
  });

  // 2) agrupa por nome: nome repetido em ids diferentes e copia
  var porNome = {}, ordemNome = [];
  ordemId.forEach(function (fid) {
    var a = porId[fid], k = chave(a.nome);
    if (!porNome[k]) { porNome[k] = []; ordemNome.push(k); }
    porNome[k].push(a);
  });

  var unicas = [], dups = [];
  var faixas = FAIXAS.map(function () { return []; });
  var cortesSemNumero = [];

  ordemNome.forEach(function (k) {
    var g = porNome[k], a = g[0];
    var sit = g.length > 1 ? 'duplicada (' + g.length + ')' : 'unica';

    if (g.length === 1) unicas.push([a.nome, a.link, a.pastas.join(' | ')]);
    else dups.push([a.nome, a.link, g.length,
                    g.map(function (x) { return x.pastas.join(' | '); }).join('  ||  ')]);

    if (String(a.nome).toLowerCase().indexOf('corte') < 0) return;
    var v = maiorMultiplicador(a.nome);
    if (v === null) { cortesSemNumero.push([a.nome, a.link, sit, a.pastas.join(' | ')]); return; }
    for (var fi = 0; fi < FAIXAS.length; fi++) {
      if (v >= FAIXAS[fi].min && v <= FAIXAS[fi].max) {
        faixas[fi].push([a.nome, a.link, v + 'x', sit, a.pastas.join(' | ')]);
        break;   // uma faixa so: nada se repete entre abas
      }
    }
  });

  // maior multiplicador primeiro dentro de cada faixa
  faixas.forEach(function (lista) {
    lista.sort(function (p, q) { return parseFloat(q[2]) - parseFloat(p[2]); });
  });

  var ordem = ['MIDIAS UNICAS', 'MIDIAS DUPLICADAS'];
  escrever(ss, 'MIDIAS UNICAS', ['NOME', 'LINK', 'PASTA'], unicas);
  escrever(ss, 'MIDIAS DUPLICADAS', ['NOME', 'LINK', 'COPIAS', 'PASTAS'], dups);
  FAIXAS.forEach(function (fx, i) {
    escrever(ss, fx.nome, ['NOME', 'LINK', 'MULT', 'SITUACAO', 'PASTA'], faixas[i]);
    ordem.push(fx.nome);
  });
  escrever(ss, 'CORTE SEM NUMERO', ['NOME', 'LINK', 'SITUACAO', 'PASTA'], cortesSemNumero);
  ordem.push('CORTE SEM NUMERO');

  ordem.forEach(function (nome, i) {
    ss.setActiveSheet(ss.getSheetByName(nome));
    ss.moveActiveSheet(i + 1);
  });
  ['_FILA', '_BRUTO'].forEach(function (nome) {
    var sh = ss.getSheetByName(nome);
    if (sh) sh.hideSheet();
  });

  var total = ordemId.length;
  var emDups = dups.reduce(function (s, r) { return s + r[2]; }, 0);

  var l = ['', '================ MAPEAMENTO CONCLUIDO ================',
           'Arquivos distintos: ' + total,
           'Nomes distintos:    ' + ordemNome.length, '',
           '  MIDIAS UNICAS:     ' + unicas.length + ' nomes',
           '  MIDIAS DUPLICADAS: ' + dups.length + ' nomes  (' + emDups + ' arquivos)', ''];
  FAIXAS.forEach(function (fx, i) {
    l.push('  ' + pad(fx.nome, 18) + faixas[i].length + ' midias');
  });
  l.push('  ' + pad('CORTE SEM NUMERO', 18) + cortesSemNumero.length + ' midias  (nome nao declara o multiplicador)');
  l.push('', 'Conferencia: ' + unicas.length + ' + ' + emDups + ' = ' + (unicas.length + emDups)
       + (unicas.length + emDups === total ? '  OK, bate com o total.' : '  ATENCAO: nao bate.'),
       '', 'PLANILHA:', ss.getUrl(),
       '======================================================');
  Logger.log(l.join('\n'));

  try {
    ss.toast(total + ' arquivos mapeados.', 'PRONTO', 15);
  } catch (e) {}
}

function escrever(ss, nome, cab, linhas) {
  var sh = ss.getSheetByName(nome);
  if (sh) sh.clear(); else sh = ss.insertSheet(nome);
  sh.getRange(1, 1, 1, cab.length).setValues([cab]).setFontWeight('bold');
  if (linhas.length) sh.getRange(2, 1, linhas.length, cab.length).setValues(linhas);
  sh.setFrozenRows(1);
  sh.autoResizeColumn(1);
}

// ---------------------------------------------------------------- APOIO
/**
 * Converte o texto antes do "x" em numero, aceitando numero quebrado.
 *   "100" -> 100      "100,5" -> 100.5
 *   "1.000" -> 1000   "1.234,5" -> 1234.5
 * Ponto so e separador de milhar quando os grupos tem 3 digitos.
 */
function valorNum(tok) {
  var s = String(tok || '').replace(/[^\d.,]/g, '');
  if (!s) return null;
  if (/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(s))      s = s.replace(/\./g, '').replace(',', '.');
  else if (/^\d{1,3}(,\d{3})+(\.\d+)?$/.test(s)) s = s.replace(/,/g, '');
  else                                           s = s.replace(',', '.');
  var v = parseFloat(s);
  return isNaN(v) ? null : v;
}

/** Maior multiplicador "<numero>x" do nome, ou null se nao houver. */
function maiorMultiplicador(nome) {
  var re = /(\d[\d.,]*)\s*x/gi, m, maior = null;
  while ((m = re.exec(String(nome || ''))) !== null) {
    var v = valorNum(m[1]);
    if (v !== null && (maior === null || v > maior)) maior = v;
  }
  return maior;
}

function chave(s) {
  return String(s || '').trim().toLowerCase()
    .replace(/\.(mp4|mov|avi|mkv|webm|jpg|jpeg|png|gif)$/, '')
    .replace(/\//g, '-')
    .replace(/\s+/g, ' ');
}

function pad(s, n) {
  s = String(s);
  while (s.length < n) s += ' ';
  return s;
}

function hoje() {
  return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd-MM-yyyy HH:mm');
}
