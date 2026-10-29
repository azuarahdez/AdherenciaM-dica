"""Guarda cada cuestionario contestado como una línea JSON en datos/respuestas.jsonl."""
import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

# En el celular (app de Flet) la carpeta de la app es de solo lectura: se usa la carpeta de
# datos privada que Flet indica en FLET_APP_STORAGE_DATA.
_CARPETA = os.environ.get("FLET_APP_STORAGE_DATA")
ARCHIVO = (Path(_CARPETA) if _CARPETA else Path(__file__).resolve().parent.parent / "datos") \
    / "respuestas.jsonl"


def guardar(paciente, resultado, respuestas):
    ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
    registro = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "paciente": paciente,
        **asdict(resultado),
        "respuestas": respuestas,
    }
    with ARCHIVO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
