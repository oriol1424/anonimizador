# Pendiente de preguntar / mirar con el bufete

Lista para revisar con el bufete. Al resolver un punto: marcarlo `[x]`, anotar la
respuesta y ajustar el código o los tests si hace falta.

**Importante:** los ejemplos que nos den deben ser **inventados** (con el formato real,
pero números falsos). Nunca documentos ni datos reales de clientes.

## 1. Formatos de números de identificación (Andorra)
Ahora se detectan por el número que va tras la palabra clave; con el formato exacto se
podrían detectar también cuando aparecen solos.

- [ ] **Número de la CASS**: ¿cuántas cifras tiene?, ¿lleva letras o guiones? Ejemplo
      inventado. ¿Cómo suele aparecer escrito ("núm. CASS", "afiliat a la CASS amb el
      número"...)?
- [ ] **Permiso de residencia / de residencia y trabajo**: formato del número y cómo
      aparece en los escritos. ¿Hay otros documentos de inmigración con número propio?
- [ ] **Número de causa de la Batllia** (y del Tribunal Superior, Tribunal de Corts):
      formato habitual. Ejemplo inventado.
- [ ] **Pasaportes**: ¿de qué países salen más a menudo? (andorrano, español, francés,
      portugués...). Con eso se añaden sus formatos para detectarlos sin la palabra
      "passaport" delante.
- [ ] **Pasaporte andorrano**: confirmar el formato "O" + 7 cifras (fuente: MoraBanc,
      2017) y si aparece también el *número personal* del pasaporte (otro número distinto).
- [ ] **NRT**: confirmar el formato "F-123456-X" (letra + 6 cifras + letra) y si se escribe
      con guiones, espacios o junto.
- [ ] **Número de cens** u otros registros del Comú: ¿aparecen en los documentos? Formato.
- [ ] ¿Aparecen **DNI/NIE españoles** a menudo o casi nunca?
- [ ] **Matrículas andorranas**: confirmar formato "A 1234" (fuente: Wikipedia).

## 2. Otros datos que pueden aparecer
- [ ] Números de **finca / registro de la propiedad**, protocolos notariales, números del
      **Registre de Societats**: ¿aparecen? ¿Hay que anonimizarlos?
- [ ] Cuentas bancarias en formato distinto del IBAN (número de cuenta local andorrano).
- [ ] Fechas de nacimiento: ¿se anonimizan o se dejan?
- [ ] Otros datos que el bufete considere sensibles en sus escritos.

## 3. Documentos
- [ ] **Tipos de documento habituales** (demandas, contratos, poderes, escrituras,
      informes médicos...) para crear documentos inventados parecidos en `tests/corpus/`.
- [ ] ¿Qué proporción son **escaneados** y de qué calidad (fotocopias, fotos del móvil)?
- [ ] ¿Tamaño típico (nº de páginas) y el más largo que suelan tener?
- [ ] ¿Llegan documentos en **castellano** o en **francés**?

## 4. Equipos
- [x] Mac de referencia: MacBook Air 2022, M2, 8 GB RAM (2026-10-11).
- [ ] **PCs Windows** del bufete: modelo, procesador y RAM.
- [ ] En el Mac: medir tiempos y memoria con un documento largo y probar el acelerador
      **CoreML** del chip M2 para el OCR.
- [ ] ¿Pueden ejecutar programas desde el USB, o los ordenadores tienen restricciones
      (antivirus, permisos de administrador)?

## 5. Decisiones que dependen del bufete
- [ ] Verificación de escaneados: releer la página entera (ahora, más seguro) o solo las
      franjas modificadas (unos 4 min menos en 80 páginas). Ver `docs/DECISIONES.md`.
