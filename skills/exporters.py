import json
import pandas as pd
import io

def to_txt(text):
    """Convierte el texto a formato TXT."""
    return text

def to_json(text, video_id, title):
    """Convierte el texto a formato JSON."""
    data = {
        "video_id": video_id,
        "title": title,
        "transcript": text
    }
    return json.dumps(data, indent=4, ensure_ascii=False)

def to_csv(text, video_id, title):
    """Convierte el texto a formato CSV."""
    df = pd.DataFrame([{
        "video_id": video_id,
        "title": title,
        "transcript": text
    }])
    # Usamos io.StringIO para retornar el string del CSV
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8')
    return output.getvalue()
