# Architectural Decision Record (ADR)

## ADR ID: ADR-001
## Title: Adopción de Transcriptor.app: Streamlit + OpenAI Whisper + Gemini (g4f)
## Status: Accepted
## Date: 2026-03-15

### Context
El proyecto requiere una herramienta robusta para la extracción de transcripciones de YouTube con un motor de reserva (fallback) ante la ausencia de subtítulos oficiales. Se requiere una interfaz intuitiva, coste cero de APIs (Zero-Auth) y alta legibilidad de salida.

### Decision
Se opta por la siguiente arquitectura:
1.  **Frontend**: Streamlit por su rapidez de desarrollo y capacidad de reactividad dinámica.
2.  **ASR**: OpenAI Whisper (modelo `base`) ejecutado localmente en CPU para garantizar privacidad y coste cero.
3.  **Corrección**: Motor `g4f` (GPT4Free) con modelo Gemini para refinado semántico sin necesidad de API Keys.
4.  **Cumplimiento**: Estándar `CONF23-STD-SDLC v15` con enfoque en asincronía y seguridad por diseño.

### Consequences
- **Pros**: Coste operativo nulo, alta modularidad, cumplimiento corporativo.
- **Contras**: Dependencia de la disponibilidad de proveedores en `g4f`, requisitos de hardware para Whisper local.

### Compliance Traceability
- **Security**: Mitigación de OWASP A03 (Exposición de datos) mediante procesamiento local de audio.
- **SDLC**: Alineado con REQ2.01 y REQ4.03 del estándar CONFIANZA23.
