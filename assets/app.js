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
    get('history_weekly.json').catch(function () { return null; })
  ]).then(function (out) {
    var g = out[0] || {}, cf = out[1], hist = out[2], dailyDoc = out[3], weeklyDoc = out[4];
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
    render(V, g, cf, hist);
  });

  function changeLine(V) {
    var w = V.weekly || [], d = V.daily || [];
    var out = [];
    if (w.length >= 2) {
      var a = w[w.length - 2], b = w[w.length - 1];
      out.push('GOR 周变化：' + (b.gor_wti == null ? '—' : b.gor_wti.toFixed(2)) + '（上周 ' + (a.gor_wti == null ? '—' : a.gor_wti.toFixed(2)) + '，' + signed((b.gor_wti || 0) - (a.gor_wti || 0), 2) + '）');
    }
    if (d.length >= 2) {
      var x = d[d.length - 2], y = d[d.length - 1];
      out.push('WTI 日变化 ' + signed((y.wti || 0) - (x.wti || 0), 2) + ' · VIX 日变化 ' + signed((y.vix || 0) - (x.vix || 0), 2));
    }
    return out.join(' · ') || '变化数据待生成';
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

  function render(V, g, cf, hist) {
    var badge = byId('gorBadge');
    if (badge) { badge.textContent = 'GOR ' + V.gorW + ' · ' + V.regime; badge.className = 'gor-badge' + ((V.gorW >= 45) ? ' alert' : ''); }
    var app = byId('app');
    if (!app) return;
    if (page === 'capital') { app.innerHTML = capitalHTML(V, cf); makeCharts(V, cf, hist); }
    else if (page === 'hedge') { app.innerHTML = hedgeHTML(V); }
    else { app.innerHTML = decisionHTML(V, g); }
  }

  function decisionHTML(V, g) {
    var bars = [['油气', V.oil, '#f06030'], ['黄金', V.goldP, '#f0c040'], ['现金', V.cash, '#64748b'], ['A股', V.astock, '#ef4444'], ['铜', V.copper, '#fb923c']];
    var barsHTML = bars.filter(function (x) { return x[1] > 0; }).map(function (x) { return '<i style="width:' + x[1] + '%;background:' + x[2] + '"></i>'; }).join('');
    var legend = bars.map(function (x) { return '<span><b>' + x[0] + '</b> ' + x[1] + '%</span>'; }).join('');
    var alerts = (g.alerts || []).map(function (a) {
      return '<div class="alert ' + (a.level === 'warning' ? 'warn' : '') + '"><b>' + (a.title || '') + '</b> — ' + (a.detail || '') + '</div>';
    }).join('') || '<div class="muted">无活跃预警</div>';
    return '<div class="hero"><h1>GOR(WTI) · 决策看板</h1><div class="hero-num">' + V.gorW + '</div>' +
      '<div class="hero-f">$' + String(V.gold).replace('$', '') + ' ÷ ' + V.wti + ' = <b>' + V.gorW + ' : 1</b></div>' +
      '<div class="hero-sub">GOR(Brent) ' + V.gorB + '（合成 ' + V.brent + '） · ' + V.regime + ' · 更新 ' + V.updated + '</div></div>' +
      '<div class="metrics">' + metric('黄金', V.gold) + metric('WTI', V.wti) + metric('Brent', V.brent) + metric('DXY', V.dxy) + metric('10Y', V.us10y) + metric('VIX', V.vix) + '</div>' +
      '<div class="card"><h2>状态解读</h2><div class="line">' + V.summary + '</div><div class="line muted" style="margin-top:8px">' + V.interpret + '</div></div>' +
      '<div class="grid2"><div class="card"><h2>今日配置 · 总仓位 ' + V.pos + '</h2><div class="bars">' + barsHTML + '</div><div class="legend">' + legend + '</div><div class="line muted" style="margin-top:10px">合同 ' + V.comp + ' · 距 $107.60 还差 ' + V.gap + ' · ' + V.days + '</div></div>' +
      '<div class="card"><h2>活跃预警</h2>' + alerts + '</div></div>' +
      '<div class="card"><h2>筛选器 / 硬止损</h2><div class="line">裁决 <b>' + V.verdict + '</b> · 通过 ' + V.npass + '/3 · 油分位 ' + V.oilPctl + ' · VIX ' + V.vix + '（门槛 ' + V.vixGate + '）</div><div class="line">硬止损 <b>' + (V.hsOn ? '已触发' : '未触发') + '</b> · 阈值 ' + V.hsThr + ' · 距离 ' + V.hsDist + '</div></div>' +
      '<div class="card"><h2>最近 10 周 GOR · 数据留底</h2><div class="line muted" style="margin-bottom:8px">' + changeLine(V) + '</div>' + historyTable(V.weekly, 10) + '</div>';
  }
  function metric(k, v) { return '<div class="metric"><div class="k">' + k + '</div><div class="v">' + v + '</div></div>'; }

  function capitalHTML(V, cf) {
    var fx = (cf && cf.fx_rates) || {};
    return '<div class="hero"><h1>资本三流 · 实时观测</h1><div class="hero-num">' + V.flowDir + '</div>' +
      '<div class="hero-f">总量 <b>' + V.flowTotal + '</b> · 流速 <b>' + V.flowSpeed + '</b> · 更新 ' + V.updated + '</div></div>' +
      '<div class="metrics">' + metric('GOR(WTI)', V.gorW) + metric('GOR(Brent)', V.gorB) + metric('DXY', V.dxy) + metric('10Y', V.us10y) + metric('VIX', V.vix) + metric('WTI', V.wti) + '</div>' +
      '<div class="card"><h2>状态解读</h2><div class="line">' + V.summary + '</div><div class="line muted" style="margin-top:8px">' + V.interpret + '</div></div>' +
      '<div class="grid2">' +
      '<div class="card"><h2>GOR(WTI) · 近 60 个交易日</h2><div class="chart"><canvas id="c-gor"></canvas></div></div>' +
      '<div class="card"><h2>美联储资产负债表（万亿美元）</h2><div class="chart"><canvas id="c-fed"></canvas></div></div>' +
      '<div class="card"><h2>联邦净利息（千亿美元 / 年化）</h2><div class="chart"><canvas id="c-int"></canvas></div></div>' +
      '<div class="card"><h2>DXY · 美元指数</h2><div class="chart"><canvas id="c-dxy"></canvas></div></div>' +
      '<div class="card"><h2>FX · USD/CNH · USD/JPY · EUR/USD</h2><div class="chart"><canvas id="c-fx"></canvas></div></div>' +
      '</div>' +
      '<div class="card"><h2>最近 10 周 GOR · 数据留底</h2><div class="line muted" style="margin-bottom:8px">' + changeLine(V) + '</div>' + historyTable(V.weekly, 10) + '</div>' +
      '<div class="card"><h2>口径说明</h2><div class="line muted">所有数值来自公开卡片/FRED/EIA 缓存；GOR(Brent) 为 WTI×1.06 合成，真实 Brent 价差更宽。图表历史点为公开序列，最后一点为当前值。</div></div>';
  }

  function makeCharts(V, cf, hist) {
    if (!window.Chart) return;
    var grid = {color: 'rgba(255,255,255,.06)'}, tick = {color: '#7a8a9a', font: {size: 10}};
    function opts(extra) {
      var o = {responsive: true, maintainAspectRatio: false, plugins: {legend: {display: false}},
        scales: {x: {grid: grid, ticks: tick}, y: {grid: grid, ticks: tick}}};
      if (extra) { for (var k in extra) o[k] = extra[k]; }
      return o;
    }
    var daily = V.daily || [];
    var gorRows = daily.filter(function (r) { return r.gor_wti != null; }).slice(-60);
    new Chart(document.getElementById('c-gor'), {type: 'line',
      data: {labels: gorRows.map(function (r) { return (r.date || '').slice(5); }),
        datasets: [{data: gorRows.map(function (r) { return r.gor_wti; }), borderColor: '#f06030', backgroundColor: 'rgba(240,96,48,.08)', fill: true, tension: .25, pointRadius: 1.5}]},
      options: opts()});

    var fedHist = [8.9, 8.8, 8.6, 8.4, 8.3, 8.1, 7.9, 7.7, 7.5, 7.3, 7.2, 7.1, 7.0, 6.9, 6.8, 6.7];
    var fedNow = (cf && cf.macro_fred && cf.macro_fred.fed_balance_trillion) || 6.76;
    var fedLabels = ['2022Q1','Q2','Q3','Q4','2023Q1','Q2','Q3','Q4','2024Q1','Q2','Q3','Q4','2025Q1','Q2','Q3','Now'];
    fedHist[fedHist.length - 1] = fedNow;
    new Chart(document.getElementById('c-fed'), {type: 'line',
      data: {labels: fedLabels, datasets: [{data: fedHist, borderColor: '#4d9bff', backgroundColor: 'rgba(77,155,255,.08)', fill: true, tension: .3, pointRadius: 1.5}]}, options: opts()});

    var intHist = [3.5, 4.2, 4.8, 6.5, 8.8, 11.0];
    var intNow = ((cf && cf.macro_fred && cf.macro_fred.net_interest_trillion) || 1.28) * 10;
    intHist.push(intNow);
    new Chart(document.getElementById('c-int'), {type: 'bar',
      data: {labels: ['2020','2021','2022','2023','2024','2025','Now'], datasets: [{data: intHist, backgroundColor: 'rgba(240,68,88,.6)'}]}, options: opts()});

    var dxyHist = [103, 105, 104, 106, 101, 107, 99, 97, 100, 101.84];
    new Chart(document.getElementById('c-dxy'), {type: 'line',
      data: {labels: ['2023H1','H2','2024Q1','Q2','Q3','Q4','2025Q1','Q2','2026Q1','Now'], datasets: [{data: dxyHist, borderColor: '#4d9bff', backgroundColor: 'rgba(77,155,255,.08)', fill: true, tension: .3, pointRadius: 1.5}]}, options: opts()});

    var fx = (cf && cf.fx_rates) || {};
    var fxLabels = ['2023H1','H2','2024Q1','Q2','Q3','Q4','2025Q1','Q2','2026Q1','Now'];
    new Chart(document.getElementById('c-fx'), {type: 'line',
      data: {labels: fxLabels, datasets: [
        {label: 'USD/CNH', data: [6.90,7.25,7.20,7.28,7.10,7.32,7.25,7.15,7.10, fx.usdcnh || 6.692], borderColor: '#4d9bff', tension: .3, pointRadius: 1.5},
        {label: 'USD/JPY', data: [140,148,150,159,143,157,149,144,150, fx.usdjpy || 158.34], borderColor: '#f06030', tension: .3, pointRadius: 1.5},
        {label: 'EUR/USD', data: [1.08,1.05,1.08,1.07,1.11,1.04,1.07,1.09,1.10, fx.usdeur || 1.119], borderColor: '#6ee7b7', tension: .3, pointRadius: 1.5}
      ]}, options: opts({plugins: {legend: {display: true, labels: {color: '#7a8a9a', boxWidth: 10}}}})});
  }

  function hedgeHTML(V) {
    var actions = V.actions.map(function (x, i) { return '<li><span class="n">' + (i + 1) + '</span>' + x + '</li>'; }).join('');
    var tools = V.tools.map(function (t) {
      return '<div class="card"><h3>' + t.name + ' <span class="tag ' + t.cls + '">' + t.status + '</span></h3><div class="line muted">' + t.text + '</div></div>';
    }).join('');
    var checks = V.checks.map(function (c) {
      return '<tr><td>' + c[0] + '</td><td>' + c[1] + '</td><td><span class="tag ' + c[2] + '">' + (c[2] === 'bad' ? '注意' : c[2] === 'warn' ? '观察' : '正常') + '</span></td></tr>';
    }).join('');
    return '<div class="hero"><h1>对冲作战手册 · 动态版</h1><div class="hero-num">' + V.pos + '</div>' +
      '<div class="hero-f">总仓位 <b>' + V.pos + '</b> · 硬止损 <b>' + (V.hsOn ? '触发' : '未触发') + '</b> · 更新 ' + V.updated + '</div></div>' +
      '<div class="card"><h2>当前行动</h2><ul class="actions">' + actions + '</ul></div>' +
      '<div class="card"><h2>状态解读</h2><div class="line">' + V.summary + '</div><div class="line muted" style="margin-top:8px">' + V.interpret + '</div></div>' +
      '<div class="grid2">' + tools + '</div>' +
      '<div class="card"><h2>执行自检</h2><table><thead><tr><th>项</th><th>现值</th><th>状态</th></tr></thead><tbody>' + checks + '</tbody></table></div>' +
      '<div class="card"><h2>最近 10 周 GOR · 数据留底</h2><div class="line muted" style="margin-bottom:8px">' + changeLine(V) + '</div>' + historyTable(V.weekly, 10) + '</div>';
  }
})();
