/* Deep-Risk-OPP — shared live data + interpretation renderer (2026-10) */
(function () {
  function $(id) { return document.getElementById(id); }
  function num(x) { return (typeof x === 'number' && isFinite(x)) ? x : null; }
  function usd(x, d) { return x == null ? '—' : '$' + Number(x).toLocaleString('en-US', {minimumFractionDigits: d == null ? 2 : d, maximumFractionDigits: d == null ? 2 : d}); }
  function pct(x, d) { return x == null ? '—' : (x * 100).toFixed(d == null ? 1 : d) + '%'; }
  function get(url) { return fetch(url + '?v=' + Date.now(), {cache: 'no-store'}).then(function (r) { return r.json(); }); }

  function hardStop(hist, wti) {
    if (!hist || !hist.length || wti == null) return {thr: null, on: false, dist: null};
    var vals = hist.map(function (r) { return num(r.wti); }).filter(function (v) { return v != null; });
    if (vals.length < 60) return {thr: null, on: false, dist: null};
    var win = vals.slice(-60), sma = win.reduce(function (a, b) { return a + b; }, 0) / 60;
    var thr = sma * 0.85;
    var on = (wti < thr) || (wti < 60);
    return {thr: thr, on: on, dist: wti - thr};
  }

  function regimeNote(g, gorW, gorB) {
    if (gorW == null) return 'GOR 数据缺失';
    if (gorW >= 45) return '极端区：金相对油贵，避险/需求恐惧占上风';
    if (gorW >= 30) return '修复区：油腿主导、金腿滞后，方向未决';
    if (gorW >= 20) return '均衡区：油相对金偏贵';
    return '原油泡沫区：油极度昂贵';
  }

  Promise.all([
    get('gor_latest.json'),
    get('capital_flows_latest.json').catch(function () { return null; }),
    get('wti_history.json').catch(function () { return null; })
  ]).then(function (out) {
    var g = out[0] || {}, cf = out[1], hist = out[2];
    var d = g.data || {}, s = g.screener || {}, a = g.allocation || {}, c = g.capital_three_flows || {};
    var gold = num((d['黄金期货'] || {}).price), wti = num((d['WTI原油'] || {}).price);
    var brent = num((d['布伦特原油'] || {}).price), dxy = num((d['美元指数DXY'] || {}).price);
    var us10y = num((d['10Y美债收益率'] || {}).price), vix = num((d['VIX恐慌指数'] || {}).price);
    var gorW = num(g.gor_wti), gorB = num(g.gor_brent), pos = num(g.final_position);
    var comp = (wti != null) ? ((wti / 69.87 - 1) / (107.60 / 69.87 - 1)) : null;
    var gap = (wti != null) ? (107.60 - wti) : null;
    var days = Math.ceil((Date.UTC(2027, 5, 30) - Date.now()) / 86400000);
    var hs = hardStop(hist, wti);
    var flow = c.total || c.direction || c.speed ? c : (cf || {});
    var vals = {
      gold: usd(gold, 0), wti: usd(wti), brent: usd(brent), dxy: dxy == null ? '—' : dxy.toFixed(2),
      us10y: us10y == null ? '—' : us10y.toFixed(2) + '%', vix: vix == null ? '—' : vix.toFixed(2),
      gor_wti: gorW == null ? '—' : gorW.toFixed(2), gor_brent: gorB == null ? '—' : gorB.toFixed(2),
      regime: g.regime || '—', position: pos == null ? '—' : pos + '%',
      verdict: s.verdict || '—', contract_pct: comp == null ? '—' : (comp * 100).toFixed(1) + '%',
      contract_gap: gap == null ? '—' : usd(gap), days: days + ' 天',
      oil_pct: a['油气'] == null ? '—' : a['油气'] + '%', gold_pct: a['黄金'] == null ? '—' : a['黄金'] + '%',
      cash_pct: a['现金'] == null ? '—' : a['现金'] + '%', astock_pct: a['A股'] == null ? '—' : a['A股'] + '%',
      oil_pctl: s.oil_pctl == null ? '—' : (s.oil_pctl * 100).toFixed(0) + '%',
      vix_gate: s.vix_thr == null ? '—' : Number(s.vix_thr).toFixed(2),
      hard_stop: hs.on ? '已触发' : '未触发', hard_stop_thr: hs.thr == null ? '—' : usd(hs.thr),
      flow_total: flow.total || '—', flow_direction: flow.direction || '—', flow_speed: flow.speed || '—',
      updated: g.updated || '—'
    };
    var summary = 'GOR(WTI) ' + vals.gor_wti + ' · GOR(Brent) ' + vals.gor_brent + '（合成） · ' + vals.regime +
      ' · 仓位 ' + vals.position + ' · 筛选器 ' + vals.verdict + ' · 合同 ' + vals.contract_pct + '（距目标 ' + vals.contract_gap + '）';
    var interpret = regimeNote(g, gorW, gorB) + '。油分位 ' + vals.oil_pctl + '；10Y ' + vals.us10y +
      '，DXY ' + vals.dxy + '，VIX ' + vals.vix + '（门槛 ' + vals.vix_gate + '）。硬止损 ' + vals.hard_stop +
      (hs.thr != null ? '（阈值 ' + vals.hard_stop_thr + '，距离 ' + usd(hs.dist) + '）' : '') + '。';
    var hedge = '硬止损' + vals.hard_stop + ' · 油气 ' + vals.oil_pct + ' · 现金 ' + vals.cash_pct +
      ' · 总仓位 ' + vals.position + '。' + (hs.on ? '按纪律：油气降至 5%。' : '未触发，维持当前配置；VIX ≥ ' + vals.vix_gate + ' 且油 ≤ 十年 P25 才是投降签名。');
    var flowText = '总量 ' + vals.flow_total + ' · 方向 ' + vals.flow_direction + ' · 流速 ' + vals.flow_speed;
    var texts = {summary: summary, interpret: interpret, hedge: hedge, flow: flowText,
      hedge_header: 'WTI ' + vals.wti + ' · 硬止损' + vals.hard_stop + ' · 仓位 ' + vals.position};

    document.querySelectorAll('[data-live]').forEach(function (el) {
      var k = el.getAttribute('data-live'); if (k in vals) el.textContent = vals[k];
    });
    document.querySelectorAll('[data-live-text]').forEach(function (el) {
      var k = el.getAttribute('data-live-text'); if (k in texts) el.textContent = texts[k];
    });
    ['drLiveUpdated', 'drLiveSummary', 'drLiveInterpret', 'drLiveHedge', 'drLiveFlow'].forEach(function (id) {
      var el = $(id); if (!el) return;
      if (id === 'drLiveUpdated') el.textContent = '数据更新于 ' + vals.updated + ' · 动态渲染';
      if (id === 'drLiveSummary') el.textContent = summary;
      if (id === 'drLiveInterpret') el.textContent = interpret;
      if (id === 'drLiveHedge') el.textContent = hedge;
      if (id === 'drLiveFlow') el.textContent = flowText;
    });
    window.DR = {card: g, flows: cf, history: hist, values: vals};
  }).catch(function (e) {
    var el = $('drLiveUpdated'); if (el) el.textContent = '动态数据加载失败：' + e.message;
  });
})();
