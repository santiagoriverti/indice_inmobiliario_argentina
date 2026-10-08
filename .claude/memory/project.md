# Historial de sesiones — indice_inmobiliario_argentina

## Sesión 1 — 2026-10-07 y 2026-10-08: arranque, piloto con Zonaprop, Colab e informe

### Objetivo y decisiones
- Pedido del usuario: índice inmobiliario que refleje el costo de alquilar + expensas respecto del
  salario y la cantidad de salarios para comprar un m².
- Decisiones (AskUserQuestion, 2026-10-07): CABA + GBA (Norte/Oeste/Sur) · mediana SIPA + RIPTE ·
  MEP + oficial como sensibilidad · expensas = ancla + índice.
- Cambio respecto de lo elegido: el IPCBA no tiene la apertura de expensas por API → IPC GBA de
  INDEC "Reparaciones y gastos comunes de la vivienda" (`104.1_I2C_2016_M_42`). Avisado al usuario.
- 2026-10-08: el usuario aclaró que los datos de propiedades (alquiler, venta, expensas) de la
  versión definitiva vendrán de un **relevamiento propio de INECO** (convenios con portales o web
  scraping). Zonaprop pasa a ser prueba piloto. La sección del informe se escribió genérica.

### Lo que se construyó
- `src/zonaprop.py`: catálogo por API CDX del Wayback (prefijos `noticias/` y `blog/`) + prueba de
  URLs actuales del sitio en paralelo (6 hilos; secuencial tardaba >10 min). 105 informes (64 Wayback
  + 40 sitio + 1 manual: CABA abr-2019 `Index-Abril-Buenos-Aires.pdf`, nombre sin fecha).
- Extracción con regex en el resumen; motores pypdf → PyMuPDF `get_text` (informes 2022-24 con el
  texto en una capa que pypdf no ve) → PyMuPDF `get_texttrace` para truncados.
- `_empalmar`: detecta revisiones de Zonaprop (GBA Oeste −4% entre ene y mar-2026).
- Huecos: alquiler interpolado con el IPC general como guía; venta log-lineal.
- `src/indice.py`: SAC fuera de la mediana SIPA (media geométrica de vecinos o RIPTE), expensas,
  indicadores. Exportación, 4 gráficos, notebook 01, 18 tests.
- `scripts/comparar_zip.py` (2026-10-08) para los ZIP de Colab.
- `docs/informe_indicadores/seccion_inmobiliario.tex`: sección del informe INECO (metodología
  genérica del relevamiento propio + resultados preliminares con Zonaprop). Compilada con pdflatex.

### Problemas encontrados y cómo se resolvieron
- Cloudflare en la API de WordPress de Zonaprop → no se saltea; se usan Wayback + URLs estáticas.
- URLs viejas `/noticias/…` redirigen a una ruta rota → solo Wayback.
- Capturas del Wayback truncadas a 1 MiB (`x-archive-orig-content-length: 1048576`): la primera
  captura (la que devuelve `collapse=urlkey`) suele ser la truncada → se piden todas y se prueba.
- PyMuPDF `get_text` en PDFs truncados une dígitos repetidos ("33.357" → "3.357", "barrios" →
  "barios") porque faltan las fuentes; `get_texttrace` no.
- Regex: "m²" con superíndice (2026), "2.557 usd/m2" (2019), "m 2" partido (traza), variaciones
  "en términos reales" (se descartan), títulos del resumen 2026 corridos (se toma la variación más
  cercana al nivel), coma decimal mal unida en la traza ("2 , 0.3%").
- El IPC "Alquiler de la vivienda" como guía de interpolación generaba saltos (abr-2024 +40%) → IPC
  general.
- `matplotlib.use('Agg')` en graficos.py apagaba los gráficos del notebook → movido a construir.py.
- Etiquetas finales de los gráficos superpuestas → `_ubicar_etiquetas`. Tildes y "m²" en los
  gráficos corregidos el 2026-10-08.
- La primera versión de la sección LaTeX tenía 5 imprecisiones (detectadas al releer contra los
  datos el 2026-10-08): "cuatro de cada diez" meses completados (eran 58%), "esfuerzo" usado para
  cifras sin expensas (44,9% RIPTE; 51%/52%), "al final de la vigencia de la Ley 27.551" para
  ene-2024 (ya estaba derogada), y un +6% de precio de otro período. Corregidas y avisado al usuario.

### Verificación
- Colab 2026-10-08 con `3ff744a`: ZIP idéntico a lo versionado salvo el dólar del mes en curso.

### Fuentes vistas y no usadas (por ahora)
- Expensas: ConsorcioAbierto jul-2026 $354.652 (promedio de todas las unidades de 15.000 consorcios);
  Octopus ago-2026 $309.625. Ancla usada: Propio jun-2026, mediana 2 amb $171.545 ($3.995/m²) en
  avisos de alquiler CABA (vía iProfesional 01-09-2026).
- IDECBA: informe trimestral de alquileres (Argenprop, $/m² por ambientes) — validación cruzada.
- Zonaprop también publica Rosario (`RSA`) y Córdoba (`CBA`).
- datos.gob.ar dataset 193 = IPCBA (solo divisiones, sin expensas).
