"""BLOCKTIDE TV: validação estática da integridade e da política editorial."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COUNTRIES_BR = {"br", "bra", "brasil", "brazil"}
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
STATUSES = {"verificado", "pendente", "internacional"}
LANGUAGES = {"pt-PT", "sem-dialogo", "en", "es", "fr", "de", "it", "nl"}


def is_brazilian(value):
    return str(value or "").strip().casefold() in COUNTRIES_BR


def is_blocked(item, channel):
    return (
        item.get("blocked") is True
        or any(is_brazilian(item.get(k)) or is_brazilian(channel.get(k))
               for k in ("country", "originCountry", "market"))
        or str(item.get("lang", "")).strip().lower().replace("_", "-") == "pt-br"
    )


def validate(catalog):
    errors = []
    channels = catalog.get("channels", {})
    videos = catalog.get("videos", [])
    shorts = catalog.get("shorts", [])
    seen = set()

    if not isinstance(channels, dict) or not isinstance(videos, list) or not isinstance(shorts, list):
        return ["Estrutura do catálogo inválida"]

    for key, channel in channels.items():
        if channel.get("status") not in STATUSES:
            errors.append(f"Canal {key}: estado desconhecido")
        if any(is_brazilian(channel.get(k)) for k in ("country", "originCountry", "market")):
            errors.append(f"Canal {key}: origem brasileira")
        if not channel.get("name"):
            errors.append(f"Canal {key}: sem nome")

    for kind, collection in (("video", videos), ("short", shorts)):
        for item in collection:
            vid = item.get("id", "")
            ch_key = item.get("ch", "")
            if not VIDEO_ID.fullmatch(str(vid)):
                errors.append(f"{kind} {vid}: ID inválido")
            if vid in seen:
                errors.append(f"{kind} {vid}: duplicado")
            seen.add(vid)
            if ch_key not in channels:
                errors.append(f"{kind} {vid}: canal inexistente ({ch_key})")
            channel = channels.get(ch_key, {})
            if is_blocked(item, channel):
                errors.append(f"{kind} {vid}: conteúdo bloqueado/BR")
            if kind == "short":
                if item.get("vertical") is not True or not isinstance(item.get("sec"), int) or not 0 < item["sec"] <= 180:
                    errors.append(f"short {vid}: duração/verticalidade inválida")
                if item.get("lang") not in LANGUAGES:
                    errors.append(f"short {vid}: idioma não permitido")
            if kind == "video" and channel.get("status") == "internacional":
                errors.append(f"video {vid}: canal internacional reservado a Shorts")
    return errors


class CatalogPolicyTests(unittest.TestCase):
    def test_catalog(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        errors = validate(catalog)
        self.assertEqual(errors, [], "\n".join(errors))
        print(f"Catálogo válido: {len(catalog['videos'])} vídeos, {len(catalog['shorts'])} Shorts, {len(catalog['channels'])} canais.")

    def test_brazilian_language_rejected(self):
        self.assertTrue(is_blocked({"lang": "pt-BR"}, {}))
        self.assertTrue(is_blocked({"lang": "PT_br"}, {}))

    def test_brazilian_origin_rejected(self):
        self.assertTrue(is_blocked({"originCountry": "BR"}, {}))
        self.assertTrue(is_blocked({}, {"market": "Brazil"}))
        self.assertTrue(is_blocked({"blocked": True}, {}))

    def test_non_brazilian_allowed(self):
        self.assertFalse(is_blocked({"lang": "pt-PT", "originCountry": "PT"}, {"market": "PT"}))

    def test_duplicate_detected(self):
        sample = {"channels": {"a": {"name": "Canal", "status": "verificado"}},
                  "videos": [{"id": "abcdefghijk", "ch": "a"}, {"id": "abcdefghijk", "ch": "a"}],
                  "shorts": []}
        self.assertTrue(any("duplicado" in e for e in validate(sample)))

    def test_unreviewed_channel_stays_pending(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        for key in ("mega", "cartoonito", "moonbug", "disneyjr", "guilherme"):
            self.assertEqual(catalog["channels"][key]["status"], "pendente")


if __name__ == "__main__":
    unittest.main(verbosity=2)
