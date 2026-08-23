"""
Servicio de recomendaciones de Manejo del Estrés.
Tabla estática de 16 tarjetas (8 preguntas × 2 niveles: POBRE y MODERADO).
BUENO y EXCELENTE no reciben recomendación.

Contenido tomado de "Guía Manejo del Estrés - DILIGENCIADA" (equipo de
psicología, versión diligenciada — propuesta de contenido para revisión y
validación profesional; requiere validación del equipo de psicología antes
de publicación en producción).

Cada pregunta tiene una sola técnica: el documento fuente no distingue
técnica/objetivo por nivel, sino que ajusta el ALCANCE de la misma técnica
según el nivel ("Nivel de aplicación"). Esa distinción se traslada aquí como
el último paso de las instrucciones, en vez de inventar una técnica
separada por nivel.

La sección del documento sobre alertas por ideación de autolesión NO está
implementada: el propio documento no trae los canales reales de ayuda
(línea de atención, bienestar universitario, urgencias) y no corresponde
inventarlos.
"""
from app.models.encuesta_hplp import EncuestaHplp


def puntaje_a_nivel(valor: int) -> str:
    return {1: "POBRE", 2: "MODERADO", 3: "BUENO", 4: "EXCELENTE"}[valor]


PREGUNTAS = {
    5:  "Dormir diariamente de 7 a 9 horas por las noches.",
    11: "Apartar diariamente algún tiempo para relajarte.",
    18: "Aceptar aquellas cosas en tu vida que no puedes cambiar.",
    24: "Concentrarte en pensamientos agradables a la hora de acostarte.",
    30: "Usar métodos o técnicas específicas para controlar tu estrés.",
    36: "Mantener un equilibrio de tiempo entre tu trabajo/estudio y tus actividades de entretenimiento.",
    43: "Practicar diariamente relajación o meditación por 15 a 20 minutos.",
    48: "Mantener equilibradas tus tareas laborales/estudios para prevenir el cansancio.",
}

ITEM_FIELDS = {
    5:  "me_item_05",
    11: "me_item_11",
    18: "me_item_18",
    24: "me_item_24",
    30: "me_item_30",
    36: "me_item_36",
    43: "me_item_43",
    48: "me_item_48",
}

# Una técnica por pregunta, con un paso final distinto según POBRE/MODERADO
# (tomado de la columna "Nivel de aplicación" del documento fuente).
_REC = {
    5: {
        "tecnica": "Higiene del sueño y regularidad de horarios",
        "objetivo": "Establecer un horario de sueño estable y un entorno que favorezca dormir entre 7 y 9 horas, de modo que el descanso deje de depender de cómo estuvo el día.",
        "instrucciones_base": [
            "Define una hora fija para levantarte, incluso los fines de semana, y calcula hacia atrás la hora de acostarte para completar entre 7 y 9 horas.",
            "Crea una rutina de cierre de 30 minutos antes de dormir: baja las luces, guarda las pantallas y haz una actividad tranquila (leer, estirarte, escuchar música suave).",
            "Reserva la cama para dormir: evita estudiar, comer o ver series en ella.",
            "Evita cafeína, bebidas energizantes y comidas pesadas en las 6 horas previas a acostarte.",
            "Cada mañana registra cuántas horas dormiste y cómo te sentiste al despertar.",
        ],
        "POBRE": "Para empezar, trabaja solo el paso 1 (hora fija de levantarte) junto con el registro diario durante dos semanas, antes de sumar el resto: la meta es la regularidad, no la duración perfecta.",
        "MODERADO": "Aplica la rutina completa y concéntrate en sostener el horario también los fines de semana, que es donde suele romperse.",
    },
    11: {
        "tecnica": "Pausa diaria de recuperación con anclaje de hábito",
        "objetivo": "Instalar el hábito de reservar cada día un espacio breve y protegido para bajar la activación, aunque la jornada haya sido exigente.",
        "instrucciones_base": [
            "Elige un momento del día que ya tengas asegurado (después del almuerzo, al llegar a casa) y ancla ahí tu pausa.",
            "Empieza con 5 minutos: silencia las notificaciones y ubícate en un lugar cómodo.",
            "Respira de forma diafragmática: inhala 4 segundos por la nariz llevando el aire al abdomen y exhala 6 segundos por la boca. Repite durante toda la pausa.",
            "Al terminar, marca la pausa como cumplida y anota en una palabra cómo quedaste.",
            "Cuando completes 7 días seguidos, sube la pausa a 10 minutos.",
        ],
        "POBRE": "Mantén la pausa en 5 minutos, en un solo momento del día y con recordatorio activo: lo que se busca primero es que la pausa exista, no que sea larga ni perfecta.",
        "MODERADO": "Sostén la pausa sin recordatorio y varía su contenido (estiramiento, caminata corta, música) para que no se vuelva mecánica.",
    },
    18: {
        "tecnica": "Círculo de control e influencia con componente de aceptación",
        "objetivo": "Diferenciar lo que sí se puede modificar de lo que no, para dirigir el esfuerzo hacia lo controlable y reducir el desgaste que produce pelear con lo que no depende de uno.",
        "instrucciones_base": [
            "Escribe en frases cortas lo que hoy te preocupa.",
            "Clasifica cada preocupación en tres círculos: la controlo, la influyo, no la controlo.",
            "Para lo que controlas, define UNA acción concreta con fecha. Para lo que influyes, define qué parte sí depende de ti.",
            "Para lo que no controlas, escribe con tus palabras una frase de aceptación (por ejemplo: 'esto no depende de mí, y aun así puedo seguir con lo que me importa') y elige una acción coherente con lo que valoras.",
            "Revisa la lista una vez por semana: algunas cosas cambian de círculo con el tiempo.",
        ],
        "POBRE": "Haz un ejercicio guiado con ejemplos y trabaja una sola preocupación por sesión, para evitar la sobrecarga.",
        "MODERADO": "Haz el ejercicio completo con varias preocupaciones y una revisión semanal autónoma.",
    },
    24: {
        "tecnica": "Descarga cognitiva e imaginería agradable antes de dormir",
        "objetivo": "Reducir la activación mental al momento de acostarse y sustituir la rumiación por contenidos mentales neutros o agradables.",
        "instrucciones_base": [
            "Dos horas antes de dormir, dedica 10 minutos a escribir lo pendiente y lo que te preocupa, anotando el primer paso de cada cosa; luego cierra el cuaderno: eso quedó agendado, no resuelto ahora.",
            "Ya en la cama, elige una escena agradable, real o imaginada, en la que te hayas sentido tranquilo.",
            "Recórrela con detalle usando los sentidos: qué ves, qué escuchas, qué temperatura hace, qué olor tiene.",
            "Si aparece una preocupación, reconócela sin discutir con ella y vuelve a la escena: tener que volver muchas veces es parte del ejercicio, no una falla.",
        ],
        "POBRE": "Incluye siempre el paso de escritura previa: en este nivel la rumiación suele ser el obstáculo principal.",
        "MODERADO": "Puedes usar solo la imaginería y reservar la escritura para los días de mayor carga.",
    },
    30: {
        "tecnica": "Botiquín personal de afrontamiento",
        "objetivo": "Reconocer tus señales tempranas de estrés y tener técnicas ya elegidas para responder, en lugar de improvisar cuando ya estás desbordado.",
        "instrucciones_base": [
            "Identifica tus señales tempranas en tres niveles: cuerpo (tensión, dolor de cabeza), emoción (irritabilidad, ansiedad) y conducta (posponer, aislarte, comer de más).",
            "Arma tu botiquín con 3 a 5 técnicas que ya sepas que te sirven: respiración, caminata, música, hablar con alguien, escribir, estiramiento.",
            "Asocia cada señal con la técnica que mejor le responde: tensión física con relajación, pensamientos acelerados con escritura o caminata, sobrecarga con priorizar y pedir ayuda.",
            "Cuando aparezca una señal, aplica la técnica asociada dentro de la misma hora.",
            "Registra qué usaste y qué tan útil te resultó (0 a 10) para ir depurando el botiquín con el tiempo.",
        ],
        "POBRE": "Usa el botiquín inicial prearmado por la app y elige solo tres técnicas, para no exigirte un repertorio que todavía no tienes.",
        "MODERADO": "Construye tu botiquín de forma autónoma y ajústalo periódicamente según tu registro de utilidad.",
    },
    36: {
        "tecnica": "Agenda equilibrada por bloques",
        "objetivo": "Repartir la semana de forma que el descanso y el ocio tengan un lugar planificado, en vez de quedar como lo que sobra cuando ya no queda energía.",
        "instrucciones_base": [
            "Dibuja tu semana y marca primero lo fijo: clases, trabajo, transporte y sueño.",
            "Agenda al menos 3 bloques semanales de ocio o actividad placentera con día, hora y actividad concreta: trátalos como una cita, no como una intención.",
            "Marca un día o media jornada a la semana sin tareas académicas ni laborales.",
            "Al final de la semana revisa cuántos bloques cumpliste; si fueron menos de la mitad, reduce su duración antes que eliminarlos.",
        ],
        "POBRE": "Empieza con un solo bloque de ocio de 30 minutos y media jornada libre: la meta es que el ocio exista en la agenda, no que sea extenso.",
        "MODERADO": "Sostén tres bloques semanales y haz la revisión al cierre de semana para mantener la constancia.",
    },
    43: {
        "tecnica": "Práctica formal de relajación: relajación muscular progresiva y respiración consciente",
        "objetivo": "Desarrollar una práctica diaria de 15 a 20 minutos que entrene la capacidad de bajar el nivel de activación de forma voluntaria.",
        "instrucciones_base": [
            "Elige un horario fijo y un lugar donde no te interrumpan durante 20 minutos.",
            "Empieza con 5 minutos diarios la primera semana y aumenta 5 minutos cada semana hasta llegar a 15 o 20.",
            "En relajación muscular progresiva: tensa un grupo muscular durante 5 segundos y suéltalo durante 15, recorriendo manos, brazos, hombros, cara, abdomen, piernas y pies.",
            "En respiración consciente: lleva la atención a la respiración sin modificarla; cuando la mente se vaya, regrésala sin reprocharte.",
            "Registra la práctica y tu nivel de tensión antes y después, en una escala de 0 a 10.",
        ],
        "POBRE": "Usa el audio guiado y progresa desde 5 minutos: la prioridad es la constancia, no la duración.",
        "MODERADO": "Practica de 15 a 20 minutos, alternando técnicas y con menor dependencia del audio guiado.",
    },
    48: {
        "tecnica": "Gestión de carga y pausas programadas",
        "objetivo": "Distribuir la carga académica o laboral de forma sostenible, de manera que el cansancio no se acumule hasta volverse agotamiento.",
        "instrucciones_base": [
            "Lista tus tareas de la semana y clasifícalas por urgencia e importancia; identifica las tres que realmente mueven el resultado.",
            "Divide cada tarea grande en pasos de 25 a 45 minutos.",
            "Trabaja en bloques de 25 a 45 minutos con pausas de 5 a 10 minutos, y una pausa larga de 20 a 30 minutos cada tres bloques; en la pausa, levántate y muévete.",
            "Define una hora de cierre diaria: a partir de ahí no abres tareas nuevas.",
            "Al cerrar la semana, califica tu nivel de cansancio de 0 a 10 y ajusta la carga de la semana siguiente.",
        ],
        "POBRE": "Aplica solo las pausas programadas y la hora de cierre: la priorización se introduce después, cuando el ritmo básico ya se sostiene.",
        "MODERADO": "Aplica el esquema completo, con priorización semanal y revisión del nivel de cansancio.",
    },
}

# Clasificación de plantilla de evidencia por pregunta (misma para POBRE y
# MODERADO, ya que la técnica no cambia entre niveles en esta dimensión).
_TIPO_POR_PREGUNTA = {
    5: "registro_numerico",
    11: "registro_numerico",
    18: "matriz",
    24: "diario",
    30: "lista",
    36: "lista",
    43: "registro_numerico",
    48: "lista",
}

_CONFIG_POR_PREGUNTA = {
    5: {"unidad": "horas dormidas"},
    11: {"unidad": "minutos"},
    18: {"cuadrantes": ["Lo controlo", "Lo influyo", "No lo controlo"]},
    24: {"prompt": "Describe la escena agradable que recorriste hoy y cómo te sentiste."},
    30: {"placeholder": "Técnica que usaste hoy (respiración, caminata, música...)"},
    36: {"placeholder": "Bloque de ocio o descanso que cumpliste hoy"},
    43: {"unidad": "minutos"},
    48: {"placeholder": "Tarea prioritaria de hoy"},
}


def _tarjeta(num_q: int, nivel: str) -> dict:
    base = _REC[num_q]
    return {
        "tecnica": base["tecnica"],
        "objetivo": base["objetivo"],
        "instrucciones": [
            *base["instrucciones_base"],
            f"Para tu nivel ({nivel.capitalize()}): {base[nivel]}",
        ],
        "tipo_actividad": _TIPO_POR_PREGUNTA[num_q],
        "config_actividad": _CONFIG_POR_PREGUNTA.get(num_q),
    }


RECOMENDACIONES: dict[int, dict[str, dict]] = {
    num_q: {"POBRE": _tarjeta(num_q, "POBRE"), "MODERADO": _tarjeta(num_q, "MODERADO")}
    for num_q in _REC
}

NIVELES_CON_RECOMENDACION = {"POBRE", "MODERADO"}
PRIORIDAD_NIVEL = {"POBRE": 0, "MODERADO": 1}


def obtener_recomendaciones_me(encuesta: EncuestaHplp) -> list[dict]:
    """
    Devuelve tarjetas de recomendación de Manejo del Estrés.
    Solo para POBRE y MODERADO. Orden: POBRE → MODERADO.
    """
    tarjetas = []
    for num_q, campo in ITEM_FIELDS.items():
        valor = getattr(encuesta, campo)
        nivel = puntaje_a_nivel(valor)
        if nivel not in NIVELES_CON_RECOMENDACION:
            continue
        rec = RECOMENDACIONES[num_q][nivel]
        tarjetas.append({
            "pregunta_num": num_q,
            "pregunta_texto": PREGUNTAS[num_q],
            "nivel": nivel,
            "puntaje": valor,
            "tecnica": rec["tecnica"],
            "objetivo": rec["objetivo"],
            "instrucciones": rec["instrucciones"],
            "tipo_actividad": rec.get("tipo_actividad", "checklist_simple"),
            "config_actividad": rec.get("config_actividad"),
        })
    tarjetas.sort(key=lambda t: PRIORIDAD_NIVEL[t["nivel"]])
    return tarjetas
