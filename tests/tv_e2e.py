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
YT_STUB = """window.__yt = { created: [] };
window.YT = { Player: function (id, opts) {
  const el = document.getElementById(id); const f = document.createElement('iframe');
  f.src = 'about:blank'; f.dataset.video = opts.videoId; f.dataset.host = opts.host || ''; f.style.background = '#223';
  el.replaceWith(f); f.id = id;
  window.__yt.created.push({ videoId: opts.videoId, host: opts.host, vars: opts.playerVars });
  const self = this; window.__yt.player = self; window.__yt.state = (s) => opts.events.onStateChange({ data: s, target: self });
  this.destroy = () => { window.__yt.destroyed = (window.__yt.destroyed || 0) + 1; }; this.seekTo = () => {}; this.playVideo = () => window.__yt.state(1);
  this.mute = () => { window.__yt.muted = true; }; this.unMute = () => { window.__yt.muted = false; }; this.pauseVideo = () => window.__yt.state(2);
  setTimeout(() => window.__yt.state(1), 50);
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
  check(f'início: {rows} filas (6 canais + Shorts) e {n_cards} cartões', rows == 7 and n_cards == 52)
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
  check('fila de Shorts no início', pg.locator('.shorts-rail .scard').count() == 10)
  pg.evaluate('window.__yt.created = []')
  pg.goto(URL + '#shorts'); pg.wait_for_function('window.__yt.created.length > 0')
  first = pg.evaluate('window.__yt.created[0]')
  check(f"Shorts: {pg.locator('.short').count()} vídeos; o primeiro toca sem som e sem controlos ({first['videoId']}, mute={first['vars']['mute']})", pg.locator('.short').count() == 10 and first['vars']['mute'] == 1 and first['vars']['controls'] == 0)
  pg.screenshot(path=str(OUT / '45-tv-shorts.png'))
  pg.click('.short:first-child .sound'); pg.wait_for_timeout(200)
  check('«Toca para ouvir» liga o som', pg.evaluate('window.__yt.muted') is False)
  pg.evaluate("document.querySelectorAll('.short')[1].scrollIntoView()"); pg.wait_for_timeout(900)
  ids = [c['videoId'] for c in pg.evaluate('window.__yt.created')]
  check(f"ao deslizar, toca o Short seguinte com som ({ids[-1]}, mute={pg.evaluate('window.__yt.created.at(-1).vars.mute')}) e o anterior é fechado", len(ids) == 2 and ids[1] != ids[0] and pg.evaluate('window.__yt.created.at(-1).vars.mute') == 0 and pg.evaluate('window.__yt.destroyed') >= 1)
  pg.evaluate('window.__yt.state(0)'); pg.wait_for_timeout(1200)
  check('no fim de um Short passa sozinho ao seguinte', len(pg.evaluate('window.__yt.created')) == 3)
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
