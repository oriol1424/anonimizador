# Licencias de terceros

Objetivo: **coste cero** y uso profesional en el bufete sin pagar licencias.

## Reglas
1. Solo dependencias **gratuitas para uso profesional**: MIT, BSD, Apache-2.0, LGPL,
   GPL/AGPL. **Nunca** licencias "no comerciales" (CC-BY-NC, Qwen Research License...):
   el bufete usa la app en su trabajo, eso es uso comercial.
2. **Nunca se sube a git código, binarios ni modelos de terceros** (`.venv/`, `models/`,
   `dist/`, `*.gguf`, `*.onnx`, `*.dll`...): se instalan o descargan en local. En el repo
   solo hay código propio.
3. Antes de añadir una dependencia o modelo: comprobar su licencia y anotarla aquí.

## Dependencias actuales
| Componente | Licencia | ¿Gratis para el bufete? | Obligaciones |
|---|---|---|---|
| python-docx | MIT | Sí | Conservar aviso de copyright |
| lxml | BSD-3 | Sí | Conservar aviso de copyright |
| PySide6 (Qt) | LGPL-3.0 | Sí | Enlace dinámico (PyInstaller `--onedir` lo cumple) + incluir texto LGPL |
| PyMuPDF | AGPL-3.0 (o comercial) | **Sí, eligiendo AGPL** | Si se entrega la app a otra persona, darle también el código fuente (ver abajo) |
| rapidocr (OCR) | Apache-2.0 | Sí | Conservar aviso; modelos PP-OCRv6 (PaddleOCR, Apache-2.0) incluidos en el paquete |
| onnxruntime | MIT | Sí | Conservar aviso de copyright |

## PyMuPDF y la AGPL, en claro
- Usarla **no cuesta nada**. La licencia comercial solo hace falta para vender software
  cerrado, que no es el caso.
- La obligación de la AGPL aparece al **entregar** la app a otros (p. ej. el USB al bufete):
  quien la recibe debe poder obtener el código fuente de la app. Se cumple incluyendo en
  el paquete una carpeta `codigo_fuente/` (o el enlace al repo) y el texto de las licencias.
  Esto se automatizará en el paso de empaquetado.
- Uso estrictamente personal sin entregar la app a nadie: sin obligaciones.

## Candidatos para próximas fases (verificar al incorporarlos)
| Componente | Licencia | Notas |
|---|---|---|
| GLiNER multi PII | Apache-2.0 (comprobar el modelo concreto) | NER |
| Modelos AINA / BSC (catalán) | Apache-2.0 en su mayoría (comprobar cada uno) | NER catalán |
| Salamandra (BSC) | Apache-2.0 | LLM con buen catalán |
| Qwen3 (4B) | Apache-2.0 | ⚠️ Qwen2.5-**3B** es "Qwen Research" (no comercial): **no usar** |
| llama-cpp-python / llama.cpp | MIT | Motor del LLM local |
