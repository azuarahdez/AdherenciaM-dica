"""Pantallas del personal de salud: pacientes, detalle, alertas y modelo FCM."""
import flet as ft
import flet.canvas as cv

from adherencia import datos_demo as demo
from movil import ui

SEVERIDAD = {"alta": ("Alta", "bad"), "media": ("Media", "warn")}


def _kpis(app):
    cuenta = {e: sum(p["etiqueta"] == e for p in demo.PACIENTES) for e in ("Bueno", "Regular", "Malo")}
    datos = [("Pacientes", len(demo.PACIENTES), ui.TEAL), ("Bueno", cuenta["Bueno"], ui.VERDE),
             ("Regular", cuenta["Regular"], ui.AMBAR), ("Malo", cuenta["Malo"], ui.ROJO)]
    controles = [ft.Row([
        ft.Container(ft.Column([ui.sub(t, 11), ui.texto(str(v), 24, c, negrita=True)], spacing=0,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                     bgcolor=ft.Colors.WHITE, border=ft.Border.all(1, ui.BORDE),
                     border_radius=14, padding=8, expand=True)
        for t, v, c in datos], spacing=6)]
    alertas = sum(len(p["alertas"]) for p in demo.PACIENTES)
    pendientes = alertas - len(app.atendidas)
    if pendientes > 0:
        controles.append(ui.boton(f"{pendientes} alertas sin atender", lambda: app.ir("m_alertas"),
                                  ft.Icons.NOTIFICATIONS_ACTIVE, principal=True))
    return controles


def _tarjeta_paciente(app, p):
    color = ui.COLOR_ETIQUETA[p["etiqueta"]]
    chips = [ui.chip(p["etiqueta"], ui.CHIP_ETIQUETA[p["etiqueta"]])]
    if p["alertas"]:
        chips.append(ui.chip(f"🔔 {len(p['alertas'])}", "bad"))

    def abrir():
        app.paciente_sel = p["id"]
        app.ir("m_detalle")

    return ui.tarjeta([
        ft.Row([
            ft.Text(ui.CARITA_ETIQUETA[p["etiqueta"]], size=34),
            ft.Column([ui.texto(f"{p['nombre']}", 16, negrita=True),
                       ui.sub(f"{p['edad']} años · {p['tratamiento']}")], spacing=0, expand=True),
            ft.Column([ft.Row(chips, spacing=4),
                       ui.texto(f"C28 = {p['c28']:.3f}", 14, color, negrita=True)],
                      spacing=4, horizontal_alignment=ft.CrossAxisAlignment.END),
        ], vertical_alignment=ft.CrossAxisAlignment.START),
        ui.barra(p["c28"], color),
    ], on_click=lambda: abrir())


def pagina_panel(app):
    lista = ft.Column(spacing=12)

    def filtrar(filtro):
        lista.controls = [_tarjeta_paciente(app, p)
                          for p in sorted(demo.PACIENTES, key=lambda p: p["c28"])
                          if filtro == "Todos" or p["etiqueta"] == filtro]

    def al_cambiar(e):
        filtrar(e.control.selected[0])
        lista.update()

    filtrar("Todos")
    filtro = ft.SegmentedButton(
        segments=[ft.Segment(f, label=f) for f in ("Todos", "Bueno", "Regular", "Malo")],
        selected=["Todos"], show_selected_icon=False, on_change=al_cambiar)
    return [ui.titulo("Mis pacientes", "Ordenados del que más atención necesita al que menos. "
                                       "Toca uno para ver su ficha."),
            *_kpis(app), filtro, lista]


def pagina_detalle(app):
    p = next(x for x in demo.PACIENTES if x["id"] == app.paciente_sel)
    color = ui.COLOR_ETIQUETA[p["etiqueta"]]
    controles = [ui.tarjeta(ft.Row([
        ui.anillo(p["c28"], f"{p['c28']:.2f}", "C28", color,
                  carita=ui.CARITA_ETIQUETA[p["etiqueta"]]),
        ft.Column([ui.texto(p["nombre"], 17, negrita=True),
                   ui.sub(f"{p['edad']} años · {p['tratamiento']}"),
                   ft.Row([ui.texto("Adherencia:"),
                           ui.chip(p["etiqueta"], ui.CHIP_ETIQUETA[p["etiqueta"]])])],
                  expand=True, spacing=4),
    ], spacing=16))]

    for nivel, texto, cuando in p["alertas"]:
        etiqueta, _ = SEVERIDAD[nivel]
        controles.append(ui.aviso(f"**Alerta {etiqueta.lower()}** · {texto} · {cuando}"))

    finales = [(f"C{c} · {demo.CONCEPTOS[c]}", p["valores"][c], c) for c in (24, 25, 26, 27)]
    controles.append(ui.tarjeta(ui.barras_h(finales), "Factores que alimentan C28"))

    peor = min((24, 25, 26, 27), key=lambda c: p["valores"][c])
    controles.append(ui.tarjeta([ui.texto(f"Prioridad: {demo.CONCEPTOS[peor]}", negrita=True),
                                 ui.sub(demo.RECOMENDACION[peor])], "💡 Recomendación sugerida"))

    grupos = []
    for final, entradas in demo.GRUPOS.items():
        items = [(f"C{c} · {demo.CONCEPTOS[c]}", p["valores"][c], c) for c in entradas]
        grupos += [ui.texto(f"C{final} · {demo.CONCEPTOS[final]}", 15, negrita=True),
                   ui.barras_h(items)]
    controles.append(ft.Container(
        ft.ExpansionTile(title="Ver los 23 conceptos de entrada", controls=grupos,
                         controls_padding=16, shape=ft.RoundedRectangleBorder(radius=16),
                         collapsed_shape=ft.RoundedRectangleBorder(radius=16)),
        bgcolor=ft.Colors.WHITE, border=ft.Border.all(1, ui.BORDE), border_radius=16))

    semanas = p["semanas"]
    controles.append(ui.tarjeta(ui.barras_v(semanas, [f"S{i + 1}" for i in range(len(semanas))]),
                                "Adherencia semanal (pastillero)"))
    controles.append(ft.Row([
        ui.boton("Generar reporte", lambda: app.avisar("Próximamente"), ft.Icons.DESCRIPTION,
                 expand=True),
        ui.boton("Enviar mensaje", lambda: app.avisar("Próximamente"), ft.Icons.MESSAGE,
                 expand=True),
    ]))
    return controles


def pagina_alertas(app):
    controles = [ui.titulo("Alertas", "Requieren atención del personal de salud.")]

    def atender(clave):
        app.atendidas.add(clave)
        app.dibujar()

    for p in demo.PACIENTES:
        for nivel, texto, cuando in p["alertas"]:
            clave = f"{p['id']}-{texto}"
            etiqueta, tipo = SEVERIDAD[nivel]
            atendida = clave in app.atendidas
            contenido = [ui.fila(ft.Column([ui.texto(texto, negrita=True),
                                            ui.sub(f"{p['nombre']} · {cuando}")], spacing=0),
                                 ui.chip("Atendida", "ok") if atendida else ui.chip(etiqueta, tipo),
                                 divisor=False)]
            if not atendida:
                contenido.append(ft.TextButton("Marcar como atendida", icon=ft.Icons.DONE,
                                               on_click=lambda e, c=clave: atender(c)))
            controles.append(ui.tarjeta(contenido))
    controles.append(ui.sub("Protocolo: una respuesta positiva en el ítem 9 del PHQ-9 genera una "
                            "alerta inmediata al personal de salud, sin importar el puntaje total."))
    return controles


# ------------------------------------------------------------------ modelo FCM
COLOR_GRUPO = {24: ui.TEAL, 25: "#5b47b5", 26: ui.AMBAR, 27: ui.VERDE}


def _diagrama():
    """Diagrama por capas del mapa: entradas → intermedios → factores → C28."""
    capas = [[1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 14, 15, 16, 17, 20, 21, 22],
             [8, 9, 13, 18, 19, 23], [24, 25, 26, 27], [28]]
    ancho, alto = 340, 470
    xs = [30, 120, 220, 305]
    pos = {}
    for x, capa in zip(xs, capas):
        paso = (alto - 20) / (len(capa) + 1)
        for i, c in enumerate(capa):
            pos[c] = (x, 20 + paso * (i + 1))

    def grupo(c):
        return next((g for g, ents in demo.GRUPOS.items() if c in ents), c)

    formas = [cv.Text(x, 8, t, ft.TextStyle(size=10, color=ui.GRIS),
                      alignment=ft.Alignment.CENTER)
              for x, t in zip(xs, ["Entradas", "Intermedios", "Factores", "Decisión"])]
    for d, origenes in demo.ESTRUCTURA.items():
        for o in origenes:
            formas.append(cv.Line(*pos[o], *pos[d], paint=ft.Paint(
                color=ft.Colors.with_opacity(0.45, COLOR_GRUPO.get(grupo(o), "#9fb3b3")),
                stroke_width=1.4)))
    for c, (x, y) in pos.items():
        relleno = ui.TEXTO if c == 28 else COLOR_GRUPO.get(grupo(c), ui.TEAL)
        formas += [cv.Circle(x, y, 18 if c == 28 else 13, paint=ft.Paint(color=relleno)),
                   cv.Text(x, y, f"C{c}", ft.TextStyle(size=9.5, color=ft.Colors.WHITE,
                                                      weight=ft.FontWeight.BOLD),
                           alignment=ft.Alignment.CENTER)]
    return ft.Row([cv.Canvas(formas, width=ancho, height=alto)],
                  alignment=ft.MainAxisAlignment.CENTER)


def pagina_modelo(app):
    leyenda = ft.Row([
        ft.Row([ft.Container(width=10, height=10, border_radius=5, bgcolor=c), ui.sub(t)],
               spacing=4)
        for t, c in [("Paciente", ui.TEAL), ("Médicos", "#5b47b5"), ("Tecnológicos", ui.AMBAR),
                     ("Familiares", ui.VERDE)]], wrap=True, spacing=10)
    estructura = ui.tarjeta([
        _diagrama(), leyenda,
        ui.sub("28 conceptos. Las entradas vienen de los cuestionarios, el pastillero y el "
               "expediente; C28 decide si la adherencia es Mala, Regular o Buena."),
    ], "Estructura del mapa")

    # Simulador: los deslizadores actualizan el resultado sin redibujar la pantalla.
    resultado = ft.Container()
    valores = {c: 0.6 for c in (24, 25, 26, 27)}

    def pintar_resultado():
        c28 = demo.estimar_c28(*valores.values())
        et = demo.etiqueta(c28)
        resultado.content = ui.tarjeta(ft.Row([
            ui.anillo(c28, f"{c28:.3f}", "C28", ui.COLOR_ETIQUETA[et],
                      carita=ui.CARITA_ETIQUETA[et]),
            ft.Column([ui.texto(f"Adherencia: {et}", 16, negrita=True),
                       ui.sub("Malo < 0.318 ≤ Regular < 0.6446 ≤ Bueno")], expand=True),
        ], spacing=16))

    def deslizador(c):
        valor = ui.texto(f"{valores[c]:.2f}", 14, negrita=True)

        def al_mover(e):
            valores[c] = round(e.control.value, 2)
            valor.value = f"{valores[c]:.2f}"
            pintar_resultado()
            app.page.update()

        return ft.Column([
            ft.Row([ft.Container(ui.texto(f"C{c} · {demo.CONCEPTOS[c]}", 14), expand=True), valor]),
            ft.Slider(value=valores[c], min=0, max=1, divisions=20, on_change=al_mover),
        ], spacing=0)

    pintar_resultado()
    simulador = ui.tarjeta([
        ui.sub("Mueve los factores para ver cómo cambia la clasificación (fórmula de etiquetas: "
               "C28 = 0.25 · (C24 + C25 + C26 + C27))."),
        *[deslizador(c) for c in (24, 25, 26, 27)],
    ], "Simulador de C28")

    inferencia = ft.Container(ft.ExpansionTile(
        title="¿Cómo infiere el mapa?", controls_padding=16,
        shape=ft.RoundedRectangleBorder(radius=16),
        collapsed_shape=ft.RoundedRectangleBorder(radius=16),
        controls=[ft.Markdown(
            "- Regla de Kosko con memoria, actualización síncrona:  \n"
            "  **Aᵢ(t+1) = tanh( Σⱼ wⱼᵢ·Aⱼ(t) + Aᵢ(t) )**\n"
            "- Se detiene cuando el cambio máximo es menor que 0.001 o tras ~100 iteraciones.\n"
            "- Los pesos wⱼᵢ se aprenden con PSO (optimización por enjambre de partículas).")]),
        bgcolor=ft.Colors.WHITE, border=ft.Border.all(1, ui.BORDE), border_radius=16)

    entrenamiento = ui.tarjeta([
        ui.fila(ui.sub("Precisión actual (FCM Expert)"), "65–70%"),
        ui.fila(ui.sub("IC 95% (réplica en Python, t de Student)"), "56.5–66.9%"),
        ui.fila(ui.sub("Meta"), "≈ 95%"),
        ui.fila(ui.sub("Estado"), ui.chip("En ajuste", "warn"), divisor=False),
    ], "Estado del entrenamiento")

    return [ui.titulo("Modelo FCM", "Cómo se calcula la adherencia de cada paciente."),
            estructura, simulador, resultado, inferencia, entrenamiento]
