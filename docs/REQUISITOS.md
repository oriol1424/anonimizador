# Requisitos

## Usuario y entorno
- Abogado/a o administrativo/a sin perfil técnico (sin discapacidad visual).
- Recibe la app por USB y la abre con doble clic. No instala nada.
- **Plataformas: macOS (principal) y Windows.** Hardware desconocido → la app debe
  adaptarse (la revisión con LLM se desactiva sola si no hay RAM suficiente).

## Idioma de los documentos
- **Catalán en el ~99,99% de los casos** → idioma por defecto.
- Selector de idioma (Català / Castellano) por si llega algún documento en castellano.
- El idioma afecta a: nombre de los alias sugeridos (`[TELEFON_1]` / `[TELEFONO_1]`),
  opciones del desplegable, y (más adelante) modelo NER y prompt del LLM.
- Nombres catalanes: `Joan Puig i Ferrer` (= `Puig Ferrer`), `Martí d'Orriols`
  (→ `l'Orriols`, `Orriols`), `Marcel·lí`, apóstrofo tipográfico `’` de Word.

## Interfaz: UNA sola ventana, sencilla
De arriba a abajo:
1. **Documento**: botón "Elegir fichero" (.docx / .pdf) + selector de idioma (Català por defecto).
2. **Qué anonimizar**: tabla de dos columnas `Texto original | Sustituir por`.
   - "Sustituir por" es un **desplegable editable**: se puede elegir una opción
     (`[PERSONA_1]`, `[CLIENT_1]`, `[EMPRESA_1]`, `[ADRECA_1]`, `***`...) o escribir lo que
     se quiera. Las opciones dependen del idioma (`core/lang.py`).
   - Botones `+ Añadir` / `– Quitar`.
3. **Guardar como**: carpeta, nombre y formato (desplegable).
4. Botón grande **"Anonimizar"**.
5. Al terminar, un diálogo de **sugerencias** con lo que la app encontró y el usuario no
   puso: cada fila con su sustituto sugerido (mismo desplegable editable) y una casilla
   para aplicarla. Botón "Aplicar y guardar".

Nada más: sin menús complejos ni configuración visible.

## Documentos de entrada
- DOCX.
- PDF con texto seleccionable.
- **PDF escaneado** (imagen) → requiere OCR en español, local.

## Funcionales
- Variantes automáticas: mayúsculas, tildes, "Sr. Pérez", "Pérez García", "J. Pérez".
- Sustitución consistente: la misma persona → el mismo alias en todo el documento.
- Cubrir cuerpo, tablas, cabeceras, pies, notas al pie, comentarios y **metadatos**.
- PDF: borrado real del texto/píxeles (no un recuadro encima de un texto que sigue ahí).
- Informe final de lo sustituido.
- **Guía de correspondencias** (registro confidencial alias → texto original) junto al
  documento anonimizado, activada por defecto.
- Fase 2: guardar mapa cifrado y "des-anonimizar" la respuesta de la IA.

## No funcionales
- 100% offline.
- Objetivo: funcionar con 8 GB de RAM sin GPU; en Mac Apple Silicon usar Metal.
- Paquete portable para cada sistema (carpeta / .app en USB).
