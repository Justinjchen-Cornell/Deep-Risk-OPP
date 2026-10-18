/* Deep-Risk-OPP — data-driven pages (no hardcoded market data) */
(function () {
  var page = document.body.getAttribute('data-page');
  function byId(id) { return document.getElementById(id); }
  function n(x) { return (typeof x === 'number' && isFinite(x)) ? x : null; }
  function usd(x, d) { return x == null ? '—' : '$' + Number(x).toLocaleString('en-US', {minimumFractionDigits: d == null ? 2 : d, maximumFractionDigits: d == null ? 2 : d}); }
  function signed(x, d) { return x == null ? '—' : (x >= 0 ? '+' : '') + Number(x).toFixed(d == null ? 2 : d); }
  function get(url) { return fetch(url + '?v=' + Date.now(), {cache: 'no-store'}).then(function (r) { return r.json(); }); }
  function hardStop(hist, wti) {
    if (!hist || !hist.length || wti == null) return {thr: null, on: false, dist: null};
    var vals = hist.map(function (r) { return n(r.wti); }).filter(function (v) { return v != null; });
    if (vals.length < 60) return {thr: null, on: false, dist: null};
    var sma = vals.slice(-60).reduce(function (a, b) { return a + b; }, 0) / 60;
    var thr = sma * 0.85;
    return {thr: thr, on: (wti < thr || wti < 60), dist: wti - thr};
  }
  function regimeNote(gor) {
    if (gor == null) return 'GOR 数据缺失';
    if (gor >= 45) return '极端区：金相对油贵，避险/需求恐惧占上风';
    if (gor >= 30) return '修复区：油腿主导、金腿滞后，方向未决';
    if (gor >= 20) return '均衡区：油相对金偏贵';
    return '原油泡沫区：油极度昂贵';
  }
  Promise.all([
    get('gor_latest.json'),
    get('capital_flows_latest.json').catch(function () { return null; }),
    get('wti_history.json').catch(function () { return null; }),
    get('history.json').catch(function () { return null; }),
    get('history_weekly.json').catch(function () { return null; }),
    get('weekly_review.json').catch(function () { return null; }),
    get('capital_flows_weekly.json').catch(function () { return null; })
  ]).then(function (out) {
    var g = out[0] || {}, cf = out[1], hist = out[2], dailyDoc = out[3], weeklyDoc = out[4], review = out[5], fw = out[6];
    var d = g.data || {}, s = g.screener || {}, a = g.allocation || {}, c = g.capital_three_flows || {};
    var gold = n((d['黄金期货'] || {}).price), wti = n((d['WTI原油'] || {}).price);
    var brent = n((d['布伦特原油'] || {}).price), dxy = n((d['美元指数DXY'] || {}).price);
    var us10y = n((d['10Y美债收益率'] || {}).price), vix = n((d['VIX恐慌指数'] || {}).price);
    var gorW = n(g.gor_wti), gorB = n(g.gor_brent), pos = n(g.final_position);
    var comp = wti == null ? null : (wti / 69.87 - 1) / (107.60 / 69.87 - 1);
    var gap = wti == null ? null : 107.60 - wti;
    var days = Math.ceil((Date.UTC(2027, 5, 30) - Date.now()) / 86400000);
    var hs = hardStop(hist, wti);
    var oilPctl = n(s.oil_pctl), vixGate = n(s.vix_thr);
    var daily = (dailyDoc && dailyDoc.rows) || [], weekly = (weeklyDoc && weeklyDoc.rows) || [];
    var flow = {total: c.total || '—', direction: c.direction || '—', speed: c.speed || '—'};
    var V = {
      gold: usd(gold, 0), wti: usd(wti), brent: usd(brent), dxy: dxy == null ? '—' : dxy.toFixed(2),
      us10y: us10y == null ? '—' : us10y.toFixed(2) + '%', vix: vix == null ? '—' : vix.toFixed(2),
      gorW: gorW == null ? '—' : gorW.toFixed(2), gorB: gorB == null ? '—' : gorB.toFixed(2),
      regime: g.regime || '—', pos: pos == null ? '—' : pos + '%', verdict: s.verdict || '—',
      comp: comp == null ? '—' : (comp * 100).toFixed(1) + '%', gap: gap == null ? '—' : usd(gap),
      days: days + ' 天', oil: a['油气'] == null ? 0 : a['油气'], goldP: a['黄金'] == null ? 0 : a['黄金'],
      cash: a['现金'] == null ? 0 : a['现金'], astock: a['A股'] == null ? 0 : a['A股'],
      copper: a['铜'] == null ? 0 : a['铜'], oilPctl: oilPctl == null ? '—' : (oilPctl * 100).toFixed(0) + '%',
      vixGate: vixGate == null ? '—' : vixGate.toFixed(2), hsOn: hs.on,
      hsThr: hs.thr == null ? '—' : usd(hs.thr), hsDist: hs.dist == null ? '—' : usd(hs.dist),
      updated: g.updated || '—', flowTotal: flow.total, flowDir: flow.direction, flowSpeed: flow.speed,
      s1: s.s1, s2: s.s2, s3: s.s3, npass: s.npass
    };
    V.summary = 'GOR(WTI) ' + V.gorW + ' · GOR(Brent) ' + V.gorB + '（合成） · ' + V.regime + ' · 仓位 ' + V.pos +
      ' · 筛选器 ' + V.verdict + ' · 合同 ' + V.comp + '（距目标 ' + V.gap + '）';
    V.interpret = regimeNote(gorW) + '。油分位 ' + V.oilPctl + '；10Y ' + V.us10y + '，DXY ' + V.dxy + '，VIX ' + V.vix +
      '（门槛 ' + V.vixGate + '）。硬止损 ' + (hs.on ? '已触发' : '未触发') +
      (hs.thr == null ? '' : '（阈值 ' + V.hsThr + '，距离 ' + V.hsDist + '）') +
      '。三流：' + V.flowTotal + ' / ' + V.flowDir + ' / ' + V.flowSpeed + '。';
    V.actions = [];
    if (hs.on) {
      V.actions.push('硬止损已触发：油气仓位降至 5%。');
      V.actions.push('检查 WTI $75 Put 赔付对账，计算净影响。');
      V.actions.push('现金优先，等待 WTI 收复阈值后再评估。');
    } else if (s.s2 && s.s3) {
      V.actions.push('投降签名成立：VIX ≥ 门槛且油 ≤ 十年 P25，机器扳机打印。');
      V.actions.push('按卡片配置执行：油气 ' + V.oil + '%、黄金 ' + V.goldP + '%、现金 ' + V.cash + '%。');
      V.actions.push('分批，不追；保留 Put 保护。');
    } else if (vixGate != null && vix != null && vix >= vixGate) {
      V.actions.push('VIX 已过门槛（' + V.vix + ' ≥ ' + V.vixGate + '），但油未到底部四分位：观察，不追。');
      V.actions.push('维持仓位 ' + V.pos + '；等油分位 ≤ 25% 的共振。');
    } else {
      V.actions.push('硬止损未触发：维持仓位 ' + V.pos + '。');
      V.actions.push('油气 ' + V.oil + '% · 黄金 ' + V.goldP + '% · 现金 ' + V.cash + '% · A股 ' + V.astock + '%。');
      V.actions.push('等待信号：VIX ≥ ' + V.vixGate + ' 且油分位 ≤ 25%，或 WTI 跌破 ' + V.hsThr + '。');
    }
    V.tools = [
      {name: 'WTI Put / 硬止损', status: hs.on ? '触发' : '未触发', cls: hs.on ? 'bad' : 'ok',
       text: hs.on ? '油气降至 5%，检查赔付。' : '阈值 ' + V.hsThr + '，距离 ' + V.hsDist + '。'},
      {name: 'SPY/IO Straddle', status: vix == null ? '—' : (vix < 17 ? '可建仓' : (vix > 25 ? '转 Put' : '等待')),
       cls: (vix != null && vix < 17) ? 'ok' : 'warn', text: 'VIX ' + V.vix + '；<17 建 Straddle，>25 改 Put。'},
      {name: 'A 股 Put', status: V.astock < 10 ? '不需要' : '可考虑', cls: V.astock < 10 ? 'ok' : 'warn',
       text: 'A 股配置 ' + V.astock + '%。'},
      {name: '现金 / 黄金', status: '防御', cls: 'ok', text: '现金 ' + V.cash + '%，黄金 ' + V.goldP + '%。'}
    ];
    V.checks = [
      ['硬止损', hs.on ? '触发' : '未触发', hs.on ? 'bad' : 'ok'],
      ['VIX 门槛', V.vix + ' / ' + V.vixGate, (vix != null && vixGate != null && vix >= vixGate) ? 'warn' : 'ok'],
      ['油分位', V.oilPctl, (oilPctl != null && oilPctl <= 0.25) ? 'warn' : 'ok'],
      ['总仓位', V.pos, 'ok'],
      ['合同完成度', V.comp, 'ok'],
      ['三流', V.flowDir + ' / ' + V.flowSpeed, 'ok']
    ];
    V.daily = daily; V.weekly = weekly;
    render(V, g, cf, hist, review, fw);
  });

  function weekPair(V) {
    var w = V.weekly || [];
    return w.length >= 2 ? {prev: w[w.length - 2], curr: w[w.length - 1]} : null;
  }
  function weeklyReview(V) {
    var p = weekPair(V);
    if (!p) return '本周对比数据待生成。';
    var a = p.prev, b = p.curr;
    return '本周 GOR ' + (b.gor_wti == null ? '—' : b.gor_wti.toFixed(2)) +
      '（上周 ' + (a.gor_wti == null ? '—' : a.gor_wti.toFixed(2)) + '，' + signed((b.gor_wti || 0) - (a.gor_wti || 0), 2) + '）· ' +
      'WTI ' + usd(b.wti) + '（上周 ' + usd(a.wti) + '，' + signed((b.wti || 0) - (a.wti || 0), 2) + '）· ' +
      'VIX ' + (b.vix == null ? '—' : b.vix.toFixed(2)) + '（上周 ' + (a.vix == null ? '—' : a.vix.toFixed(2)) + '，' + signed((b.vix || 0) - (a.vix || 0), 2) + '）· ' +
      '仓位 ' + (b.position == null ? '—' : b.position + '%') + '（' + (a.position == null ? '上周未记录' : '上周 ' + a.position + '%') + '）。' +
      '解读：' + regimeNote(b.gor_wti) + '；' + ((b.vix != null && b.vix >= V.vixGate && b.wti != null && b.wti < 60) ? '投降签名成立' : '筛选器 ' + V.verdict + '，尚未触发投降签名') + '；合同 ' + V.comp + '。';
  }
  function changeLine(V) {
    var p = weekPair(V);
    if (!p) return '本周对比数据待生成';
    var a = p.prev, b = p.curr;
    return '本周 vs 上周：GOR ' + (b.gor_wti == null ? '—' : b.gor_wti.toFixed(2)) + '（上周 ' + (a.gor_wti == null ? '—' : a.gor_wti.toFixed(2)) + '，' + signed((b.gor_wti || 0) - (a.gor_wti || 0), 2) + '）· WTI ' + usd(b.wti) + '（上周 ' + usd(a.wti) + '，' + signed((b.wti || 0) - (a.wti || 0), 2) + '）· VIX ' + (b.vix == null ? '—' : b.vix.toFixed(2)) + '（上周 ' + (a.vix == null ? '—' : a.vix.toFixed(2)) + '，' + signed((b.vix || 0) - (a.vix || 0), 2) + '）';
  }

  function historyTable(rows, limit) {
    rows = (rows || []).slice(-(limit || 10)).reverse();
    var h = '<table><thead><tr><th>周</th><th>日期</th><th>GOR</th><th>WTI</th><th>VIX</th><th>仓位</th><th>区间</th></tr></thead><tbody>';
    rows.forEach(function (r) {
      h += '<tr><td>' + (r.week || '—') + '</td><td>' + (r.date || '—') + '</td><td>' +
        (r.gor_wti == null ? '—' : r.gor_wti.toFixed(2)) + '</td><td>' +
        (r.wti == null ? '—' : '$' + r.wti.toFixed(2)) + '</td><td>' +
        (r.vix == null ? '—' : r.vix.toFixed(2)) + '</td><td>' +
        (r.position == null ? '—' : r.position + '%') + '</td><td>' + (r.regime || '—') + '</td></tr>';
    });
    return h + '</tbody></table>';
  }

  var ICONS = {
    gold: '<circle cx="12" cy="12" r="8"/><path d="M9 9h6M9 15h6M12 6v12"/>',
    oil: '<path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z"/>',
    dollar: '<path d="M12 3v18M16 7.5c0-1.4-1.8-2.5-4-2.5s-4 1.1-4 2.5 1.8 2.5 4 2.5 4 1.1 4 2.5-1.8 2.5-4 2.5-4-1.1-4-2.5"/>',
    yield: '<path d="M4 18l5-6 4 3 7-9"/><path d="M16 6h4v4"/>',
    vix: '<path d="M3 12h4l2-7 4 14 2-7h6"/>',
    gor: '<circle cx="8" cy="12" r="4"/><circle cx="16" cy="12" r="4"/><path d="M12 6v12"/>',
    shield: '<path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6l7-3z"/>',
    bank: '<path d="M3 9l9-6 9 6"/><path d="M5 9v8M9 9v8M15 9v8M19 9v8M3 21h18"/>',
    flow: '<path d="M3 8c4 0 4 8 8 8s4-8 8-8"/><path d="M3 14c4 0 4 4 8 4s4-4 8-4"/>',
    history: '<circle cx="12" cy="12" r="8"/><path d="M12 7v5l3 2"/>',
    alert: '<path d="M12 3l9 17H3L12 3z"/><path d="M12 9v5M12 17h.01"/>',
    target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>',
    globe: '<circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c3 3 3 13 0 16M12 4c-3 3-3 13 0 16"/>',
    pie: '<path d="M12 3v9h9"/><path d="M21 12a9 9 0 1 1-9-9"/>'
  };
  var META = {
    '黄金': {icon:'gold', tone:'gold', note:'避险/储备资产 · GOR 分子'},
    'WTI': {icon:'oil', tone:'oil', note:'美国基准原油 · GOR 分母'},
    'Brent': {icon:'oil', tone:'oil', note:'全球基准 · 卡面为 WTI×1.06 合成'},
    'DXY': {icon:'dollar', tone:'blue', note:'美元指数 · >99 向心坍缩区间'},
    '10Y': {icon:'yield', tone:'amber', note:'长端利率 · 5% 上方压制估值'},
    'VIX': {icon:'vix', tone:'red', note:'恐慌指数 · ≥22.5 才是投降门槛'},
    'GOR(WTI)': {icon:'gor', tone:'gold', note:'金油比 · 越低油越强'},
    'GOR(Brent)': {icon:'gor', tone:'gold', note:'Brent 腿 · 合成口径'},
    '仓位': {icon:'shield', tone:'green', note:'总仓位 · 机器输出'}
  };
  function icon(name, size) {
    var p = ICONS[name] || ICONS.gold;
    return '<svg class="icon" width="' + (size || 18) + '" height="' + (size || 18) + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' + p + '</svg>';
  }
  function secTitle(n, ic, title, sub) {
    return '<div class="sec-title"><span class="sec-num">' + n + '</span><span class="sec-ic">' + icon(ic, 18) + '</span><div><div class="sec-h">' + title + '</div><div class="sec-s">' + sub + '</div></div></div>';
  }
  function numList(items) { return '<ol class="num-list">' + items.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ol>'; }
  function chartNote(text) { return '<div class="chart-note">' + text + '</div>'; }
  function legendBar() {
    return '<div class="legend-bar">' + tag('红 = 风险/触发', 'bad') + tag('黄 = 观察', 'warn') + tag('绿 = 正常/通过', 'ok') + tag('金 = 主指标', 'gold') + '<span class="muted">数据：卡面 / FRED / 机构转引，均已标注</span></div>';
  }

  function tag(txt, cls) { return '<span class="tag ' + (cls || '') + '">' + txt + '</span>'; }
  function metric(k, v, delta, cls) {
    var m = META[k] || {icon: 'gold', tone: 'neutral', note: ''};
    return '<div class="metric"><div class="m-top"><span class="m-ic ' + m.tone + '">' + icon(m.icon, 17) + '</span><span class="k">' + k + '</span></div>' +
      '<div class="v">' + v + '</div>' +
      (delta ? '<div class="d ' + (cls || 'flat') + '">' + delta + '</div>' : '') +
      '<div class="m-note">' + m.note + '</div></div>';
  }
  function changeCard(k, v, s, cls) {
    return '<div class="change"><div class="k">' + k + '</div><div class="v ' + (cls || '') + '">' + v + '</div><div class="s">' + s + '</div></div>';
  }
  function changeCards(V) {
    var p = weekPair(V), cards = [];
    if (p) {
      var a = p.prev, b = p.curr, dg = (b.gor_wti || 0) - (a.gor_wti || 0), dw = (b.wti || 0) - (a.wti || 0), dv = (b.vix || 0) - (a.vix || 0);
      cards.push(changeCard('GOR 本周 vs 上周', (b.gor_wti == null ? '—' : b.gor_wti.toFixed(2)), '上周 ' + (a.gor_wti == null ? '—' : a.gor_wti.toFixed(2)) + ' · ' + signed(dg, 2), dg >= 0 ? 'up' : 'down'));
      cards.push(changeCard('WTI 本周 vs 上周', usd(b.wti), '上周 ' + usd(a.wti) + ' · ' + signed(dw, 2), dw >= 0 ? 'up' : 'down'));
      cards.push(changeCard('VIX 本周 vs 上周', b.vix == null ? '—' : b.vix.toFixed(2), '上周 ' + (a.vix == null ? '—' : a.vix.toFixed(2)) + ' · ' + signed(dv, 2), dv >= 0 ? 'up' : 'down'));
      cards.push(changeCard('仓位 / 区间', (b.position == null ? '—' : b.position + '%') + ' / ' + (b.regime || '—'), (a.position == null ? '上周未记录' : '上周 ' + a.position + '%') + ' / ' + (a.regime || '—'), 'flat'));
    }
    cards.push(changeCard('合同 / 硬止损', V.comp + ' / ' + (V.hsOn ? '触发' : '未触发'), '距 $107.60 还差 ' + V.gap + ' · 阈值 ' + V.hsThr, V.hsOn ? 'up' : 'down'));
    return cards.join('');
  }
  function screenTags(V) {
    return tag('拆腿 ' + (V.s1 ? '通过' : '未过'), V.s1 ? 'ok' : 'bad') +
      tag('恐慌 ' + (V.s2 ? '通过' : '未过'), V.s2 ? 'ok' : 'warn') +
      tag('油分位 ' + (V.s3 ? '通过' : '未过'), V.s3 ? 'ok' : 'warn');
  }

  function stageHTML(V) {
    var s2 = V.s2, s3 = V.s3, cap = s2 && s3;
    var st = [
      ['01', '蓄力', 'QT/购金/利差', 'done'],
      ['02', '出拳', '油价/通胀/紧缩', (V.gorW >= 30 && !cap) ? 'active' : (V.gorW < 30 ? 'done' : '')],
      ['03', '坍缩', '资本回中心', (V.vix != null && V.vixGate != null && V.vix >= V.vixGate) ? 'active' : ''],
      ['04', '抄底', '收购/重置', '']
    ];
    return '<div class="stage-row">' + st.map(function (x) {
      return '<div class="stage ' + x[3] + '"><div class="num">' + x[0] + '</div><div class="name">' + x[1] + '</div><div class="desc">' + x[2] + '</div></div>';
    }).join('') + '</div>';
  }
  function adviceItems(V) {
    var cls = V.hsOn ? 'bad' : (V.s2 && V.s3 ? 'ok' : 'warn');
    return V.actions.map(function (x, i) {
      return '<li><span class="tag ' + cls + '">' + (i === 0 ? '首要' : '执行') + '</span>' + x + '</li>';
    }).join('');
  }
  function timelineHTML(V) {
    var rows = [
      ['现在', 'WTI ' + V.wti + ' · GOR ' + V.gorW + ' · 仓位 ' + V.pos],
      ['合同', '目标 $107.60 · 还差 ' + V.gap + ' · ' + V.days],
      ['2026Q4', 'COFER 2026Q3（约 12 月底）· GOR 42/40 观察'],
      ['风险', 'VIX ≥ ' + V.vixGate + ' 且油分位 ≤ 25% 才是投降签名'],
      ['数据', '更新 ' + V.updated]
    ];
    return '<div class="timeline">' + rows.map(function (r) { return '<div class="row"><span class="when">' + r[0] + '</span><span>' + r[1] + '</span></div>'; }).join('') + '</div>';
  }

  function render(V, g, cf, hist, review, fw) {
    var badge = byId('gorBadge');
    if (badge) {
      badge.textContent = 'GOR ' + V.gorW + ' · ' + V.regime;
      badge.className = 'gor-badge' + ((V.gorW >= 45) ? ' alert' : '');
    }
    var app = byId('app');
    if (!app) return;
    if (page === 'capital') { app.innerHTML = capitalHTML(V, cf, review, fw); makeCapitalCharts(V, cf, fw); }
    else if (page === 'hedge') { app.innerHTML = hedgeHTML(V); makeAllocChart(V, 'c-alloc'); makeWeeklyGorChart(V, 'c-week-h'); }
    else { app.innerHTML = decisionHTML(V, g, review); makeGorChart(V, 'c-gor-d'); makeAllocChart(V, 'c-alloc-d'); makeWeeklyGorChart(V, 'c-week-d'); makeWtiGorChart(V, 'c-wti-gor'); }
  }

  function reviewHTML(review, V) {
    if (!review) return '';
    function st(s) { return s === 'match' ? '一致' : s === 'near' ? '接近' : s === 'diff' ? '差异' : '参考'; }
    function stCls(s) { return s === 'match' ? 'ok' : s === 'near' ? 'warn' : s === 'diff' ? 'bad' : ''; }
    var rows = (review.key_data || []).map(function (r) {
      return '<tr><td>' + r.label + '</td><td>' + r.report + '</td><td>' + r.ours + '</td><td>' + tag(st(r.status), stCls(r.status)) + '<div class="muted" style="font-size:10px">' + (r.note || '') + '</div></td></tr>';
    }).join('');
    var agree = (review.agreements || []).map(function (x) { return '<li>' + x + '</li>'; }).join('');
    var diff = (review.differences || []).map(function (x) { return '<li>' + x + '</li>'; }).join('');
    var forks = (review.forks || []).map(function (f) {
      return '<div class="fork"><div class="fh">' + f.title + '</div><div class="fk">盯：' + f.watch + '</div><div class="fk bad">证伪：' + f.falsify + '</div></div>';
    }).join('');
    var flows = (review.flows || []).map(function (x) { return '<li>' + x + '</li>'; }).join('');
    var scen = (review.scenarios || []).map(function (s) {
      return '<div class="scen"><b>' + s.name + '</b><div class="muted">条件：' + s.condition + '</div><div class="muted">倾向：' + s.market + '</div><div class="muted">证伪/重开：' + s.falsify + '</div></div>';
    }).join('');
    return '<div class="card review"><div class="card-head"><span class="ic">🏛️</span><h2>本周机构 vs 机器 · 一周一期</h2>' + tag(review.period || '', 'gold') + '</div>' +
      '<div class="review-thesis">' + (review.thesis || '') + '</div><div class="muted" style="margin-bottom:12px">' + (review.source || '') + ' · ' + (review.title || '') + '</div>' +
      '<div class="compare"><table><thead><tr><th>指标</th><th>机构</th><th>我们</th><th>判定</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<div class="grid2" style="margin-top:14px"><div class="subcard"><h3>一致</h3><ul class="advice">' + agree + '</ul></div><div class="subcard"><h3>差异</h3><ul class="advice">' + diff + '</ul></div></div>' +
      '<div class="fork-grid">' + forks + '</div>' +
      '<div class="grid2"><div class="subcard"><h3>资金与仓位</h3><ul class="advice">' + flows + '</ul></div><div class="subcard"><h3>三种情景</h3>' + scen + '</div></div></div>';
  }

  function decisionHTML(V, g, review) {
    var bars = [['油气', V.oil, '#f06030'], ['黄金', V.goldP, '#f0c040'], ['现金', V.cash, '#64748b'], ['A股', V.astock, '#ef4444'], ['铜', V.copper, '#fb923c']];
    var barsHTML = bars.filter(function (x) { return x[1] > 0; }).map(function (x) { return '<i style="width:' + x[1] + '%;background:' + x[2] + '"></i>'; }).join('');
    var legend = bars.map(function (x) { return '<span><b>' + x[0] + '</b> ' + x[1] + '%</span>'; }).join('');
    var alerts = (g.alerts || []).map(function (a) {
      return '<div class="alert ' + (a.level === 'warning' ? 'warn' : '') + '"><b>' + (a.title || '') + '</b> — ' + (a.detail || '') + '</div>';
    }).join('') || '<div class="muted">无活跃预警</div>';
    var compPct = Math.max(0, Math.min(100, V.comp === '—' ? 0 : parseFloat(V.comp)));
    return '<div class="hero"><div class="hero-kicker">GOR(WTI) · DECISION CARD · ' + V.updated + '</div>' +
      '<div class="hero-row"><div class="hero-num">' + V.gorW + '</div>' +
      '<div class="hero-side"><div class="hero-f">' + V.gold + ' ÷ ' + V.wti + ' = <b>' + V.gorW + ' : 1</b></div>' +
      '<div class="hero-sub">GOR(Brent) ' + V.gorB + '（合成 ' + V.brent + '） · 合同 ' + V.comp + ' · 距目标 ' + V.gap + '</div></div></div>' +
      '<div class="hero-tags">' + tag(V.regime, 'gold') + tag('仓位 ' + V.pos, 'ok') + tag('筛选器 ' + V.verdict, V.verdict === '红' ? 'bad' : 'warn') +
      tag(V.hsOn ? '硬止损 已触发' : '硬止损 未触发', V.hsOn ? 'bad' : 'ok') + '</div></div>' +
      secTitle('01','target','本周状态','价格、GOR、仓位与筛选器') + legendBar() + '<div class="metrics">' + metric('黄金', V.gold) + metric('WTI', V.wti) + metric('Brent', V.brent) +
      metric('DXY', V.dxy) + metric('10Y', V.us10y) + metric('VIX', V.vix) + '</div>' +
      '<div class="grid2"><div class="card"><div class="card-head"><span class="ic">📈</span><h2>GOR 周度</h2></div><div class="chart-sm"><canvas id="c-week-d"></canvas></div>' + chartNote('最近 8 周 GOR：从 46 区间回落到 41，方向向下。') + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">🥧</span><h2>仓位结构</h2></div><div class="chart-sm"><canvas id="c-alloc-d"></canvas></div>' + chartNote('现金 ' + V.cash + '% + 黄金 ' + V.goldP + '% + 油气 ' + V.oil + '%：防御底仓。') + '</div></div>' +
      '<div class="subcard" style="margin-bottom:14px"><h3>1 / 2 / 3 读法</h3>' + numList([
        'GOR ' + V.gorW + '，' + V.regime + '；' + (V.gorW < 42 ? '已跌破 42' : '仍在 42 上方'),
        'VIX ' + V.vix + ' vs 门槛 ' + V.vixGate + '：' + (V.s2 ? '已过门槛' : '未到投降签名'),
        '油分位 ' + V.oilPctl + '：' + (V.oilPctl !== '—' && parseFloat(V.oilPctl) <= 25 ? '底部区域' : '非底部') + '；合同 ' + V.comp
      ]) + '</div>' +
      secTitle('02','gor','机器解读','变化、建议、阶段') + '<div class="grid2"><div class="card"><div class="card-head"><span class="ic">📌</span><h2>本周重要变化</h2></div><div class="line">' + changeLine(V) + '</div><div class="line muted" style="margin-top:6px">' + weeklyReview(V) + '</div><div class="change-grid" style="margin-top:10px">' + changeCards(V) + '</div></div>' +
      '<div class="card"><div class="card-head"><span class="ic">💡</span><h2>投资建议</h2></div><ul class="advice">' + adviceItems(V) + '</ul></div></div>' +
      '<div class="card"><div class="card-head"><span class="ic">🌀</span><h2>向心坍缩阶段</h2></div>' + stageHTML(V) + '</div>' +
      secTitle('03','bank','机构对照','本周机构 vs 机器') + '<div class="subcard" style="margin-bottom:12px"><h3>1 / 2 / 3 对照</h3>' + numList([
        '机构：增长尚可、通胀黏性、资本更贵',
        '我们：GOR ' + V.gorW + '、仓位 ' + V.pos + '、筛选器 ' + V.verdict + '，没有投降签名',
        '差异：机构偏“盈利轮动”，机器等“困境打印”'
      ]) + '</div>' + '<div class="subcard" style="margin-bottom:12px"><h3>1 / 2 / 3 建议</h3>' + numList([
        '机器：GOR ' + V.gorW + '、仓位 ' + V.pos + '；没有投降签名就不动',
        '机构：基准是“盈利轮动”，不是全面衰退',
        '差异：机构偏股票内部轮动，机器只做商品/合同与困境'
      ]) + '</div>' +
      '<details class="fold"><summary>展开：本周机构 vs 机器（' + ((review && review.period) || '') + '）</summary>' + reviewHTML(review, V) + '</details>' + '<div class="grid2"><div class="card"><div class="card-head"><span class="ic">🧭</span><h2>状态解读</h2></div>' +
      '<div class="line">' + V.summary + '</div><div class="line muted" style="margin-top:8px">' + V.interpret + '</div>' +
      '<div style="margin-top:12px">' + screenTags(V) + '</div></div>' +
      '<div class="card"><div class="card-head"><span class="ic">💰</span><h2>今日配置 · 总仓位 ' + V.pos + '</h2></div>' +
      '<div class="bars">' + barsHTML + '</div><div class="legend">' + legend + '</div>' +
      '<div style="margin-top:14px"><div class="muted">合同完成度 ' + V.comp + '（距 $107.60 还差 ' + V.gap + ' · ' + V.days + '）</div>' +
      '<div class="progress"><i style="width:' + compPct + '%"></i></div></div></div></div>' +
      '<div class="grid2"><div class="card"><div class="card-head"><span class="ic">⚠️</span><h2>活跃预警</h2></div>' + alerts + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">🛡️</span><h2>硬止损 / 筛选器</h2></div>' +
      '<div class="line">硬止损 <b>' + (V.hsOn ? '已触发' : '未触发') + '</b> · 阈值 ' + V.hsThr + ' · 距离 ' + V.hsDist + '</div>' +
      '<div class="line">裁决 <b>' + V.verdict + '</b> · 通过 ' + V.npass + '/3 · 油分位 ' + V.oilPctl + ' · VIX ' + V.vix + '（门槛 ' + V.vixGate + '）</div>' +
      '<div style="margin-top:12px">' + screenTags(V) + '</div></div></div>' +
      '<div class="card"><div class="card-head"><span class="ic">📊</span><h2>WTI × GOR 双轴 · 近 60 日</h2></div><div class="chart"><canvas id="c-wti-gor"></canvas></div>' + chartNote('WTI 上行、GOR 下行：油腿主导；两条线反向，是“金转油”的盘面证据。') + '</div>' +
      secTitle('04','history','数据留底','GOR 走势、时间轴与最近 10 周') +
      '<div class="card"><div class="card-head"><span class="ic">📈</span><h2>GOR 走势 · 近 60 日</h2></div><div class="chart"><canvas id="c-gor-d"></canvas></div>' + chartNote('当前 GOR ' + V.gorW + '：油腿主导，已跌破 42；下一道观察线 40。') + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">⏰</span><h2>关键时间节点</h2></div>' + timelineHTML(V) + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">📜</span><h2>最近 10 周 GOR · 留底</h2></div><div class="line muted" style="margin-bottom:8px">' + changeLine(V) + '</div>' + historyTable(V.weekly, 10) + '</div>';
  }

  function chartBase(extra) {
    var grid = {color: 'rgba(255,255,255,.06)'}, tick = {color: '#7a8a9a', font: {size: 10}};
    var o = {responsive: true, maintainAspectRatio: false, plugins: {legend: {display: false}},
      scales: {x: {grid: grid, ticks: tick}, y: {grid: grid, ticks: tick}}};
    if (extra) for (var k in extra) o[k] = extra[k];
    return o;
  }
  function parseFlow(v) {
    if (!v) return 0;
    var s = String(v).replace(/[$,]/g, '');
    var m = s.match(/([0-9.]+)/);
    var n = m ? parseFloat(m[1]) : 0;
    return s.indexOf('-') >= 0 ? -n : n;
  }
  function makeWeeklyGorChart(V, id) {
    if (!window.Chart) return;
    var rows = (V.weekly || []).slice(-8);
    var el = byId(id); if (!el) return;
    new Chart(el, {type: 'bar', data: {labels: rows.map(function (r) { return (r.date || '').slice(5); }),
      datasets: [{data: rows.map(function (r) { return r.gor_wti; }), backgroundColor: rows.map(function (r) { return r.gor_wti >= 45 ? 'rgba(240,68,88,.65)' : 'rgba(240,192,64,.55)'; })}]}, options: chartBase()});
  }
  function makeFlowsChart(fw, id) {
    if (!window.Chart || !fw) return;
    var rows = fw.weekly_flows || [];
    var el = byId(id); if (!el) return;
    new Chart(el, {type: 'bar', data: {labels: rows.map(function (x) { return x.label; }),
      datasets: [{data: rows.map(function (x) { return parseFlow(x.value); }), backgroundColor: rows.map(function (x) { return parseFlow(x.value) >= 0 ? 'rgba(110,231,183,.55)' : 'rgba(240,68,88,.55)'; })}]},
      options: chartBase({indexAxis: 'y'})});
  }
  function makeSystematicChart(fw, id) {
    if (!window.Chart || !fw) return;
    var rows = fw.systematic || [];
    var el = byId(id); if (!el) return;
    new Chart(el, {type: 'bar', data: {labels: rows.map(function (x) { return x.scenario; }),
      datasets: [{data: rows.map(function (x) { return parseFlow(x.flow); }), backgroundColor: rows.map(function (x) { return parseFlow(x.flow) <= -50 ? 'rgba(240,68,88,.65)' : 'rgba(251,191,36,.55)'; })}]}, options: chartBase()});
  }
  function makeWtiGorChart(V, id) {
    if (!window.Chart) return;
    var rows = (V.daily || []).filter(function (r) { return r.gor_wti != null && r.wti != null; }).slice(-60);
    var el = byId(id); if (!el) return;
    new Chart(el, {type: 'line', data: {labels: rows.map(function (r) { return (r.date || '').slice(5); }),
      datasets: [
        {label: 'GOR(WTI)', data: rows.map(function (r) { return r.gor_wti; }), borderColor: '#f0c040', yAxisID: 'y', tension: .25, pointRadius: 1.2},
        {label: 'WTI', data: rows.map(function (r) { return r.wti; }), borderColor: '#f06030', yAxisID: 'y1', tension: .25, pointRadius: 1.2}
      ]}, options: chartBase({plugins: {legend: {display: true, labels: {color: '#7a8a9a', boxWidth: 10}}},
        scales: {x: {grid: {color: 'rgba(255,255,255,.06)'}, ticks: {color: '#7a8a9a', font: {size: 11}}},
          y: {position: 'left', grid: {color: 'rgba(255,255,255,.06)'}, ticks: {color: '#f0c040', font: {size: 11}}},
          y1: {position: 'right', grid: {display: false}, ticks: {color: '#f06030', font: {size: 11}}}}})});
  }
  function makeGorChart(V, id) {
    if (!window.Chart) return;
    var rows = (V.daily || []).filter(function (r) { return r.gor_wti != null; }).slice(-60);
    var el = byId(id); if (!el) return;
    new Chart(el, {type: 'line', data: {labels: rows.map(function (r) { return (r.date || '').slice(5); }),
      datasets: [{data: rows.map(function (r) { return r.gor_wti; }), borderColor: '#f06030',
        backgroundColor: 'rgba(240,96,48,.08)', fill: true, tension: .25, pointRadius: 1.5}]}, options: chartBase()});
  }

  function flowWeekHTML(fw) {
    if (!fw) return '';
    var flows = (fw.weekly_flows || []).map(function (x) {
      return '<div class="flow-mini"><div class="k">' + x.label + '</div><div class="v">' + x.value + '</div><div class="s">' + (x.note || '') + '</div></div>';
    }).join('');
    var pos = (fw.positioning || []).map(function (x) {
      return '<div class="check"><span class="l">' + x.label + '</span><span class="v">' + x.value + '</span></div><div class="muted" style="font-size:11px;margin:-4px 0 6px">' + (x.note || '') + '</div>';
    }).join('');
    var sys = (fw.systematic || []).map(function (x) {
      var cls = x.scenario.indexOf('下跌') >= 0 ? 'bad' : x.scenario.indexOf('上涨') >= 0 ? 'ok' : 'warn';
      return '<div class="sys"><span class="tag ' + cls + '">' + x.scenario + '</span><b>' + x.flow + '</b><div class="muted">' + (x.note || '') + '</div></div>';
    }).join('');
    var cta = (fw.cta || []).map(function (x) { return '<li>' + x + '</li>'; }).join('');
    var credit = (fw.credit || []).concat(fw.regional || [], fw.commodities || []).map(function (x) { return '<li>' + x + '</li>'; }).join('');
    var scen = (fw.scenarios || []).map(function (s) {
      return '<div class="scen"><b>' + s.name + '</b><div class="muted">条件：' + s.condition + '</div><div class="muted">倾向：' + s.market + '</div><div class="muted">证伪：' + s.falsify + '</div></div>';
    }).join('');
    var watch = (fw.watch || []).map(function (x) { return '<li>' + x + '</li>'; }).join('');
    return '<div class="card flow-module"><div class="card-head"><span class="ic">🌐</span><h2>本周资金流（机构）· 一周一期</h2>' + tag(fw.period || '', 'gold') + '</div>' +
      '<div class="review-thesis">' + (fw.summary || '') + '</div><div class="muted" style="margin-bottom:12px">' + (fw.source || '') + '</div>' +
      '<div class="flow-grid">' + flows + '</div>' +
      '<div class="grid2" style="margin-top:14px"><div class="subcard"><h3>仓位与拥挤</h3>' + pos + '</div><div class="subcard"><h3>系统性资金</h3>' + sys + '</div></div>' +
      '<div class="grid2"><div class="subcard"><h3>CTA / 久期</h3><ul class="advice">' + cta + '</ul></div><div class="subcard"><h3>信用 / 区域 / 商品</h3><ul class="advice">' + credit + '</ul></div></div>' +
      '<div class="grid2"><div class="subcard"><h3>三种情景</h3>' + scen + '</div><div class="subcard"><h3>观察阈值</h3><ul class="advice">' + watch + '</ul></div></div></div>';
  }

  function capitalHTML(V, cf, review, fw) {
    return '<div class="hero"><div class="hero-kicker">CAPITAL THREE FLOWS · ' + V.updated + '</div>' +
      '<div class="hero-row"><div class="hero-num" style="font-size:64px;letter-spacing:-2px">' + V.flowDir + '</div>' +
      '<div class="hero-side"><div class="hero-f">总量 <b>' + V.flowTotal + '</b> · 流速 <b>' + V.flowSpeed + '</b></div>' +
      '<div class="hero-sub">GOR(WTI) ' + V.gorW + ' · 仓位 ' + V.pos + ' · 合同 ' + V.comp + '</div></div></div>' +
      '<div class="hero-tags">' + tag('向心坍缩', 'gold') + tag('VIX ' + V.vix, 'warn') + tag('10Y ' + V.us10y, 'warn') + tag('DXY ' + V.dxy, 'ok') + '</div></div>' +
      secTitle('01','flow','资金流总览','总量、方向、流速') + legendBar() + '<div class="card"><div class="card-head"><span class="ic">🌀</span><h2>向心坍缩阶段</h2></div>' + stageHTML(V) + '</div>' +
      '<div class="metrics">' + metric('GOR(WTI)', V.gorW) + metric('GOR(Brent)', V.gorB) + metric('DXY', V.dxy) +
      metric('10Y', V.us10y) + metric('VIX', V.vix) + metric('WTI', V.wti) + '</div>' +
      '<div class="change-grid">' + changeCards(V) + '</div>' +
      '<div class="flow-row"><div class="flow"><div class="k">总量</div><div class="v">' + V.flowTotal + '</div></div>' +
      '<div class="flow"><div class="k">方向</div><div class="v">' + V.flowDir + '</div></div>' +
      '<div class="flow"><div class="k">流速</div><div class="v">' + V.flowSpeed + '</div></div></div>' +
      '<div class="grid2"><div class="card"><div class="card-head"><span class="ic">🌐</span><h2>周度资金流</h2></div><div class="chart-sm"><canvas id="c-flows"></canvas></div>' + chartNote('股票 +$64.5B、债券 +$11.8B、现金 −$53.1B：不是撤退，是再平衡。') + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">📈</span><h2>GOR 周度</h2></div><div class="chart-sm"><canvas id="c-week-cap"></canvas></div>' + chartNote('GOR 从 46.05 回落到 41.11：油腿主导，合同方向一致。') + '</div></div>' +
      '<div class="subcard" style="margin-bottom:14px"><h3>1 / 2 / 3 读法</h3>' + numList([
        '总量：股票、债券同流入，现金流出——风险偏好未全面退潮',
        '结构：科技/AI 仍吸金，但拥挤度上升、回撤弹性变大',
        '信用：IG 吸金、HY 流出——买久期，不买低等级'
      ]) + '</div>' +
      secTitle('02','bank','机构资金','一周一期') + '<div class="card"><div class="card-head"><span class="ic">⚙️</span><h2>系统性资金 · 三种路径</h2></div><div class="chart-sm"><canvas id="c-sys"></canvas></div>' + chartNote('下跌路径卖出 ~$810 亿：市场不需要全面撤资，价格走弱本身就会放大卖压。') + '</div>' +
      '<div class="subcard" style="margin-bottom:12px"><h3>1 / 2 / 3 观察</h3>' + numList([
        '标普 500 距最近卖出触发位约 1.1%',
        '10Y 4.85–4.95% 才触发 CTA 明显回补；4.65% 约回补一半',
        '现金 3.9% 低于 4.0% 阈值，科技超配为 2020-08 以来最大'
      ]) + '</div>' +
      '<details class="fold"><summary>展开：本周资金流（机构）· 股票 / 债券 / 现金</summary>' + flowWeekHTML(fw) + '</details>' + secTitle('03','gor','机器与市场','GOR、仓位、合同') + '<details class="fold"><summary>展开：本周机构 vs 机器（' + ((review && review.period) || '') + '）</summary>' + reviewHTML(review, V) + '</details>' + '<div class="grid2"><div class="card"><div class="card-head"><span class="ic">🥇</span><h2>金 · 底仓</h2></div><div class="line">黄金 ' + V.gold + ' · 配置 ' + V.goldP + '% · GOR(WTI) ' + V.gorW + '</div><div class="line muted" style="margin-top:6px">金价距 8 月峰值回撤约 11.9%；央行购金仍是中期支撑。</div></div>' +
      '<div class="card"><div class="card-head"><span class="ic">🛢️</span><h2>油 · 合同</h2></div><div class="line">WTI ' + V.wti + ' · 配置 ' + V.oil + '% · 合同 ' + V.comp + '</div><div class="line muted" style="margin-top:6px">距 $107.60 还差 ' + V.gap + ' · ' + V.days + '；硬止损 ' + (V.hsOn ? '已触发' : '未触发') + '（阈值 ' + V.hsThr + '）。</div></div></div>' +
      '<div class="card"><div class="card-head"><span class="ic">🧭</span><h2>状态解读</h2></div><div class="line">' + V.summary + '</div><div class="line muted" style="margin-top:8px">' + V.interpret + '</div></div>' +
      '<div class="card"><div class="card-head"><span class="ic">📈</span><h2>GOR(WTI) · 近 60 个交易日</h2></div><div class="chart"><canvas id="c-gor"></canvas></div>' + chartNote('GOR 回落 = 油相对金走强；与合同方向一致，但机器仍等投降签名。') + '</div>' +
      '<div class="grid2"><div class="card"><div class="card-head"><span class="ic">🏦</span><h2>美联储资产负债表（万亿美元）</h2></div><div class="chart"><canvas id="c-fed"></canvas></div>' + chartNote('资产负债表 ' + (((cf && cf.macro_fred && cf.macro_fred.fed_balance_trillion) || 6.76)) + ' 万亿、同比基本持平：QT 已停，但未重新大幅扩表。') + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">💸</span><h2>联邦净利息（千亿美元 / 年化）</h2></div><div class="chart"><canvas id="c-int"></canvas></div>' + chartNote('净利息 ' + (((cf && cf.macro_fred && cf.macro_fred.net_interest_trillion) || 1.28)) + ' 万亿（年化）：利息账单是当前最大的资本容器。') + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">💵</span><h2>DXY · 美元指数</h2></div><div class="chart"><canvas id="c-dxy"></canvas></div>' + chartNote('DXY ' + V.dxy + '，仍在 >99 的向心坍缩区间；没有出现美元挤兑式升值。') + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">🌐</span><h2>FX · USD/CNH · USD/JPY · EUR/USD</h2></div><div class="chart"><canvas id="c-fx"></canvas></div>' + chartNote('USD/JPY ' + (((cf && cf.fx_rates && cf.fx_rates.usdjpy) || 158.34)) + '（日元弱）、USD/CNH ' + (((cf && cf.fx_rates && cf.fx_rates.usdcnh) || 6.692)) + '（人民币偏强）、EUR/USD ' + (((cf && cf.fx_rates && cf.fx_rates.usdeur) || 1.119)) + '。') + '</div></div>' +
      secTitle('04','history','数据留底','图表与最近 10 周') + '<div class="card"><div class="card-head"><span class="ic">⏰</span><h2>关键时间节点</h2></div>' + timelineHTML(V) + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">📜</span><h2>最近 10 周 GOR · 留底</h2></div><div class="line muted" style="margin-bottom:8px">' + changeLine(V) + '</div>' + historyTable(V.weekly, 10) + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">📎</span><h2>口径说明</h2></div><div class="line muted">数值来自公开卡片 / FRED / EIA 缓存；GOR(Brent) 为 WTI×1.06 合成，真实 Brent 价差更宽。图表历史点为公开序列，最后一点为当前值。</div></div>';
  }

  function makeCapitalCharts(V, cf, fw) {
    if (!window.Chart) return;
    var daily = V.daily || [];
    var gorRows = daily.filter(function (r) { return r.gor_wti != null; }).slice(-60);
    new Chart(byId('c-gor'), {type: 'line', data: {labels: gorRows.map(function (r) { return (r.date || '').slice(5); }),
      datasets: [{data: gorRows.map(function (r) { return r.gor_wti; }), borderColor: '#f06030', backgroundColor: 'rgba(240,96,48,.08)', fill: true, tension: .25, pointRadius: 1.5}]}, options: chartBase()});
    var fedHist = [8.9, 8.8, 8.6, 8.4, 8.3, 8.1, 7.9, 7.7, 7.5, 7.3, 7.2, 7.1, 7.0, 6.9, 6.8, 6.7];
    var fedNow = (cf && cf.macro_fred && cf.macro_fred.fed_balance_trillion) || 6.76;
    fedHist[fedHist.length - 1] = fedNow;
    new Chart(byId('c-fed'), {type: 'line', data: {labels: ['2022Q1','Q2','Q3','Q4','2023Q1','Q2','Q3','Q4','2024Q1','Q2','Q3','Q4','2025Q1','Q2','Q3','Now'],
      datasets: [{data: fedHist, borderColor: '#4d9bff', backgroundColor: 'rgba(77,155,255,.08)', fill: true, tension: .3, pointRadius: 1.5}]}, options: chartBase()});
    var intHist = [3.5, 4.2, 4.8, 6.5, 8.8, 11.0];
    intHist.push(((cf && cf.macro_fred && cf.macro_fred.net_interest_trillion) || 1.28) * 10);
    new Chart(byId('c-int'), {type: 'bar', data: {labels: ['2020','2021','2022','2023','2024','2025','Now'],
      datasets: [{data: intHist, backgroundColor: 'rgba(240,68,88,.6)'}]}, options: chartBase()});
    new Chart(byId('c-dxy'), {type: 'line', data: {labels: ['2023H1','H2','2024Q1','Q2','Q3','Q4','2025Q1','Q2','2026Q1','Now'],
      datasets: [{data: [103,105,104,106,101,107,99,97,100, parseFloat(V.dxy)], borderColor: '#4d9bff', backgroundColor: 'rgba(77,155,255,.08)', fill: true, tension: .3, pointRadius: 1.5}]}, options: chartBase()});
    var fx = (cf && cf.fx_rates) || {};
    new Chart(byId('c-fx'), {type: 'line', data: {labels: ['2023H1','H2','2024Q1','Q2','Q3','Q4','2025Q1','Q2','2026Q1','Now'],
      datasets: [
        {label: 'USD/CNH', data: [6.90,7.25,7.20,7.28,7.10,7.32,7.25,7.15,7.10, fx.usdcnh || 6.692], borderColor: '#4d9bff', tension: .3, pointRadius: 1.5},
        {label: 'USD/JPY', data: [140,148,150,159,143,157,149,144,150, fx.usdjpy || 158.34], borderColor: '#f06030', tension: .3, pointRadius: 1.5},
        {label: 'EUR/USD', data: [1.08,1.05,1.08,1.07,1.11,1.04,1.07,1.09,1.10, fx.usdeur || 1.119], borderColor: '#6ee7b7', tension: .3, pointRadius: 1.5}
      ]}, options: chartBase({plugins: {legend: {display: true, labels: {color: '#7a8a9a', boxWidth: 10}}}})});
    makeFlowsChart(fw, 'c-flows');
    makeSystematicChart(fw, 'c-sys');
    makeWeeklyGorChart(V, 'c-week-cap');
  }

  function hedgeHTML(V) {
    var actions = V.actions.map(function (x, i) { return '<li><span class="n">' + (i + 1) + '</span><div>' + x + '</div></li>'; }).join('');
    var tools = V.tools.map(function (t) {
      return '<div class="tool"><h3>' + t.name + ' ' + tag(t.status, t.cls) + '</h3><div class="t">' + t.text + '</div></div>';
    }).join('');
    var checks = V.checks.map(function (c) {
      return '<div class="check"><span class="l">' + c[0] + '</span><span class="v">' + c[1] + '</span>' + tag(c[2] === 'bad' ? '注意' : c[2] === 'warn' ? '观察' : '正常', c[2]) + '</div>';
    }).join('');
    return '<div class="hero"><div class="hero-kicker">HEDGE PLAYBOOK · ' + V.updated + '</div>' +
      '<div class="hero-row"><div class="hero-num">' + V.pos + '</div><div class="hero-side">' +
      '<div class="hero-f">总仓位 <b>' + V.pos + '</b> · 硬止损 <b>' + (V.hsOn ? '已触发' : '未触发') + '</b></div>' +
      '<div class="hero-sub">油气 ' + V.oil + '% · 黄金 ' + V.goldP + '% · 现金 ' + V.cash + '% · A股 ' + V.astock + '%</div></div></div>' +
      '<div class="hero-tags">' + tag(V.regime, 'gold') + tag('WTI ' + V.wti, 'ok') + tag('VIX ' + V.vix, 'warn') + tag('阈值 ' + V.hsThr, 'ok') + '</div></div>' +
      secTitle('01','shield','当前动作','按机器状态生成') + legendBar() + '<div class="card"><div class="card-head"><span class="ic">🌀</span><h2>向心坍缩阶段</h2></div>' + stageHTML(V) + '</div>' +
      '<div class="metrics">' + metric('GOR(WTI)', V.gorW) + metric('WTI', V.wti) + metric('VIX', V.vix) + metric('10Y', V.us10y) + metric('仓位', V.pos) + '</div>' +
      '<div class="change-grid">' + changeCards(V) + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">🎯</span><h2>当前行动</h2></div><ul class="actions">' + actions + '</ul></div>' +
      secTitle('02','target','工具与自检','四类工具 + 六项自检') + '<div class="grid2">' + tools + '</div>' +
      '<div class="grid2"><div class="card"><div class="card-head"><span class="ic">✅</span><h2>执行自检</h2></div>' + checks + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">🥧</span><h2>仓位结构</h2></div><div class="chart-sm"><canvas id="c-alloc"></canvas></div>' + chartNote('现金 ' + V.cash + '% + 黄金 ' + V.goldP + '% + 油气 ' + V.oil + '%：防御底仓，等 VIX ≥ ' + V.vixGate + ' 且油 ≤ P25 的扳机。') + '</div></div>' +
      '<div class="card"><div class="card-head"><span class="ic">📈</span><h2>GOR 周度</h2></div><div class="chart-sm"><canvas id="c-week-h"></canvas></div>' + chartNote('GOR 从 46.05 回落到 41.11：油腿主导；仓位 30% 未变。') + '</div>' +
      '<div class="subcard" style="margin-bottom:12px"><h3>1 / 2 / 3 自检</h3>' + numList([
        '硬止损：' + (V.hsOn ? '已触发' : '未触发') + '（阈值 ' + V.hsThr + '）',
        'VIX ' + V.vix + ' vs 门槛 ' + V.vixGate + '：' + (V.s2 ? '已过门槛' : '未到投降'),
        '油分位 ' + V.oilPctl + '：' + (V.oilPctl !== '—' && parseFloat(V.oilPctl) <= 25 ? '底部区域' : '非底部')
      ]) + '</div>' +
      secTitle('03','history','数据留底','时间轴与最近 10 周') + '<div class="card"><div class="card-head"><span class="ic">⏰</span><h2>关键时间节点</h2></div>' + timelineHTML(V) + '</div>' +
      '<div class="card"><div class="card-head"><span class="ic">📜</span><h2>最近 10 周 GOR · 留底</h2></div><div class="line muted" style="margin-bottom:8px">' + changeLine(V) + '</div>' + historyTable(V.weekly, 10) + '</div>';
  }

  function makeAllocChart(V, id) {
    if (!window.Chart) return;
    var el = byId(id || 'c-alloc'); if (!el) return;
    new Chart(el, {type: 'doughnut', data: {labels: ['油气', '黄金', '现金', 'A股', '铜'],
      datasets: [{data: [V.oil, V.goldP, V.cash, V.astock, V.copper], backgroundColor: ['#f06030', '#f0c040', '#64748b', '#ef4444', '#fb923c'], borderWidth: 0}]},
      options: {responsive: true, maintainAspectRatio: false, plugins: {legend: {position: 'bottom', labels: {color: '#7a8a9a', boxWidth: 10}}}}});
  }
})();
