"""Instrumentos de medición: preguntas y cálculo puntaje → nivel → valor FCM.

Los rangos y valores salen de Instrumentos.docx. Donde el documento no define
la regla de puntaje (hábitos, efectos secundarios, índice socioeconómico) se
usa una propuesta marcada como PROPUESTA para que se pueda ajustar.
"""
from dataclasses import dataclass, field
from statistics import mean


@dataclass
class Resultado:
    instrumento: str
    codigo: str          # código del factor según Instrumentos.docx
    puntaje: float
    nivel: str
    valor_fcm: float
    alertas: list = field(default_factory=list)
    detalle: dict = field(default_factory=dict)


# ---------------------------------------------------------------- C1 Motivación
LIKERT_ACUERDO = {
    1: "Totalmente en desacuerdo",
    2: "En desacuerdo",
    3: "Ni de acuerdo ni en desacuerdo",
    4: "De acuerdo",
    5: "Totalmente de acuerdo",
}

MOTIVACION_ITEMS = [
    "Estoy convencido(a) de que mi tratamiento mejorará mi salud.",
    "Confío en que las indicaciones de mi médico son las adecuadas para mi caso.",
    "Me siento capaz de seguir el tratamiento tal como se me indica.",
    "Aunque el tratamiento me resulte incómodo, considero que vale la pena continuarlo.",
    "Tengo la disposición de mantener el tratamiento durante el tiempo que sea necesario.",
]


def calcular_motivacion(respuestas):
    prom = mean(respuestas)
    if prom >= 4.0:
        nivel, valor = "Alto", 0.90
    elif prom >= 2.5:
        nivel, valor = "Medio", 0.55
    else:
        nivel, valor = "Bajo", 0.20
    return Resultado("Motivación y actitud", "C1", round(prom, 2), nivel, valor)


# ------------------------------------------------------- C3 Salud mental (PHQ-9 / GAD-7)
# Fraseo oficial (Spanish for Mexico). No parafrasear.
PHQ9_INSTRUCCION = ("Durante las últimas 2 semanas, ¿qué tan seguido le han afectado "
                    "cualquiera de los siguientes problemas?")
PHQ9_OPCIONES = {0: "Para nada", 1: "Varios días", 2: "Más de la mitad de los días",
                 3: "Casi todos los días"}
PHQ9_ITEMS = [
    "Poco interés o placer en hacer las cosas",
    "Se ha sentido decaído(a), deprimido(a), o sin esperanzas",
    "Dificultad para dormir o permanecer dormido(a), o ha dormido demasiado",
    "Se ha sentido cansado(a) o con poca energía",
    "Con poco apetito o ha comido en exceso",
    "Se ha sentido mal con usted mismo(a) – o que es un fracaso o que ha quedado mal "
    "con usted mismo(a) o con su familia",
    "Ha tenido dificultad para concentrarse en cosas tales como leer el periódico o ver televisión",
    "¿Se ha estado moviendo o hablando tan lento que otras personas podrían notarlo?, o por "
    "el contrario – ha estado tan inquieto(a) o agitado(a), que se ha estado moviendo mucho "
    "más de lo normal",
    "Ha pensado que estaría mejor muerto(a) o se le ha ocurrido lastimarse de alguna manera",
]

GAD7_INSTRUCCION = ("Durante las últimas 2 semanas, ¿con qué frecuencia ha sentido molestias "
                    "por los siguientes problemas?")
GAD7_OPCIONES = {0: "Nunca", 1: "Varios días", 2: "Más de la mitad de los días",
                 3: "Casi todos los días"}
GAD7_ITEMS = [
    "Sentirse nervioso/a, intranquilo/a o con los nervios de punta",
    "No poder dejar de preocuparse o no poder controlar la preocupación",
    "Preocuparse demasiado por diferentes cosas",
    "Dificultad para relajarse",
    "Estar tan inquieto/a que es difícil permanecer sentado/a tranquilamente",
    "Molestarse o ponerse irritable fácilmente",
    "Sentir miedo como si algo terrible pudiera pasar",
]

_RIESGO = [("Bajo riesgo", 0.30), ("Riesgo moderado", 0.70), ("Riesgo alto", 0.85)]


def _riesgo(total):
    return 0 if total <= 9 else 1 if total <= 14 else 2


def calcular_salud_mental(phq9, gad7):
    phq_total, gad_total = sum(phq9), sum(gad7)
    # Se toma el mayor riesgo de las dos escalas.
    nivel, valor = _RIESGO[max(_riesgo(phq_total), _riesgo(gad_total))]
    alertas = []
    if phq9[8] > 0:
        alertas.append("ALERTA INMEDIATA: respuesta positiva en el ítem 9 del PHQ-9 "
                       "(ideación autolesiva). Notificar al personal de salud.")
    return Resultado("Salud mental (PHQ-9 / GAD-7)", "C3", max(phq_total, gad_total),
                     nivel, valor, alertas, {"PHQ-9": phq_total, "GAD-7": gad_total})


# ----------------------------------------------------------------- C4 Olvido
def calcular_olvido(olvidos_semana):
    if olvidos_semana <= 1:
        nivel, valor = "Bajo", 0.20
    elif olvidos_semana <= 4:
        nivel, valor = "Medio", 0.60
    else:
        nivel, valor = "Alto", 0.90
    return Resultado("Olvido", "C4", olvidos_semana, nivel, valor)


# ------------------------------------------------------------ C5 Hábitos
# PROPUESTA: 5 preguntas de 0–20 puntos cada una (total 0–100).
HABITOS_ITEMS = {
    "¿Cuántos días a la semana realiza actividad física de al menos 20 minutos?": {
        "Ninguno": 0, "1 a 2 días": 8, "3 a 4 días": 15, "5 o más días": 20},
    "¿Cuántas horas duerme en promedio por noche?": {
        "Menos de 5 horas": 0, "5 a 6 horas": 10, "7 a 9 horas": 20, "Más de 9 horas": 10},
    "¿Con qué frecuencia consume bebidas alcohólicas?": {
        "Nunca": 20, "Una vez al mes o menos": 15, "2 a 4 veces al mes": 10,
        "2 a 3 veces por semana": 5, "4 o más veces por semana": 0},
    "¿Fuma actualmente?": {
        "No": 20, "Ocasionalmente": 10, "Diariamente": 0},
    "¿Con qué frecuencia consume alimentos altos en azúcar o grasas?": {
        "Rara vez o nunca": 20, "1 a 2 veces por semana": 15, "3 a 5 veces por semana": 8,
        "Diariamente": 0},
}


def calcular_habitos(puntos):
    total = sum(puntos)
    nivel = "Saludable" if total >= 70 else "Moderado" if total >= 40 else "No saludable"
    return Resultado("Hábitos y estilo de vida", "C5", total, nivel, round(total / 100, 3))


# ----------------------------------------------------- C7 Efectos secundarios
EFECTOS_SINTOMAS = ["Náuseas", "Mareo", "Dolor", "Vómito", "Somnolencia"]
EFECTOS_INTENSIDAD = {0: "No lo tuve", 1: "1 · Muy leve", 2: "2 · Leve", 3: "3 · Moderado",
                      4: "4 · Fuerte", 5: "5 · Muy fuerte"}


def calcular_efectos(intensidades, interfiere_rutina):
    # PROPUESTA: promedio de intensidad de los síntomas presentes.
    presentes = [i for i in intensidades if i > 0]
    prom = mean(presentes) if presentes else 0
    if interfiere_rutina or prom >= 4 or (presentes and max(presentes) == 5):
        nivel, valor = "Graves", 0.90
    elif prom >= 3:
        nivel, valor = "Moderados", 0.55
    else:
        nivel, valor = "Leves", 0.20
    alertas = []
    if nivel == "Graves":
        alertas.append("Efectos secundarios graves: remitir a valoración médica.")
    return Resultado("Efectos secundarios", "C7", round(prom, 2), nivel, valor, alertas)


# ------------------------------------------------------- C9 Apoyo familiar
LIKERT_FRECUENCIA = {1: "Nunca", 2: "Casi nunca", 3: "A veces", 4: "Casi siempre", 5: "Siempre"}

APOYO_ITEMS = [
    "¿Algún familiar le recuerda tomar su medicamento?",
    "¿Algún familiar lo acompaña a sus consultas médicas?",
    "¿Recibe apoyo emocional de su familia respecto a su tratamiento?",
    "¿Su familia muestra interés en su proceso de recuperación?",
]


def calcular_apoyo(respuestas, sin_familia=False):
    if sin_familia:
        # Sin red familiar se registra el mínimo de la escala (1/5).
        respuestas = [1] * len(APOYO_ITEMS)
    prom = mean(respuestas)
    nivel = "Alto" if prom >= 4.0 else "Medio" if prom >= 2.5 else "Bajo"
    return Resultado("Apoyo familiar", "C9", round(prom, 2), nivel, round(prom / 5, 3),
                     detalle={"sin_familia": sin_familia})


# ---------------------------------------------------- C14 Seguimiento médico
def calcular_seguimiento(programadas, asistidas):
    pct = 100 * asistidas / programadas
    nivel = "Alto" if pct >= 80 else "Medio" if pct >= 50 else "Bajo"
    return Resultado("Seguimiento médico", "C14", round(pct, 1), nivel, round(pct / 100, 3))


# ------------------------------------------------------- C16 Carga económica
def calcular_carga(ingreso, costo):
    pct = 100 * costo / ingreso
    nivel = "Baja carga" if pct < 10 else "Media" if pct <= 30 else "Alta carga"
    return Resultado("Carga económica", "C16", round(pct, 1), nivel,
                     round(max(0.0, 1 - pct / 100), 3))


# ----------------------------------------------- C17 Situación socioeconómica
# PROPUESTA de índice 0–100.
SOCIO_ITEMS = {
    "Nivel educativo": {
        "Sin estudios": 0, "Primaria": 5, "Secundaria": 10, "Preparatoria o técnico": 15,
        "Licenciatura o más": 20},
    "Tipo de empleo": {
        "Sin empleo": 0, "Empleo informal o por cuenta propia": 10,
        "Jubilado(a) o pensionado(a)": 15, "Empleo formal": 20},
    "Cobertura de seguro médico": {
        "Ninguna": 0, "Pública (IMSS, ISSSTE, IMSS-Bienestar u otra)": 20, "Privada": 20},
    "Número de dependientes económicos": {
        "Ninguno": 15, "1 a 2": 10, "3 a 4": 5, "5 o más": 0},
    "Ingreso mensual aproximado": {
        "Menos de $5,000": 0, "$5,000 a $10,000": 8, "$10,001 a $20,000": 15,
        "$20,001 a $40,000": 20, "Más de $40,000": 25},
}


def rango_ingreso(ingreso):
    """Convierte un ingreso numérico al rango usado en el índice socioeconómico."""
    if ingreso < 5000:
        return "Menos de $5,000"
    if ingreso <= 10000:
        return "$5,000 a $10,000"
    if ingreso <= 20000:
        return "$10,001 a $20,000"
    if ingreso <= 40000:
        return "$20,001 a $40,000"
    return "Más de $40,000"


def calcular_socioeconomico(puntos):
    indice = sum(puntos)
    nivel = "Alta" if indice >= 70 else "Media" if indice >= 40 else "Baja"
    return Resultado("Situación socioeconómica", "C17", indice, nivel, round(indice / 100, 3))
