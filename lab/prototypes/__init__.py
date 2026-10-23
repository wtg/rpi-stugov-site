"""Alternate site layouts under evaluation.

Each prototype is a subpackage that defines ``META`` (name, thesis,
recommended) in its ``__init__.py`` and ``urlpatterns`` in ``urls.py``.
Templates live in ``lab/templates/lab/<slug>/``. Prototypes are discovered
automatically, so adding one never touches shared files.
"""

import importlib
import pkgutil


def discover():
    prototypes = []
    for info in pkgutil.iter_modules(__path__):
        if not info.ispkg:
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        meta = getattr(module, "META", {})
        prototypes.append({"slug": info.name.replace("_", "-"), "module": info.name, **meta})
    return sorted(prototypes, key=lambda p: (not p.get("recommended", False), p["slug"]))
