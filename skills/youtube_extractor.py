import re
import os
import tempfile
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import whisper

def extract_video_id(url):
    """
    Extrae el ID del video de una URL de YouTube.
    """
    regex = r"(?:v=|\/|embed\/|youtu.be\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def get_video_info(url):
    """
    Obtiene metadatos del video usando yt-dlp.
    """
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Video de YouTube'),
                'duration': info.get('duration', 0)
            }
    except Exception:
        return {'title': "Video de YouTube", 'duration': 0}

def download_audio(url, progress_callback=None):
    """
    Descarga el audio del video con hook de progreso.
    """
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, 'yt_audio.%(ext)s')
    
    def ydl_hook(d):
        if d['status'] == 'downloading' and progress_callback:
            try:
                # Extraemos datos numéricos para mayor precisión
                p = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1)
                eta = d.get('eta', 0)
                speed = d.get('speed', 0) # bytes/seg
                
                progress_callback({
                    'percent': p,
                    'eta': eta,
                    'speed': speed
                })
            except: pass

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [ydl_hook],
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

def transcribe_with_whisper(audio_path):
    """
    Transcribe el audio optimizado para CPU (sin FP16).
    """
    try:
        # Usamos fp16=False para evitar warnings en CPU
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, fp16=False)
        return result["text"].strip()
    except Exception as e:
        raise Exception(f"Error en ASR (Whisper): {str(e)}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

def get_transcript(url, video_id, languages=['es', 'en'], progress_bar=None, status_placeholder=None):
    """
    Motor de extracción con soporte para callbacks de progreso en UI.
    """
    # INTENTO 1: Subtítulos oficiales
    if status_placeholder: status_placeholder.info("🔍 Buscando subtítulos oficiales...")
    try:
        data = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return " ".join([segment['text'] for segment in data]), "Oficial"
    except Exception:
        pass

    # INTENTO 2: Cualquier subtítulo
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for t in transcript_list:
            return " ".join([segment['text'] for segment in t.fetch()]), "Auto-generado"
    except Exception:
        pass

    # INTENTO 3: ASR con Whisper
    if status_placeholder: status_placeholder.warning("⚠️ No hay subtítulos. Iniciando ASR con Whisper...")
    try:
        # Callback para la descarga (ahora recibe un diccionario)
        def update_download(data):
            if progress_bar and status_placeholder: 
                p = data['percent']
                eta = data['eta']
                speed_mb = data['speed'] / 1024 / 1024 if data['speed'] else 0
                
                eta_str = f"{eta}s" if eta else "--"
                text = f"📥 Descargando audio | ETA: {eta_str} | Velocidad: {speed_mb:.2f} MB/s"
                progress_bar.progress(p, text=text)

        audio_file = download_audio(url, progress_callback=update_download)
        
        if progress_bar and status_placeholder: 
            progress_bar.progress(1.0, text="⚙️ Transcribiendo audio...")
            status_placeholder.info("🎙️ Whisper está procesando el audio. Por favor, espera.")
            
        text = transcribe_with_whisper(audio_file)
        return text, "ASR (Whisper)"
    except Exception as e:
        raise Exception(f"ASR Falló: {str(e)}")
