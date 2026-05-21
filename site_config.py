import json
import os

_FILE = "site.json"


def _load() -> dict:
    try:
        with open(_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(cfg: dict) -> None:
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_logo_path() -> str | None:
    return _load().get("logo_path")


def set_logo_path(path: str | None) -> None:
    cfg = _load()
    cfg["logo_path"] = path
    _save(cfg)


def get_site_name() -> str | None:
    return _load().get("site_name")


def set_site_name(name: str | None) -> None:
    cfg = _load()
    cfg["site_name"] = name or None
    _save(cfg)
