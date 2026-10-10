# Registro de decisiones

| Fecha      | Decisión | Motivo |
|------------|----------|--------|
| 2026-10-10 | App de escritorio Python + PySide6, empaquetada con PyInstaller | Usuario no técnico, entrega por USB, todo local |
| 2026-10-10 | LLM embebido con llama-cpp-python (no Ollama) | Ollama requiere instalación y un servicio; llama.cpp va dentro de la app |
| 2026-10-10 | Detección en capas (usuario → regex → NER → LLM) | Un LLM pequeño solo no es fiable ni rápido; las reglas cubren lo estructurado |
| 2026-10-10 | El LLM solo sugiere, el usuario confirma | Responsabilidad profesional y errores del modelo |
| 2026-10-10 | Multiplataforma macOS + Windows | El bufete usará Mac y algún Windows |
| 2026-10-10 | Builds con GitHub Actions | No se puede generar el .app de Mac desde Windows |
| 2026-10-10 | Soporte OCR (RapidOCR propuesto) | Llegarán PDFs escaneados |
| 2026-10-10 | Ventana única; sustituto con desplegable editable | Petición del cliente: sencillez |
| 2026-10-10 | Repo: https://github.com/oriol1424/anonimizador | Publicación del progreso |
