# Progreso

## Estado actual
Fase 0 — Planificación cerrada. Repo publicado en GitHub. Todavía sin código.

## Pendiente de confirmar con el bufete
- [ ] Modelos concretos de Mac (¿Apple Silicon M1+ o Intel?) y RAM; ídem PCs Windows.
- [ ] ¿Firmar la app? (Apple Developer 99 €/año; certificado Windows ~200–400 €/año).
- [ ] Tipos de documento habituales para el corpus sintético.

## Siguientes pasos
1. [ ] Estructura del proyecto: `pyproject.toml`, `src/`, venv, ruff, pytest.
2. [ ] Corpus sintético de pruebas (docx, PDF de texto y PDF escaneado, datos inventados).
3. [ ] MVP DOCX: lector + sustitución de la lista del usuario conservando el formato.
4. [ ] Detector regex español + tests.
5. [ ] Ventana única PySide6 (fichero, tabla con desplegable editable, guardar como).
6. [ ] PDF de texto con redacción real.
7. [ ] PDF escaneado con OCR.
8. [ ] NER (GLiNER) + diálogo de sugerencias.
9. [ ] LLM local de revisión (desactivable por RAM).
10. [ ] GitHub Actions: build Mac + Windows; prueba desde USB en equipos limpios.
11. [ ] Mapa cifrado y des-anonimización de respuestas (fase 2).

## Hecho
- 2026-10-10: Definición de la idea, requisitos y estructura de documentación.
- 2026-10-10: Respuestas del cliente: Mac + Windows, PDFs escaneados y nativos,
  sustituto con desplegable editable, interfaz de una sola ventana.
