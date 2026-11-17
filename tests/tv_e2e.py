# BLOCKTIDE — © 2026 Igor Serrano. Todos os direitos reservados. Ver LICENSE.
# BLOCKTIDE TV (web app): catálogo, leitor (API do YouTube simulada), «a seguir», tempo, limites, pais, pesquisa, offline.
import json, pathlib, threading, http.server, functools, time, base64
from playwright.sync_api import sync_playwright
TV = pathlib.Path(__file__).resolve().parents[1]; OUT = pathlib.Path(__file__).resolve().parent / 'shots'; OUT.mkdir(exist_ok=True)
class H(http.server.SimpleHTTPRequestHandler):
  def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(H, directory=str(TV)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
# API do YouTube simulada: regista o que a app pede e deixa o teste mudar o estado do leitor
YT_STUB = """window.__yt = { created: [], loaded: [], noAutoplay: false };
window.YT = { Player: function (id, opts) {
  const el = document.getElementById(id); const f = document.createElement('iframe');
  f.src = 'about:blank'; f.dataset.video = opts.videoId; f.dataset.host = opts.host || ''; f.style.background = '#223';
  el.replaceWith(f); f.id = id;
  window.__yt.created.push({ videoId: opts.videoId, host: opts.host, vars: opts.playerVars });
  const self = this; let st = -1; window.__yt.player = self;
  window.__yt.state = (s) => { st = s; opts.events.onStateChange && opts.events.onStateChange({ data: s, target: self }); };
  const autoplay = () => setTimeout(() => { if (!window.__yt.noAutoplay || window.__yt.muted) window.__yt.state(1); }, 50);
  this.destroy = () => { window.__yt.destroyed = (window.__yt.destroyed || 0) + 1; }; this.seekTo = () => {};
  this.playVideo = () => { if (!window.__yt.noAutoplay || window.__yt.muted || window.__yt.gesture) window.__yt.state(1); };
  this.mute = () => { window.__yt.muted = true; }; this.unMute = () => { window.__yt.muted = false; }; this.setVolume = () => {};
  this.pauseVideo = () => window.__yt.state(2); this.getPlayerState = () => st;
  this.loadVideoById = (vid) => { window.__yt.loaded.push(vid); st = -1; autoplay(); };
  setTimeout(() => { opts.events.onReady && opts.events.onReady({ target: self }); autoplay(); }, 30);
} };
setTimeout(() => window.onYouTubeIframeAPIReady && window.onYouTubeIframeAPIReady(), 10);"""
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
def handle(route):
  u = route.request.url
  if 'youtube.com/iframe_api' in u: return route.fulfill(status=200, body=YT_STUB, content_type='text/javascript')
  if 'i.ytimg.com' in u: return route.fulfill(status=200, body=PNG, content_type='image/png')
  return route.fulfill(status=404, body='')
ok = True
def check(name, cond):
  global ok; ok &= bool(cond); print(('OK  ' if cond else 'FALHA ') + name)
with sync_playwright() as p:
  b = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True)
  ctx = b.new_context(**p.devices['iPhone 13'], service_workers='allow')
  ctx.route(lambda u: 'youtube.com' in u or 'ytimg.com' in u, handle)
  pg = ctx.new_page(); errs = []
  pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
  pg.goto(URL); pg.wait_for_selector('.card')
  n_cards = pg.locator('.rail .card').count(); rows = pg.locator('section.row').count()
  check(f'início: {rows} filas (6 canais + Shorts) e {n_cards} cartões', rows == 7 and n_cards == 72)
  pg.screenshot(path=str(OUT / '40-tv-inicio.png'))
  pg.click('[data-tema="musica"]'); pg.wait_for_timeout(200)
  names = pg.locator('section.row h2').all_inner_texts()
  check(f'tema «Música»: {names}', set(names) == {'Panda e os Caricas', 'Xana Toc Toc', 'Avô Cantigas'})
  pg.click('[data-tema="tudo"]')
  # Ver um vídeo
  pg.goto(URL + '#ver-xOIsbH2-fkI'); pg.wait_for_function('window.__yt && window.__yt.created.length > 0')
  cr = pg.evaluate('window.__yt.created[0]')
  check(f"leitor oficial com youtube-nocookie e sem sugestões externas ({cr['host']}, rel={cr['vars']['rel']})", cr['videoId'] == 'xOIsbH2-fkI' and 'nocookie' in cr['host'] and cr['vars']['rel'] == 0 and cr['vars']['playsinline'] == 1)
  nxt = pg.locator('.upnext .card .t').all_inner_texts()
  check(f'«a seguir» com 8 vídeos, o primeiro do mesmo tema: {nxt[:2]}', len(nxt) == 8 and 'xOIsbH2-fkI' not in pg.inner_html('.upnext'))
  pg.screenshot(path=str(OUT / '41-tv-ver.png'))
  pg.wait_for_timeout(10800)
  w = pg.evaluate("JSON.parse(localStorage.getItem('btv.watch'))")
  sec = sum(d['sec'] for d in w['days'].values())
  check(f'tempo contado só a reproduzir ({sec} s)', 10 <= sec <= 15)
  pg.evaluate('window.__yt.state(2)'); pg.wait_for_timeout(5600)
  sec2 = sum(d['sec'] for d in pg.evaluate("JSON.parse(localStorage.getItem('btv.watch'))")['days'].values())
  check('em pausa o tempo não conta', sec2 == sec)
  # Fim do vídeo → ecrã «a seguir» com contagem → passa sozinho
  pg.evaluate('window.__yt.state(0)'); pg.wait_for_timeout(500)
  check('ecrã «A seguir» no fim do vídeo', pg.locator('#cover:not([hidden]) .next').count() == 1)
  pg.screenshot(path=str(OUT / '42-tv-a-seguir.png'))
  t0 = time.time()
  while time.time() - t0 < 9 and 'xOIsbH2-fkI' in pg.url: pg.wait_for_timeout(250)
  check(f'passou sozinho ao seguinte ao fim de ~6 s ({pg.url.split("#")[-1]})', 'xOIsbH2-fkI' not in pg.url and '#ver-' in pg.url)
  # Shorts: deslizar na vertical, um leitor de cada vez
  pg.goto(URL + '#inicio'); pg.wait_for_selector('.card')
  check('fila de Shorts no início (30, primeiro os portugueses)', pg.locator('.shorts-rail .scard').count() == 30)
  pg.evaluate('window.__yt.created = []')
  pg.goto(URL + '#shorts'); pg.wait_for_function('window.__yt.created.length > 0')
  first = pg.evaluate('window.__yt.created[0]')
  check(f"Shorts: {pg.locator('.short').count()} vídeos; o primeiro toca sem som e sem controlos ({first['videoId']}, mute={first['vars']['mute']})", pg.locator('.short').count() == 108 and first['vars']['mute'] == 1 and first['vars']['controls'] == 0)
  pg.screenshot(path=str(OUT / '45-tv-shorts.png'))
  pg.click('#ssound'); pg.wait_for_timeout(200)
  check('«Toca para ouvir» liga o som', pg.evaluate('window.__yt.muted') is False)
  pg.evaluate("document.querySelectorAll('.short')[1].scrollIntoView()"); pg.wait_for_timeout(900)
  check(f"ao deslizar, o MESMO leitor muda de vídeo (leitores criados: {len(pg.evaluate('window.__yt.created'))}, carregados: {pg.evaluate('window.__yt.loaded')})", len(pg.evaluate('window.__yt.created')) == 1 and len(pg.evaluate('window.__yt.loaded')) == 1 and pg.evaluate('window.__yt.loaded[0]') != first['videoId'])
  pe = pg.evaluate("[getComputedStyle(document.querySelector('#sdock')).pointerEvents, getComputedStyle(document.querySelector('#sdock iframe')).pointerEvents]")
  check(f'o leitor deixa passar o dedo para deslizar ({pe})', pe == ['none', 'none'])
  pts = pg.evaluate("(()=>{const d=document.querySelector('#sdock').getBoundingClientRect(); const out=[]; for (const fx of [.1,.5,.9]) for (const fy of [.1,.5,.9]) { const el=document.elementFromPoint(d.left+d.width*fx, d.top+d.height*fy); out.push(!!el.closest('.short') && !el.closest('#sdock')); } return out})()")
  check(f'o dedo toca sempre no Short (e não no vídeo) em todo o ecrã: {pts}', all(pts))
  check('o leitor está dentro da lista, por baixo dos Shorts', pg.evaluate("document.querySelector('#sdock').parentElement.id === 'feed' && getComputedStyle(document.querySelector('#sdock')).zIndex === '0'"))
  check('o Short a tocar deixa ver o vídeo por baixo', pg.evaluate("getComputedStyle(document.querySelector('.short.live .sposter')).opacity") == '0')
  fw = pg.evaluate("[document.querySelector('.short.live .sframe').getBoundingClientRect().width, innerWidth]")
  check(f'no telemóvel o Short ocupa a largura toda do ecrã ({fw[0]:.0f} de {fw[1]} px)', abs(fw[0] - fw[1]) < 1)
  cdp = ctx.new_cdp_session(pg)
  for label, fx in (('ao centro', .5), ('à esquerda', .2), ('à direita', .8)):
    t0 = pg.evaluate("document.querySelector('#feed').scrollTop")
    vw, vh = pg.evaluate('[innerWidth, innerHeight]')
    x, y0, y1 = int(vw * fx), int(vh * .7), int(vh * .3)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y0}]})
    for k in range(1, 13):
      cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y0 + (y1 - y0) * k / 12}]}); pg.wait_for_timeout(16)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    pg.wait_for_timeout(1300)
    t1 = pg.evaluate("document.querySelector('#feed').scrollTop")
    check(f'deslizar com o dedo para cima {label} do vídeo passa ao Short seguinte ({t0} → {t1})', t1 > t0)
  feed_top0 = pg.evaluate("document.querySelector('#feed').scrollTop")
  box = pg.evaluate("(()=>{const d=document.querySelector('#sdock').getBoundingClientRect(); return [d.left+d.width/2, d.top+d.height/2]})()")
  pg.mouse.move(*box); pg.mouse.wheel(0, 900); pg.wait_for_timeout(1200)
  check(f"rodar/deslizar por cima do vídeo avança na lista ({feed_top0} → {pg.evaluate('document.querySelector(\'#feed\').scrollTop')})", pg.evaluate("document.querySelector('#feed').scrollTop") > feed_top0)
  check('o som ligado mantém-se no Short seguinte', pg.evaluate('window.__yt.muted') is False)
  n0 = len(pg.evaluate('window.__yt.loaded'))
  pg.evaluate('window.__yt.state(0)'); pg.wait_for_timeout(1200)
  check('no fim de um Short passa sozinho ao seguinte', len(pg.evaluate('window.__yt.loaded')) == n0 + 1)
  # Simular iPhone: sem som não há autorização para arrancar → a app volta a tentar sem som e mostra «Toca para ouvir»
  pg.evaluate('window.__yt.noAutoplay = true')
  pg.evaluate("document.querySelectorAll('.short')[4].scrollIntoView()"); pg.wait_for_timeout(2200)
  check(f"se não arrancar com som, recomeça sem som e mostra «Toca para ouvir» (estado {pg.evaluate('window.__yt.player.getPlayerState()')})", pg.evaluate('window.__yt.player.getPlayerState()') == 1 and pg.evaluate('window.__yt.muted') is True and pg.locator('#ssound:not([hidden])').count() == 1)
  pg.evaluate('window.__yt.noAutoplay = false')
  langs = pg.evaluate("[...document.querySelectorAll('.short .badge-pt')].map(b=>b.textContent.trim())")
  first_foreign = next((i for i, t in enumerate(langs) if 'Português' not in t), None)
  check(f"Shorts de outros países a seguir aos portugueses (a partir do n.º {first_foreign}: {sorted(set(langs))})", first_foreign == 30 and all('Português' not in t for t in langs[30:]) and {'Inglês', 'Sem diálogo', 'Espanhol', 'Francês'} <= set(langs))
  check('todos os Shorts são verticais e até 3 minutos', all(v.get('vertical') and 0 < v.get('sec', 0) <= 180 for v in pg.evaluate("fetch('catalog.json').then(r => r.json()).then(c => c.shorts)")))
  check('nenhum Short em PT-BR no catálogo', all((v.get('lang') or '').lower() != 'pt-br' for v in pg.evaluate("fetch('catalog.json').then(r => r.json()).then(c => c.shorts)")))
  # Pesquisa só no catálogo
  pg.goto(URL + '#procurar'); pg.fill('#q', 'astronauta'); pg.wait_for_timeout(200)
  res = pg.locator('#results .card .t').all_inner_texts()
  check(f'pesquisa «astronauta» → {res}', len(res) == 2)
  pg.fill('#q', 'Luccas Neto'); pg.wait_for_timeout(200)
  check('pesquisa fora do catálogo não mostra nada', pg.locator('#results .card').count() == 0)
  # Área dos pais
  pg.goto(URL + '#pais'); pg.fill('#p1', '2468'); pg.fill('#p2', '2468'); pg.click('#go'); pg.wait_for_timeout(300)
  check('PIN criado e área dos pais aberta', pg.locator('h1').first.inner_text() == 'Área dos pais')
  pg.screenshot(path=str(OUT / '43-tv-pais.png'), full_page=True)
  check('Shorts de outros países têm painel próprio nos pais', pg.locator('.seg[data-key="ch:bluey"] button.on[data-v="on"]').count() == 1)
  pg.click('.seg[data-key="ch:bluey"] button[data-v="off"]'); pg.click('.seg[data-key="shortsOtherLangs"] button[data-v="false"]'); pg.wait_for_timeout(200)
  pg.goto(URL + '#shorts'); pg.wait_for_selector('.short')
  langs = set(pg.evaluate("[...document.querySelectorAll('.short .badge-pt')].map(b=>b.textContent.trim())"))
  check(f"com «Só PT-PT e sem diálogo»: {pg.locator('.short').count()} Shorts, idiomas {sorted(langs)}", langs == {'✓ Português europeu', 'Sem diálogo'} and pg.locator('.short').count() == 50)
  pg.goto(URL + '#pais'); pg.wait_for_selector('.seg[data-key="ch:panda"]')
  pg.click('.seg[data-key="ch:bluey"] button[data-v="on"]'); pg.click('.seg[data-key="shortsOtherLangs"] button[data-v="true"]'); pg.wait_for_timeout(200)
  pg.click('.seg[data-key="ch:panda"] button[data-v="off"]'); pg.wait_for_timeout(200)
  check('canais por confirmar aparecem na área dos pais, desligados', pg.locator('.seg[data-key="pch:cartoonito"] button.on[data-v="off"]').count() == 1)
  pg.click('.seg[data-key="pch:cartoonito"] button[data-v="on"]'); pg.wait_for_timeout(200)
  pg.fill('#au', 'https://youtu.be/dQw4w9WgXcQ'); pg.fill('#at', 'Vídeo da família'); pg.click('#addv'); pg.wait_for_timeout(200)
  pg.click('.seg[data-key="shortsOn"] button[data-v="false"]'); pg.wait_for_timeout(200)
  pg.goto(URL + '#inicio'); pg.wait_for_selector('.card')
  heads = pg.locator('section.row h2').all_inner_texts()
  check('pais desligam os Shorts: sai a fila do início', 'Shorts' not in heads)
  pg.goto(URL + '#shorts'); pg.wait_for_timeout(300)
  check('e a página de Shorts explica que estão desligados', 'desligados' in pg.inner_text('#view'))
  pg.goto(URL + '#inicio'); pg.wait_for_selector('.card')
  check(f'canal desligado sai do início e vídeo dos pais aparece: {heads}', 'Canal Panda' not in heads and 'Escolhidos pelos pais' in heads)
  check('canal por confirmar ligado pelos pais aparece no início', 'Cartoonito Portugal' in heads and 'Moonbug Portugal' not in heads)
  # Limite diário
  pg.evaluate("""() => { const s = JSON.parse(localStorage.getItem('btv.settings')); s.dailyMin = 30; localStorage.setItem('btv.settings', JSON.stringify(s));
    const w = JSON.parse(localStorage.getItem('btv.watch')); const d = new Date(); const k = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
    w.days[k] = { sec: 1800, videos: [] }; localStorage.setItem('btv.watch', JSON.stringify(w)); }""")
  pg.reload(); pg.wait_for_timeout(600)
  check('limite de 30 min atingido → ecrã «Acabou o tempo»', 'Acabou o tempo' in pg.inner_text('#view'))
  pg.goto(URL + '#ver-MSkoCcj0Q5U'); pg.wait_for_timeout(400)
  check('com o limite atingido, um vídeo direto também não abre', 'Acabou o tempo' in pg.inner_text('#view'))
  pg.screenshot(path=str(OUT / '44-tv-limite.png'))
  # Hora de dormir
  pg.evaluate("""() => { const s = JSON.parse(localStorage.getItem('btv.settings')); s.dailyMin = 0; const d = new Date(); const hh = (x) => String(x).padStart(2,'0');
    s.bedtime = { on: true, from: `${hh(d.getHours())}:00`, to: `${hh((d.getHours()+2)%24)}:00` }; localStorage.setItem('btv.settings', JSON.stringify(s)); }""")
  pg.reload(); pg.wait_for_timeout(600)
  check('hora de dormir → «Está na hora de descansar»', 'hora de descansar' in pg.inner_text('#view'))
  # Web app instalável e sem rede
  man = pg.evaluate("fetch('manifest.webmanifest').then(r => r.json())")
  sw = pg.evaluate("navigator.serviceWorker.getRegistration().then(r => !!(r && r.active))")
  check(f"instalável: manifesto ({man['display']}, {len(man['icons'])} ícones) e service worker ativo ({sw})", man['display'] == 'standalone' and sw)
  pg.evaluate("""() => { const s = JSON.parse(localStorage.getItem('btv.settings')); s.bedtime.on = false; localStorage.setItem('btv.settings', JSON.stringify(s)); }""")
  pg.goto(URL + '#inicio'); pg.reload(); pg.wait_for_selector('.card')
  ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(1200)
  print('   (sem rede)', pg.locator('.card').count(), 'cartões |', pg.evaluate("(document.querySelector('#view')||document.body).innerText.slice(0,90).replace(/\\n/g,' ')"))
  check('sem rede: a app abre a partir do aparelho', pg.locator('.card').count() > 10)
  ctx.set_offline(False)
  bad = [e for e in errs if 'ERR_INTERNET_DISCONNECTED' not in e and 'Failed to load resource' not in e]
  check('sem erros na consola', not bad)
  for e in bad: print('  ', e[:200])
  b.close()
print('RESULTADO:', 'PASSOU' if ok else 'FALHOU')
