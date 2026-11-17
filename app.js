/*! BLOCKTIDE TV — © 2026 Igor Serrano. Todos os direitos reservados. Ver LICENSE. */
/*
 * BLOCKTIDE TV — web app para crianças: só vídeos em português europeu, de um catálogo verificado,
 * reproduzidos no leitor oficial do YouTube (incorporado). Painel dos pais com PIN, limites de tempo,
 * hora de dormir, canais e resumo. Tudo fica neste aparelho (localStorage).
 */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const view = $('#view');
  const TEMAS = { tudo: 'Tudo', desenhos: 'Desenhos e programas', musica: 'Música', aprender: 'Aprender', historias: 'Histórias' };
  const NEXT_SECONDS = 6;

  // ---------------------------------------------------------------------------
  // Dados guardados neste aparelho
  // ---------------------------------------------------------------------------
  const load = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch (_) { return d; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) { /* sem armazenamento: continua */ } };
  const DEF = { disabled: [], enabled: [], dailyMin: 0, bedtime: { on: false, from: '21:00', to: '07:30' }, added: [], pin: null };
  let settings = { ...DEF, ...load('btv.settings', {}) };
  if (!Array.isArray(settings.enabled)) settings.enabled = [];
  const saveSettings = () => save('btv.settings', settings);
  let watch = load('btv.watch', { days: {}, channels: {}, recent: [] });
  const saveWatch = () => save('btv.watch', watch);
  const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  const secsToday = () => (watch.days[today()] || {}).sec || 0;

  let catalog = { channels: {}, videos: [] };
  // Canais verificados: ligados até os pais os desligarem. Canais «por confirmar»: desligados até os pais os ligarem.
  const pending = (k) => (catalog.channels[k] || {}).status === 'pendente';
  const channelsOn = () => Object.keys(catalog.channels).filter((k) => (pending(k) ? settings.enabled.includes(k) : !settings.disabled.includes(k)));
  function videos() {
    const on = new Set(channelsOn());
    const added = settings.added.map((a) => ({ ...a, ch: 'pais' }));
    return [...catalog.videos.filter((v) => on.has(v.ch)), ...added];
  }
  const chOf = (v) => (v.ch === 'pais' ? { name: 'Escolhido pelos pais', cor: '#9a5424', tema: 'tudo' } : catalog.channels[v.ch] || { name: '', cor: '#888' });
  const thumb = (id) => `https://i.ytimg.com/vi/${encodeURIComponent(id)}/mqdefault.jpg`;

  // ---------------------------------------------------------------------------
  // Semelhança entre vídeos (para «a seguir»): mesmo canal, mesmo tema, palavras do título
  // ---------------------------------------------------------------------------
  const STOP = new Set('para com uma uns por pelo pela que como mais sobre dos das nos nas aos the and ser mais parte'.split(' '));
  const words = (t) => new Set(String(t).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 2 && !STOP.has(w)));
  function upNext(cur, n = 8) {
    const w = words(cur.title), ch = chOf(cur);
    const recent = new Set(watch.recent.slice(0, 12));
    return videos().filter((v) => v.id !== cur.id).map((v) => {
      const vw = words(v.title); let inter = 0; for (const x of vw) if (w.has(x)) inter++;
      const s = (v.ch === cur.ch ? 1 : 0) + (chOf(v).tema === ch.tema ? 0.6 : 0) + inter * 0.5 - (recent.has(v.id) ? 1.2 : 0) + Math.random() * 0.3;
      return { v, s };
    }).sort((a, b) => b.s - a.s).slice(0, n).map((x) => x.v);
  }

  // ---------------------------------------------------------------------------
  // Limites (tempo diário e hora de dormir)
  // ---------------------------------------------------------------------------
  const mins = (hhmm) => { const [h, m] = String(hhmm).split(':').map(Number); return h * 60 + m; };
  function stopReason() {
    if (settings.dailyMin > 0 && secsToday() >= settings.dailyMin * 60) return 'time';
    const b = settings.bedtime;
    if (b && b.on) {
      const d = new Date(); const now = d.getHours() * 60 + d.getMinutes(); const f = mins(b.from), t = mins(b.to);
      if (f > t ? (now >= f || now < t) : (now >= f && now < t)) return 'bed';
    }
    return null;
  }
  function stopScreen(reason) {
    return `<div class="stop panel"><div class="moon">${reason === 'bed' ? '🌙' : '⏰'}</div>
      <h1>${reason === 'bed' ? 'Está na hora de descansar' : 'Acabou o tempo de vídeos de hoje'}</h1>
      <p class="muted" style="font-weight:800">${reason === 'bed' ? 'Os vídeos voltam amanhã de manhã.' : 'Amanhã há mais! Podes pedir a um adulto mais tempo.'}</p>
      <a class="btn primary" href="#pais">Sou adulto</a></div>`;
  }

  // ---------------------------------------------------------------------------
  // Vistas
  // ---------------------------------------------------------------------------
  function card(v) {
    const ch = chOf(v);
    return `<a class="card" href="#ver-${esc(v.id)}"><div class="thumb"><img loading="lazy" src="${thumb(v.id)}" alt="">${v.dur ? `<span class="dur">${esc(v.dur)}</span>` : ''}</div>
      <div class="t">${esc(v.title)}</div><div class="c"><i style="background:${esc(ch.cor)}"></i>${esc(ch.name)}</div></a>`;
  }
  let tema = 'tudo';
  function home() {
    const all = videos();
    const recent = watch.recent.map((id) => all.find((v) => v.id === id)).filter(Boolean).slice(0, 10);
    const chs = channelsOn().filter((k) => tema === 'tudo' || catalog.channels[k].tema === tema);
    return `<div class="chips">${Object.entries(TEMAS).map(([k, n]) => `<button class="tchip ${k === tema ? 'on' : ''}" data-tema="${k}">${n}</button>`).join('')}</div>
      ${recent.length && tema === 'tudo' ? `<section class="row"><div class="row-head"><h2>Continuar a ver</h2></div><div class="rail">${recent.map(card).join('')}</div></section>` : ''}
      ${chs.map((k) => {
        const c = catalog.channels[k]; const list = all.filter((v) => v.ch === k);
        return list.length ? `<section class="row"><div class="row-head"><h2><span class="dot" style="background:${esc(c.cor)}"></span>${esc(c.name)}</h2><a href="#canal-${k}">Ver tudo</a></div>
          <div class="rail">${list.map(card).join('')}</div></section>` : '';
      }).join('')}
      ${settings.added.length && tema === 'tudo' ? `<section class="row"><div class="row-head"><h2><span class="dot" style="background:#9a5424"></span>Escolhidos pelos pais</h2></div><div class="rail">${settings.added.map((a) => card({ ...a, ch: 'pais' })).join('')}</div></section>` : ''}
      ${!chs.length ? '<div class="empty">Não há vídeos neste tema.</div>' : ''}`;
  }
  function channelPage(k) {
    const c = catalog.channels[k];
    if (!c || !channelsOn().includes(k)) return '<div class="empty">Canal indisponível.</div>';
    return `<h1 style="display:flex;align-items:center;gap:10px"><span class="dot" style="width:18px;height:18px;border-radius:5px;background:${esc(c.cor)}"></span>${esc(c.name)}</h1>
      <p class="muted" style="font-weight:800">Canal português verificado · ${videos().filter((v) => v.ch === k).length} vídeos</p>
      <div class="grid">${videos().filter((v) => v.ch === k).map(card).join('')}</div>`;
  }
  function searchPage() {
    return `<h1>Procurar</h1><p class="muted" style="font-weight:800">Só nos vídeos em português europeu do BLOCKTIDE.</p>
      <input class="search" type="search" id="q" placeholder="O que queres ver?" autocomplete="off" />
      <div class="grid" id="results" style="margin-top:16px"></div>`;
  }
  function bindSearch() {
    const q = $('#q'), out = $('#results');
    const norm = (s) => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    const run = () => {
      const t = norm(q.value.trim());
      const list = t ? videos().filter((v) => norm(`${v.title} ${chOf(v).name}`).includes(t)) : [];
      out.innerHTML = t ? (list.length ? list.map(card).join('') : '<div class="empty">Não encontrei nada. Experimenta outra palavra!</div>') : '';
    };
    q.addEventListener('input', run); q.focus();
  }

  // ---------------------------------------------------------------------------
  // Leitor (YouTube incorporado, oficial)
  // ---------------------------------------------------------------------------
  let player = null, current = null, tick = null, countdown = null;
  let ytReady = null;
  function loadYT() {
    if (!ytReady) {
      ytReady = new Promise((resolve) => {
        if (window.YT && window.YT.Player) { resolve(); return; }
        window.onYouTubeIframeAPIReady = () => resolve();
        const s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(s);
      });
    }
    return ytReady;
  }
  function stopPlayer() {
    clearInterval(tick); tick = null; clearInterval(countdown); countdown = null;
    if (player && player.destroy) { try { player.destroy(); } catch (_) { /* ignorar */ } }
    player = null;
  }
  function watchPage(id) {
    const v = videos().find((x) => x.id === id);
    if (!v) return '<div class="empty">Este vídeo não está no BLOCKTIDE TV.</div><p style="text-align:center"><a class="btn primary" href="#inicio">Voltar ao início</a></p>';
    const ch = chOf(v);
    return `<div class="watch"><div>
        <div class="stage"><div id="player"></div><div class="cover" id="cover" hidden></div></div>
        <div class="vtitle">${esc(v.title)}</div>
        <div class="vmeta"><span class="badge-pt">✓ Português europeu</span><span>${esc(ch.name)}</span></div>
      </div>
      <aside class="upnext"><h2>A seguir</h2>${upNext(v).map(card).join('')}</aside></div>`;
  }
  async function bindWatch(id) {
    const v = videos().find((x) => x.id === id);
    if (!v) return;
    current = v;
    watch.recent = [v.id, ...watch.recent.filter((x) => x !== v.id)].slice(0, 30); saveWatch();
    await loadYT();
    if (!current || current.id !== id) return;
    player = new window.YT.Player('player', {
      host: 'https://www.youtube-nocookie.com',
      videoId: id,
      playerVars: { autoplay: 1, playsinline: 1, rel: 0, modestbranding: 1, iv_load_policy: 3, cc_lang_pref: 'pt', hl: 'pt-PT', fs: 1 },
      events: {
        onStateChange: (e) => {
          if (e.data === 1) startTick();
          else { clearInterval(tick); tick = null; }
          if (e.data === 0) endScreen();
        },
        onError: () => { toast('Este vídeo não pode ser visto aqui. Vamos ao seguinte!'); endScreen(true); },
      },
    });
  }
  function startTick() {
    if (tick) return;
    tick = setInterval(() => {
      if (!current) return;
      const d = today(); const day = watch.days[d] || (watch.days[d] = { sec: 0, videos: [] });
      day.sec += 5; if (!day.videos.includes(current.id)) day.videos.push(current.id);
      const ch = chOf(current); const c = watch.channels[current.ch] || (watch.channels[current.ch] = { name: ch.name, sec: 0 });
      c.sec += 5;
      const keys = Object.keys(watch.days).sort(); keys.slice(0, Math.max(0, keys.length - 60)).forEach((k) => delete watch.days[k]);
      saveWatch();
      const r = stopReason();
      if (r) { stopPlayer(); view.innerHTML = stopScreen(r); }
    }, 5000);
  }
  function endScreen(skip = false) {
    clearInterval(tick); tick = null;
    const cover = $('#cover'); if (!cover || !current) return;
    const next = upNext(current, 1)[0];
    if (!next) { cover.hidden = false; cover.innerHTML = '<h2>Acabou!</h2><div class="btns"><a class="btn primary" href="#inicio">Escolher outro</a></div>'; return; }
    let n = skip ? 3 : NEXT_SECONDS;
    cover.hidden = false;
    cover.innerHTML = `<h2>A seguir</h2>
      <a class="next" href="#ver-${esc(next.id)}"><img src="${thumb(next.id)}" alt=""><span><b>${esc(next.title)}</b>${esc(chOf(next).name)}</span></a>
      <div class="num" id="cd">${n}</div>
      <div class="btns"><button class="btn" id="again">Ver outra vez</button><a class="btn" href="#inicio">Escolher</a></div>`;
    $('#again').onclick = () => { clearInterval(countdown); cover.hidden = true; try { player.seekTo(0); player.playVideo(); } catch (_) { route(); } };
    countdown = setInterval(() => {
      n -= 1; const el = $('#cd'); if (el) el.textContent = n;
      if (n <= 0) { clearInterval(countdown); location.hash = `#ver-${next.id}`; }
    }, 1000);
  }

  // ---------------------------------------------------------------------------
  // Painel dos pais (PIN)
  // ---------------------------------------------------------------------------
  let unlockedUntil = 0;
  async function hash(text) {
    try {
      const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
      return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
    } catch (_) { let h = 0; for (const c of text) h = (h * 31 + c.charCodeAt(0)) >>> 0; return 'w' + h.toString(16); }
  }
  function gate() {
    const has = !!settings.pin;
    return `<div class="gate panel"><h1>Área dos pais</h1>
      <p class="muted" style="font-weight:800">${has ? 'Introduza o PIN.' : 'Crie um PIN de 4 a 8 algarismos para proteger as definições.'}</p>
      <input type="password" inputmode="numeric" maxlength="8" id="p1" placeholder="PIN" autocomplete="off" />
      ${has ? '' : '<input type="password" inputmode="numeric" maxlength="8" id="p2" placeholder="Confirmar PIN" autocomplete="off" />'}
      <div class="err" id="err"></div><button class="btn primary" id="go" style="width:100%">${has ? 'Entrar' : 'Guardar PIN'}</button></div>`;
  }
  function bindGate() {
    const go = async () => {
      const p1 = $('#p1').value.trim(); const err = $('#err');
      if (!/^\d{4,8}$/.test(p1)) { err.textContent = 'O PIN tem de ter 4 a 8 algarismos.'; return; }
      if (settings.pin) {
        if ((await hash(settings.pin.salt + p1)) !== settings.pin.hash) { err.textContent = 'PIN incorreto.'; $('#p1').value = ''; return; }
      } else {
        if (p1 !== $('#p2').value.trim()) { err.textContent = 'Os PIN não coincidem.'; return; }
        const salt = [...crypto.getRandomValues(new Uint8Array(12))].map((b) => b.toString(16).padStart(2, '0')).join('');
        settings.pin = { salt, hash: await hash(salt + p1) }; saveSettings();
      }
      unlockedUntil = Date.now() + 10 * 60 * 1000; route();
    };
    $('#go').onclick = go;
    view.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
  }
  const fmt = (sec) => { const m = Math.round(sec / 60); return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, '0')}`; };
  function parents() {
    if (Date.now() > unlockedUntil) return gate();
    const days = []; for (let i = 6; i >= 0; i--) { const d = new Date(Date.now() - i * 864e5); const k = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; days.push({ k, l: d.toLocaleDateString('pt-PT', { weekday: 'short' }).replace('.', ''), sec: (watch.days[k] || {}).sec || 0, n: ((watch.days[k] || {}).videos || []).length }); }
    const week = days.reduce((a, d) => a + d.sec, 0), max = Math.max(60, ...days.map((d) => d.sec));
    const top = Object.values(watch.channels).sort((a, b) => b.sec - a.sec).slice(0, 5);
    const seg = (key, opts, val) => `<div class="seg" data-key="${key}">${opts.map(([v, l]) => `<button data-v="${v}" class="${String(val) === String(v) ? 'on' : ''}">${l}</button>`).join('')}</div>`;
    return `<h1>Área dos pais</h1>
      <div class="kpis" style="margin-top:12px">
        <div class="kpi"><div class="l">Hoje</div><div class="v">${fmt(secsToday())}</div></div>
        <div class="kpi g"><div class="l">Últimos 7 dias</div><div class="v">${fmt(week)}</div></div>
        <div class="kpi o"><div class="l">Vídeos vistos (7 dias)</div><div class="v">${new Set(days.flatMap((d) => (watch.days[d.k] || {}).videos || [])).size}</div></div>
      </div>
      <div class="panel"><h2>Por dia</h2><div class="bars">${days.map((d) => `<div title="${fmt(d.sec)}"><i style="height:${Math.round((d.sec / max) * 90)}px"></i>${esc(d.l)}</div>`).join('')}</div>
        ${top.length ? `<div style="margin-top:12px">${top.map((c) => `<div class="field"><div>${esc(c.name)}</div><b>${fmt(c.sec)}</b></div>`).join('')}</div>` : ''}</div>
      <div class="panel"><h2>Limites</h2>
        <div class="field"><div>Tempo por dia<div class="d">Quando acaba, os vídeos param até amanhã.</div></div>${seg('dailyMin', [[0, 'Sem limite'], [30, '30 min'], [60, '1 h'], [90, '1 h 30'], [120, '2 h']], settings.dailyMin)}</div>
        <div class="field"><div>Hora de dormir<div class="d">Sem vídeos entre estas horas.</div></div>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">${seg('bedOn', [['true', 'Ligada'], ['false', 'Desligada']], settings.bedtime.on)}
          <input type="time" id="bf" value="${esc(settings.bedtime.from)}" /> às <input type="time" id="bt" value="${esc(settings.bedtime.to)}" /></div></div>
      </div>
      <div class="panel"><h2>Canais</h2><p class="muted" style="font-weight:800;margin:6px 0 0">Canais de produção portuguesa, verificados. Desligue os que não quiser.</p>
        ${Object.entries(catalog.channels).filter(([k]) => !pending(k)).map(([k, c]) => `<div class="field"><div><span class="dot" style="display:inline-block;width:11px;height:11px;border-radius:3px;background:${esc(c.cor)};margin-right:7px"></span><b>${esc(c.name)}</b><div class="d">${catalog.videos.filter((v) => v.ch === k).length} vídeos · ${esc(TEMAS[c.tema] || '')}</div></div>
          ${seg('ch:' + k, [['on', 'Ligado'], ['off', 'Desligado']], settings.disabled.includes(k) ? 'off' : 'on')}</div>`).join('')}
      </div>
      <div class="panel"><h2>Canais por confirmar</h2><p class="muted" style="font-weight:800;margin:6px 0 0">Canais com identidade confirmada que se apresentam em português de Portugal, mas cujo áudio ainda não foi verificado. Ficam desligados: ouça um ou dois vídeos e ligue só os que forem mesmo em português europeu.</p>
        ${Object.entries(catalog.channels).filter(([k]) => pending(k)).map(([k, c]) => { const n = catalog.videos.filter((v) => v.ch === k).length; return `<div class="field"><div><span class="dot" style="display:inline-block;width:11px;height:11px;border-radius:3px;background:${esc(c.cor)};margin-right:7px"></span><b>${esc(c.name)}</b>
          <div class="d">${n ? `${n} vídeo${n > 1 ? 's' : ''}` : 'Ainda sem vídeos no catálogo'} · ${esc(TEMAS[c.tema] || '')}${c.nota ? ` · ${esc(c.nota)}` : ''} · <a href="https://www.youtube.com/channel/${esc(c.id)}" target="_blank" rel="noopener">abrir no YouTube</a></div></div>
          ${seg('pch:' + k, [['on', 'Ligado'], ['off', 'Desligado']], settings.enabled.includes(k) ? 'on' : 'off')}</div>`; }).join('')}
      </div>
      <div class="panel"><h2>Acrescentar um vídeo</h2><p class="muted" style="font-weight:800;margin:6px 0 10px">Um vídeo do YouTube que já viu e sabe que é em português europeu.</p>
        <div style="display:grid;gap:8px"><input type="url" id="au" placeholder="Endereço do vídeo (youtube.com/watch?v=… ou youtu.be/…)" /><input type="text" id="at" placeholder="Nome para a criança ver" />
        <button class="btn primary" id="addv">Acrescentar</button></div>
        ${settings.added.map((a) => `<div class="field"><div>${esc(a.title)}<div class="d">${esc(a.id)}</div></div><button class="btn danger" data-rm="${esc(a.id)}">Retirar</button></div>`).join('')}
      </div>
      <div class="panel"><h2>Segurança</h2>
        <div class="field"><div>Bloquear o YouTube<div class="d">Para a criança só ver o BLOCKTIDE TV: no iPhone, Tempo de ecrã → bloquear a app do YouTube e os sites youtube.com; no Android, Family Link → bloquear a app do YouTube.</div></div></div>
        <div class="field"><div>Sair da área dos pais</div><button class="btn" id="lock">Bloquear</button></div>
        <div class="field"><div>Apagar dados deste aparelho<div class="d">PIN, limites, histórico e vídeos acrescentados.</div></div><button class="btn danger" id="wipe">Apagar</button></div>
      </div>
      <p class="muted" style="font-size:12px;font-weight:700;text-align:center">BLOCKTIDE TV · © 2026 Igor Serrano · Os vídeos são reproduzidos pelo leitor do YouTube.</p>`;
  }
  function bindParents() {
    if (Date.now() > unlockedUntil) { bindGate(); return; }
    view.querySelectorAll('.seg[data-key]').forEach((s) => s.querySelectorAll('button').forEach((b) => b.onclick = () => {
      const k = s.dataset.key, v = b.dataset.v;
      if (k === 'dailyMin') settings.dailyMin = Number(v);
      else if (k === 'bedOn') settings.bedtime.on = v === 'true';
      else if (k.startsWith('ch:')) { const c = k.slice(3); settings.disabled = settings.disabled.filter((x) => x !== c); if (v === 'off') settings.disabled.push(c); }
      else if (k.startsWith('pch:')) { const c = k.slice(4); settings.enabled = settings.enabled.filter((x) => x !== c); if (v === 'on') settings.enabled.push(c); }
      saveSettings(); route(); toast('Guardado.');
    }));
    $('#bf').onchange = () => { settings.bedtime.from = $('#bf').value; saveSettings(); toast('Guardado.'); };
    $('#bt').onchange = () => { settings.bedtime.to = $('#bt').value; saveSettings(); toast('Guardado.'); };
    $('#addv').onclick = () => {
      const m = ($('#au').value || '').match(/(?:v=|youtu\.be\/|shorts\/|embed\/)([\w-]{11})/);
      const title = ($('#at').value || '').trim();
      if (!m) { toast('Endereço inválido.'); return; }
      if (!title) { toast('Escreva um nome para o vídeo.'); return; }
      settings.added = [{ id: m[1], title }, ...settings.added.filter((a) => a.id !== m[1])]; saveSettings(); route(); toast('Vídeo acrescentado.');
    };
    view.querySelectorAll('[data-rm]').forEach((b) => b.onclick = () => { settings.added = settings.added.filter((a) => a.id !== b.dataset.rm); saveSettings(); route(); });
    $('#lock').onclick = () => { unlockedUntil = 0; location.hash = '#inicio'; };
    $('#wipe').onclick = () => {
      if (b2.dataset.confirm !== '1') { b2.dataset.confirm = '1'; b2.textContent = 'Carregue outra vez para confirmar'; return; }
      settings = { ...DEF, enabled: [], disabled: [], added: [], bedtime: { ...DEF.bedtime } }; watch = { days: {}, channels: {}, recent: [] }; saveSettings(); saveWatch(); unlockedUntil = 0; location.hash = '#inicio';
    };
    const b2 = $('#wipe');
  }

  // ---------------------------------------------------------------------------
  // Navegação
  // ---------------------------------------------------------------------------
  let toastT = null;
  function toast(t) { const el = $('#toast'); el.textContent = t; el.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { el.hidden = true; }, 2600); }
  function route() {
    stopPlayer(); current = null;
    const h = (location.hash || '#inicio').slice(1);
    const r = stopReason();
    if (r && !h.startsWith('pais')) { view.innerHTML = stopScreen(r); return; }
    if (h.startsWith('ver-')) { const id = h.slice(4); view.innerHTML = watchPage(id); bindWatch(id); }
    else if (h.startsWith('canal-')) view.innerHTML = channelPage(h.slice(6));
    else if (h === 'procurar') { view.innerHTML = searchPage(); bindSearch(); }
    else if (h === 'pais') { view.innerHTML = parents(); bindParents(); }
    else {
      view.innerHTML = home();
      view.querySelectorAll('[data-tema]').forEach((b) => b.onclick = () => { tema = b.dataset.tema; route(); });
    }
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', route);

  (async () => {
    try { catalog = await (await fetch('catalog.json', { cache: 'no-cache' })).json(); } catch (_) { view.innerHTML = '<div class="empty">Sem ligação. Tente outra vez.</div>'; return; }
    route();
    if ('serviceWorker' in navigator && location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
      try { await navigator.serviceWorker.register('sw.js'); } catch (_) { /* sem modo offline */ }
    }
  })();
  window.BTV = { videos, upNext, stopReason, get settings() { return settings; } };
})();
