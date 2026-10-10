# Anonimizador Legal — Memoria principal del proyecto

App de escritorio **100% local** (Windows) para que un bufete anonimice documentos
Word/PDF antes de pasarlos a una IA. Se entrega por USB a un usuario NO técnico.

Plataformas: **macOS y Windows**. Repo: https://github.com/oriol1424/anonimizador (rama `main`).

## Qué leer según la tarea
| Necesito...                         | Leer                     |
|-------------------------------------|--------------------------|
| Saber qué toca hacer ahora          | `docs/PROGRESO.md`       |
| Requisitos y flujo del usuario      | `docs/REQUISITOS.md`     |
| Arquitectura, módulos, tecnologías  | `docs/ARQUITECTURA.md`   |
| Por qué se decidió algo             | `docs/DECISIONES.md`     |

## Reglas innegociables
1. **Nada sale del equipo**: sin llamadas de red en ejecución, sin telemetría, sin
   descargas de modelos en ejecución (el modelo va dentro del paquete).
2. **Nunca usar documentos reales** de clientes en desarrollo ni en tests: solo
   documentos sintéticos de `tests/corpus/`. La carpeta `datos_reales/` está vetada.
3. Los logs **nunca** contienen texto del documento ni nombres detectados.
4. El fichero de correspondencias (original ↔ sustituto) es un dato personal:
   siempre cifrado y local.
5. En caso de duda, el sistema **sugiere de más**: un falso positivo cuesta un clic;
   un falso negativo es una filtración.

## Flujo de trabajo de Claude
- Al empezar una sesión: leer `docs/PROGRESO.md`.
- Al terminar una tarea: actualizar `docs/PROGRESO.md` (hecho / siguiente paso).
- Si se toma una decisión técnica relevante: añadir una entrada en `docs/DECISIONES.md`.
- **Permisos**: cuando el usuario apruebe un comando que no estaba permitido,
  añadirlo a `permissions.allow` en `.claude/settings.json` para no volver a preguntar.
- **Git**: al cerrar cada paso, commit y push a `main` (el usuario quiere ir publicando).
- Idioma: código e identificadores en inglés; documentación e interfaz en español.
