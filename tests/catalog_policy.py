"""Testes estáticos do catálogo infantil BLOCKTIDE."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
channels = data['channels']
items = data['videos'] + data['shorts']
def is_br(s):
    return str(s or '').strip().lower() in {'br', 'bra', 'brasil', 'brazil'}
for key, channel in channels.items():
    assert channel['status'] in {'verificado', 'pendente', 'internacional'}, key
    assert not any(is_br(channel.get(k)) for k in ('country', 'originCountry', 'market')), key
seen = set()
for item in items:
    vid = item['id']
    assert re.fullmatch(r'[a-zA-Z0-9_-]{11}', vid), (vid, 'id inválido')
    assert vid not in seen, (vid, 'id duplicado')
    seen.add(vid)
    assert item['ch'] in channels, (vid, 'canal inexistente')
    assert not any(is_br(item.get(k)) for k in ('country', 'originCountry', 'market')), vid
    assert str(item.get('lang', '')).strip().lower().replace('_', '-') != 'pt-br', vid
for item in data['shorts']:
    assert item.get('vertical') is True and 0 < item.get('sec', 0) <= 180, (item['id'], 'short inválido')
print(f"OK: {len(data['videos'])} vídeos, {len(data['shorts'])} Shorts, {len(channels)} canais, sem duplicados nem conteúdos BR assinalados.")
