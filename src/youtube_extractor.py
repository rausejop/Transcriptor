import re
import os
import tempfile
import asyncio
from typing import Dict, List, Optional, Tuple, Callable
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from loguru import logger
import yt_dlp
from yt_dlp import YoutubeDL
import whisper

# Módulo de extracción multimedia y procesamiento ASR especializado para YouTube.

def extract_video_id(url: str) -> Optional[str]:
    """Extrae el ID del video de una URL de YouTube."""
    # Expresión regular para capturar el identificador único de 11 caracteres.
    regex = r"(?:v=|\/|embed\/|youtu.be\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    logger.debug(f"ID no encontrado para URL: {url}")
    return None

def get_video_info(url: str) -> Dict[str, any]:
    """Obtiene metadatos del video usando yt-dlp."""
    try:
        # Configuración silenciosa para la extracción rápida de metadatos.
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Video de YouTube'),
                'duration': info.get('duration', 0)
            }
    except Exception as e:
        logger.error(f"Fallo recuperando info de video {url}: {str(e)}")
        return {'title': "Video de YouTube", 'duration': 0}

def download_audio(url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> Path:
    """Descarga el audio del video con hook de progreso."""
    temp_dir = Path(tempfile.gettempdir())
    # Genera una ruta única usando el PID para evitar colisiones en procesos paralelos.
    target_file = temp_dir / f"yt_audio_{os.getpid()}_{id(url)}.%(ext)s"
    logger.info(f"Iniciando descarga de audio para: {url}")

    # Hook interno para reportar el progreso de la descarga a la interfaz.
    def ydl_hook(d: Dict) -> None:
        if d['status'] == 'downloading' and progress_callback:
            try:
                p = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1)
                eta = d.get('eta', 0)
                speed = d.get('speed', 0)
                progress_callback({
                    'percent': p,
                    'eta': eta,
                    'speed': speed
                })
            except Exception as hook_err:
                logger.debug(f"Error en hook de progreso: {str(hook_err)}")

    # Opciones de post-procesamiento para convertir a MP3 de alta calidad.
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(target_file),
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
        final_path = Path(ydl.prepare_filename(info)).with_suffix('.mp3')
        logger.debug(f"Audio descargado satisfactoriamente en: {final_path}")
        return final_path

def transcribe_with_whisper(audio_path: Path) -> str:
    """Transcribe el audio optimizado para CPU (sin FP16)."""
    logger.info(f"Cargando motor de IA Whisper para transcribir: {audio_path.name}")
    try:
        # Carga del modelo base y ejecución de la inferencia local.
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path), fp16=False)
        logger.success("Transcripción Whisper finalizada exitosamente.")
        return result["text"].strip()
    except Exception as e:
        logger.error(f"Fallo crítico en motor Whisper: {str(e)}")
        raise Exception(f"ASR Local Falló: {str(e)}")
    finally:
        # Higiene del sistema de archivos mediante eliminación proactiva del audio temporal.
        if audio_path.exists():
            try:
                os.remove(str(audio_path))
            except: pass
            logger.debug(f"Higiene de archivos temporales completada para: {audio_path}")

def get_transcript(url: str, video_id: str, languages: List[str] = ['es', 'en'], progress_bar: any = None, status_placeholder: any = None) -> Tuple[str, str]:
    """Motor de extracción jerárquico con soporte para feedback visual en tiempo real."""
    logger.info(f"Iniciando proceso de obtención de texto para video ID: {video_id}")
    
    # Capa de compatibilidad para YouTubeTranscriptApi (Versión 1.2.4+ vs clásicas).
    # Se instancia la API para soportar versiones que requieren métodos de instancia.
    api = YouTubeTranscriptApi()

    # INTENTO 1: Búsqueda de subtítulos oficiales remotos.
    try:
        if status_placeholder: status_placeholder.info("🔍 Buscando subtítulos oficiales en YouTube...")
    except: pass
    
    try:
        # Intento de llamada estática (versión clásica) o de instancia (versión 1.2.4).
        try:
            data = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        except AttributeError:
            data = api.fetch(video_id, languages=languages)
        
        # Procesamiento de los datos obtenidos (soporta lista de dicts o FetchedTranscript).
        text = " ".join([segment['text'] if isinstance(segment, dict) else segment.text for segment in data])
        logger.debug("Subtítulos oficiales localizados y descargados con éxito.")
        return text, "Oficial"
    except Exception as e1:
        logger.info(f"Subtítulos oficiales ausentes o error de API: {str(e1)}")
        pass

    # INTENTO 2: Búsqueda de cualquier pista disponible (incluyendo automáticas).
    try:
        # Detección dinámica de list_transcripts (estático) o list (instancia).
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except AttributeError:
            transcript_list = api.list(video_id)
            
        for t in transcript_list:
            logger.debug(f"Utilizando fuente de texto auto-generada por servidor: {t.language}")
            # El método fetch() retorna el contenido de la transcripción.
            data = t.fetch()
            text = " ".join([segment['text'] if isinstance(segment, dict) else segment.text for segment in data])
            return text, "Auto-generado"
    except Exception as e2:
        logger.warning(f"Búsqueda en la nube agotada sin éxito: {str(e2)}")
        pass

    # INTENTO 3: Procesamiento local con IA Whisper (Fallback definitivo).
    try:
        if status_placeholder: status_placeholder.warning("⚠️ No se encontraron subtítulos en la nube. Iniciando procesamiento local con Whisper...")
    except: pass
    
    logger.info("Activando pipeline de emergencia ASR (Whisper) para regenerar el texto desde el audio.")
    try:
        # Función interna para actualizar la UI durante el monitoreo de descarga de audio.
        def update_download(data: Dict) -> None:
            if progress_bar:
                p = data['percent']
                eta = data['eta']
                speed_mb = data['speed'] / 1024 / 1024 if data['speed'] else 0
                eta_str = f"{int(eta)}s" if eta else "--"
                text = f"📥 Operación: Descarga de Audio | Tiempo estimado: {eta_str} | Vel: {speed_mb:.2f} MB/s"
                try:
                    progress_bar.progress(p, text=text)
                except: pass

        audio_file = download_audio(url, progress_callback=update_download)
        
        # Notificación de inicio de la fase de transcripción pesada tras la descarga.
        try:
            if progress_bar: progress_bar.progress(1.0, text="⚙️ Fase final: Transcribiendo audio con IA...")
            if status_placeholder: status_placeholder.info("🎙️ Whisper está analizando el audio localmente. Por favor, mantén la pestaña abierta.")
        except: pass
        
        text = transcribe_with_whisper(audio_file)
        return text, "ASR (Whisper)"
    except Exception as e3:
        logger.critical(f"Pipeline local ASR falló catastróficamente: {str(e3)}")
        raise Exception(f"Fase ASR local falló críticamente: {str(e3)}")
