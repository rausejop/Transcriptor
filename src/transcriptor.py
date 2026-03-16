import asyncio
import sys
import streamlit as st
from pathlib import Path
from loguru import logger
import traceback

# Configuración de importaciones dinámicas para compatibilidad de versiones de Streamlit.
try:
    from streamlit.runtime.scriptrunner import get_script_run_context, add_script_run_context
except ImportError:
    try:
        from streamlit.runtime.script_run_context import get_script_run_context, add_script_run_context
    except ImportError:
        try:
            from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx as get_script_run_context, add_script_run_ctx as add_script_run_context
        except ImportError:
            from streamlit.scriptrunner import get_script_run_context, add_script_run_context

# Importación de módulos de lógica de negocio y exportación.
from youtube_extractor import extract_video_id, get_video_info, get_transcript
from exporters import to_txt, to_json, to_csv
from gemini_corrector import correct_transcript

# Configuración de Logging Estructurado (Cumplimiento SDLC REQ2.01.13).
logger.remove()
logger.add(sys.stderr, format="{time} | {level} | {message}", level="DEBUG", serialize=True)

# Configuración global de la página y estética visual premium.
st.set_page_config(
    page_title="Transcriptor Premium | CONFIANZA23",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de estilos CSS3 personalizados para identidad corporativa.
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0b0d17 0%, #1c2033 100%);
        color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #3b82f6 !important;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #00d2ff, #3a7bd5);
    }
    h1 {
        background: linear-gradient(to right, #00d2ff, #eaafc8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Construcción de la barra lateral con controles de usuario.
with st.sidebar:
    st.image("images/Logo_CONFIANZA23.png", width=200)
    st.divider()
    st.markdown("### 🛠️ Configuración")
    url = st.text_input("URL de YouTube:", placeholder="https://www.youtube.com/watch?v=...")
    start_btn = st.button("🚀 Iniciar Transcripción")
    st.divider()
    st.markdown("### 👨‍💻 Info\nDesarrollado bajo estándar **Secure SDLC v15** por CONFIANZA23.")

# Encabezado principal del área de trabajo.
st.markdown("<h1>🎙️ Transcriptor.app</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #7f8c8d; margin-bottom: 2rem;'>Transcripción con IA + Corrección Gemini (Gratis)</p>", unsafe_allow_html=True)

# Organización del contenido en columnas centradas.
col_l, col_c, col_r = st.columns([1, 4, 1])

with col_c:
    # Lógica de procesamiento al activar el inicio de la transcripción.
    if start_btn:
        logger.info(f"Usuario ha iniciado una nueva solicitud para la URL: {url}")
        if url:
            video_id = extract_video_id(url)
            if video_id:
                logger.debug(f"Identificador de video extraído: {video_id}")
                progress_bar = st.progress(0, text="🔍 Fase 1: Analizando video y metadatos remotos...")
                status_text = st.empty()
                
                try:
                    # Captura del contexto de Streamlit para inyección en hilos secundarios (Thread Safety).
                    ctx = get_script_run_context()
                    logger.debug(f"Contexto de Streamlit capturado: {ctx}")
                    
                    async def process_workflow():
                        # Wrapper para mantener el contexto de Streamlit en hilos asíncronos.
                        def run_with_context(func, *args, **kwargs):
                            if ctx:
                                try:
                                    add_script_run_context(ctx)
                                except Exception as ctx_err:
                                    logger.warning(f"No se pudo inyectar el contexto de Streamlit: {ctx_err}")
                            return func(*args, **kwargs)

                        # Fase de obtención de metadatos del video.
                        info_data = await asyncio.to_thread(run_with_context, get_video_info, url)
                        st.markdown(f"### 📺 {info_data['title']}")
                        if info_data['duration'] > 0:
                            st.caption(f"⏱️ Duración total detectada: {info_data['duration'] // 60}m {info_data['duration'] % 60}s")
                        
                        # Fase de obtención jerárquica de la transcripción.
                        transcript, method = await asyncio.to_thread(run_with_context, get_transcript, url, video_id, progress_bar=progress_bar, status_placeholder=status_text)
                        logger.info(f"Tarea de transcripción finalizada mediante el método: {method}")
                        return transcript, info_data, method

                    # Ejecución del flujo de trabajo asíncrono y almacenamiento de resultados.
                    res_transcript, res_info, res_method = asyncio.run(process_workflow())
                    st.session_state['transcript'] = res_transcript
                    st.session_state['video_id'] = video_id
                    st.session_state['title'] = res_info['title']
                    st.session_state['method'] = res_method
                    
                    # Limpieza de estados previos de corrección IA.
                    if 'corrected_transcript' in st.session_state:
                        del st.session_state['corrected_transcript']
                    
                    # Feedback visual de éxito al usuario.
                    progress_bar.progress(1.0, text="✅ Transcripción lista para revisión")
                    status_text.success("🎉 ¡Pipeline de transcripción finalizado exitosamente!")
                    st.balloons()
                    
                except Exception as e:
                    # Gestión robusta de errores con traza completa para diagnóstico.
                    full_error = traceback.format_exc()
                    logger.error(f"Fallo crítico en el pipeline:\n{full_error}")
                    error_msg = str(e) if str(e) else "Error interno de inicialización o pérdida de contexto de hilo."
                    st.error(f"❌ Error detallado: {error_msg}")
            else:
                logger.warning(f"URL no reconocida: {url}")
                st.error("❌ El enlace proporcionado no parece corresponder a un video de YouTube válido.")
        else:
            st.warning("⚠️ Por favor, introduce una dirección URL de YouTube.")

# Visualización y herramientas de post-procesado para transcripciones existentes.
if 'transcript' in st.session_state:
    st.divider()
    t_orig = st.session_state['transcript']
    v_id = st.session_state['video_id']
    title = st.session_state['title']
    
    # Navegación por pestañas entre versiones originales y mejoradas por IA.
    tab1, tab2 = st.tabs(["📝 Transcripción Original", "✨ Versión Corregida (Google Gemini)"])
    
    with tab1:
        st.info(f"Metodología de obtención aplicada: {st.session_state.get('method', 'Desconocido')}")
        st.text_area("Texto Original en Bruto", t_orig, height=400, key="orig_area")
        
        # Bloque de herramientas de exportación multiformato.
        st.subheader("📥 Exportar Transcripción Original")
        c1, c2, c3 = st.columns(3)
        c1.download_button("📄 Archivo TXT", to_txt(t_orig), f"transcripcion_original_{v_id}.txt", mime="text/plain")
        c2.download_button("📦 Formato JSON", to_json(t_orig, v_id, title), f"transcripcion_original_{v_id}.json", mime="application/json")
        c3.download_button("📊 Datos CSV", to_csv(t_orig, v_id, title), f"transcripcion_original_{v_id}.csv", mime="text/csv")
        
    with tab2:
        # Lógica para disparar la mejora lingüística a través de Google Gemini.
        if 'corrected_transcript' not in st.session_state:
            st.warning("Pulsa el botón inferior para mejorar la legibilidad y puntuación del texto mediante IA.")
            if st.button("🪄 Ejecutar Mejora con Google Gemini"):
                logger.info(f"Iniciando refinamiento Gemini para: {v_id}")
                with st.spinner("🤖 Refinando transcripción con IA..."):
                    try:
                        corrected = asyncio.run(correct_transcript(t_orig))
                        st.session_state['corrected_transcript'] = corrected
                        st.rerun()
                    except Exception as e_corr:
                        logger.error(f"Error en refinamiento IA: {str(e_corr)}")
                        st.error(f"Error en la mejora inteligente: {str(e_corr)}")
        else:
            # Presentación y exportación de la versión refinada por IA.
            t_corr = st.session_state['corrected_transcript']
            st.success("Transcripción optimizada lingüísticamente por Google Gemini")
            st.text_area("Texto Refinado por IA", t_corr, height=400, key="corr_area")
            
            st.subheader("📥 Exportar Transcripción Refinada")
            cc1, cc2, cc3 = st.columns(3)
            cc1.download_button("📄 Archivo TXT", to_txt(t_corr), f"transcripcion_refinada_{v_id}.txt", mime="text/plain")
            cc2.download_button("📦 Formato JSON", to_json(t_corr, v_id, title), f"transcripcion_refinada_{v_id}.json", mime="application/json")
            cc3.download_button("📊 Datos CSV", to_csv(t_corr, v_id, title), f"transcripcion_refinada_{v_id}.csv", mime="text/csv")

# Pie de página institucional y tecnológico.
st.markdown("<br><hr><p style='text-align: center; color: #444; font-size: 0.7em;'>Google Gemini IA | OpenAI Whisper Base ASR | Secure SDLC v15 | Confianza23 Lab (Professional Edition)</p>", unsafe_allow_html=True)
