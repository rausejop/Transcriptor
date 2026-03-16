import json
import pandas as pd
import io

# Funciones de exportación profesional para diversos formatos de archivo estándar.

def to_txt(text: str) -> bytes:
    """Convierte el texto a formato TXT (bytes)."""
    # Codifica el texto usando UTF-8 para asegurar la compatibilidad universal.
    return text.encode('utf-8')

def to_json(text: str, video_id: str, title: str) -> bytes:
    """Convierte el texto a formato JSON (bytes)."""
    # Organiza el contenido y metadatos en un diccionario estructurado.
    data = {
        "video_id": video_id,
        "title": title,
        "transcript": text
    }
    # Serializa el objeto a JSON con indentación para mejorar la legibilidad.
    return json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')

def to_csv(text: str, video_id: str, title: str) -> bytes:
    """Convierte el texto a formato CSV (bytes)."""
    # Crea un DataFrame de pandas para estructurar los datos en formato tabular.
    df = pd.DataFrame([{
        "video_id": video_id,
        "title": title,
        "transcript": text
    }])
    # Utiliza un búfer de memoria para generar el archivo CSV sin usar el disco físico.
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    return output.getvalue()
