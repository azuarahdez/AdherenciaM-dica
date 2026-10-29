"""App móvil nativa de adherencia terapéutica (Flet).

Probar en la computadora:  flet run main.py
Probar en el celular:      flet run --android main.py   (con la app "Flet" instalada)
Generar el APK:            flet build apk
"""
import flet as ft

from movil.app import App


def main(page: ft.Page):
    App(page)


if __name__ == "__main__":
    ft.run(main)
