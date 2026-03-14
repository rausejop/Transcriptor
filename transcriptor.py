import streamlit as st
from skills.youtube_extractor import extract_video_id, get_video_info, get_transcript
from skills.exporters import to_txt, to_json, to_csv
from skills.gemini_corrector import correct_transcript

# Configuración de página
st.set_page_config(
    page_title="Transcriptor Premium + AI Gemini",
    page_icon="🎙️",
    layout="wide"
)

# Estilo Premium
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0b0d17 0%, #1c2033 100%);
        color: #ffffff;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #00d2ff, #3a7bd5);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 210, 255, 0.2);
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

# Encabezado con Logo
head_col1, head_col2 = st.columns([4, 1])
with head_col1:
    st.markdown("<h1>🎙️ Transcriptor.app</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7f8c8d; margin-bottom: 2rem;'>Transcripción con IA + Corrección Gemini (Gratis)</p>", unsafe_allow_html=True)
with head_col2:
    st.image("images/Logo_CONFIANZA23.png", width=150)

# Barra Lateral o Columna Central
col_l, col_c, col_r = st.columns([1, 2, 1])

with col_c:
    url = st.text_input("URL de YouTube:", placeholder="https://www.youtube.com/watch?v=...")
    start_btn = st.button("🚀 Iniciar Transcripción")

if start_btn:
    if url:
        video_id = extract_video_id(url)
        if video_id:
            progress_bar = st.progress(0, text="🔍 Analizando video y metadatos...")
            status_text = st.empty()
            
            try:
                with st.container():
                    info_data = get_video_info(url)
                    st.markdown(f"### 📺 {info_data['title']}")
                    
                    if info_data['duration'] > 0:
                        st.caption(f"⏱️ Duración detectada: {info_data['duration'] // 60}m {info_data['duration'] % 60}s")
                    
                    transcript, method = get_transcript(url, video_id, progress_bar=progress_bar, status_placeholder=status_text)
                    
                    st.session_state['transcript'] = transcript
                    st.session_state['video_id'] = video_id
                    st.session_state['title'] = info_data['title']
                    st.session_state['method'] = method
                    # Limpiamos corrección previa
                    if 'corrected_transcript' in st.session_state:
                        del st.session_state['corrected_transcript']
                    
                    progress_bar.progress(1.0, text="✅ Transcripción lista")
                    status_text.success("🎉 ¡Proceso completado exitosamente!")
                    st.balloons()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.error("❌ Link no válido.")
    else:
        st.warning("⚠️ Introduce una URL.")

# Resultados y Corrección
if 'transcript' in st.session_state:
    st.divider()
    
    t_orig = st.session_state['transcript']
    v_id = st.session_state['video_id']
    title = st.session_state['title']
    
    tab1, tab2 = st.tabs(["📝 Transcripción Original", "✨ Versión Corregida (Gemini)"])
    
    with tab1:
        st.info(f"Origen: {st.session_state.get('method', 'N/A')}")
        st.text_area("Original", t_orig, height=400, key="orig_area")
        
        st.subheader("📥 Descargar Original")
        c1, c2, c3 = st.columns(3)
        c1.download_button("📄 TXT", to_txt(t_orig), f"original_{v_id}.txt")
        c2.download_button("📦 JSON", to_json(t_orig, v_id, title), f"original_{v_id}.json")
        c3.download_button("📊 CSV", to_csv(t_orig, v_id, title), f"original_{v_id}.csv")

    with tab2:
        if 'corrected_transcript' not in st.session_state:
            st.warning("Pulsa el botón para mejorar la legibilidad del texto con IA.")
            if st.button("🪄 Corregir con Google Gemini"):
                with st.spinner("🤖 Gemini está analizando y corrigiendo el texto..."):
                    try:
                        corrected = correct_transcript(t_orig)
                        st.session_state['corrected_transcript'] = corrected
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en corrección: {str(e)}")
        else:
            t_corr = st.session_state['corrected_transcript']
            st.success("Texto corregido por IA Gemini")
            st.text_area("Corregido", t_corr, height=400, key="corr_area")
            
            st.subheader("📥 Descargar Corregido")
            cc1, cc2, cc3 = st.columns(3)
            cc1.download_button("📄 TXT", to_txt(t_corr), f"corregido_{v_id}.txt")
            cc2.download_button("📦 JSON", to_json(t_corr, v_id, title), f"corregido_{v_id}.json")
            cc3.download_button("📊 CSV", to_csv(t_corr, v_id, title), f"corregido_{v_id}.csv")

st.markdown("<br><hr><p style='text-align: center; color: #444; font-size: 0.7em;'>Gemini Correction Enabled | Whisper AI | Act_TSLCB_2026</p>", unsafe_allow_html=True)
