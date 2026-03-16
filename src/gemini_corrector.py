import g4f
import asyncio
from loguru import logger

# Módulo de refinamiento lingüístico mediante Inteligencia Artificial (Google Gemini).

async def correct_transcript(text: str) -> str:
    """
    Corrige el texto de la transcripción usando Google Gemini (vía g4f).
    Se enfoca en puntuación, ortografía y coherencia sin cambiar el sentido original.
    """
    # Validación proactiva del contenido para evitar llamadas innecesarias a la IA.
    if not text:
        logger.warning("Se intentó corregir una transcripción vacía.")
        return ""

    logger.info(f"Iniciando corrección IA para texto de {len(text)} caracteres.")

    # Construcción de la instrucción experta (prompt) para guiar el comportamiento del modelo.
    prompt = (
        "Actúa como un corrector de estilo experto. A continuación te presento una transcripción "
        "en bruto de un video de YouTube. Tu tarea es corregirla para que sea legible, "
        "añadiendo puntuación adecuada (comas, puntos), corrigiendo errores ortográficos "
        "y mejorando la coherencia de las frases, pero MANTENIENDO el sentido original y "
        "las palabras clave. No añadidas conclusiones ni introducciones tuyas. "
        "Sólo devuelve el texto corregido.\n\n"
        f"TEXTO A CORREGIR:\n{text}"
    )

    try:
        # Intento de corrección utilizando el modelo Gemini como opción preferente por su alta calidad técnica.
        logger.debug("Solicitando corrección al modelo Gemini...")
        response = await asyncio.to_thread(g4f.ChatCompletion.create, 
            model=g4f.models.gemini,
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("Corrección Gemini exitosa.")
        return response
    except Exception as e:
        # Protocolo de contingencia: reintento con modelo predeterminado si el preferente falla.
        logger.error(f"Fallo en modelo Gemini: {str(e)}. Intentando fallback...")
        try:
            response = await asyncio.to_thread(g4f.ChatCompletion.create,
                model=g4f.models.default, 
                messages=[{"role": "user", "content": prompt}]
            )
            logger.info("Corrección mediante modelo default exitosa.")
            return response
        except Exception as e2:
            # Reporte de error fatal si toda la infraestructura de IA es inaccesible.
            logger.critical(f"Error crítico en sistema de corrección IA: {str(e2)}")
            raise Exception(f"No se pudo completar la corrección IA: {str(e2)}")
