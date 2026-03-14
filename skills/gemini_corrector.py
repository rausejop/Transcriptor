import g4f

def correct_transcript(text):
    """
    Corrige el texto de la transcripción usando Google Gemini (vía g4f).
    Se enfoca en puntuación, ortografía y coherencia sin cambiar el sentido original.
    """
    if not text:
        return ""
    
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
        # Intentamos usar el proveedor de Gemini
        response = g4f.ChatCompletion.create(
            model=g4f.models.gemini,
            messages=[{"role": "user", "content": prompt}],
        )
        return response
    except Exception as e:
        # Fallback simple o error descriptivo
        try:
            # Reintento con modelo base de g4f si falla el específico de Gemini
            response = g4f.ChatCompletion.create(
                model=g4f.models.default, # Usamos el modelo por defecto del proveedor disponible
                messages=[{"role": "user", "content": prompt}],
            )
            return response
        except Exception as e2:
            raise Exception(f"No se pudo completar la corrección IA: {str(e2)}")
