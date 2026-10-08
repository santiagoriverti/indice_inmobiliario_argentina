# CONTEXTO — definiciones, decisiones, fuentes y trampas

## 1. Qué mide el índice

Dos indicadores mensuales por región (CABA, GBA Norte, GBA Oeste, GBA Sur):

| Indicador | Fórmula | Columna |
|---|---|---|
| Costo de alquilar | alquiler 2 amb / salario × 100 | `pct_alquiler_{salario}` |
| Costo de alquilar con expensas (solo CABA) | (alquiler + expensas) / salario × 100 | `pct_alquiler_expensas_{salario}` |
| Costo de comprar | precio USD/m² × dólar / salario | `salarios_por_m2_{salario}_{dolar}` |

`{salario}` ∈ `mediana` (principal), `ripte`; `{dolar}` ∈ `mep` (principal), `oficial`.

## 2. Decisiones (tomadas con el usuario el 2026-10-07)

1. **Cobertura**: CABA + GBA Norte/Oeste/Sur (las regiones del Zonaprop Index). Nacional queda
   afuera de la v1 (no hay series de precios largas y comparables por provincia).
2. **Salario**: mediana de la remuneración bruta de asalariados registrados del sector privado
   (SIPA) como principal; RIPTE como alternativa. Ambos **brutos** (antes de aportes: el neto es ~83%).
3. **Dólar**: MEP para pasar el USD/m² a pesos (es el que usa Zonaprop y el relevante para operar);
   oficial A3500 como sensibilidad.
4. **Expensas**: nivel ancla × índice de precios. El usuario eligió el IPC de CABA (IPCBA), pero el
   IPCBA **no publica la apertura de expensas por API** (datos.gob.ar solo tiene sus divisiones). Se
   usa en su lugar el IPC **GBA** de INDEC, apertura "Reparaciones y gastos comunes de la vivienda"
   (`104.1_I2C_2016_M_42`, desde abr-2016), que cubre CABA + conurbano. Ancla en
   `data/reference/expensas_ancla.csv`. Solo hay ancla para CABA: el GBA va sin expensas.
5. **Zonaprop es una prueba piloto** (2026-10-08): la versión definitiva del índice usará datos de
   un **relevamiento propio de INECO** (convenios con portales inmobiliarios o *web scraping*). La
   sección del informe INECO (`docs/informe_indicadores/seccion_inmobiliario.tex`) describe esa
   metodología de forma genérica y presenta las cifras de Zonaprop como "resultados preliminares".
   Ver §5.

## 3. Fuentes

| Dato | Fuente | Desde | Notas |
|---|---|---|---|
| Alquiler 2 amb 50 m² ($/mes) | Zonaprop Index (PDF mensual) | CABA oct-2017 · GBA Oeste dic-2020 · GBA Norte feb-2023 · GBA Sur dic-2025 | precio publicado (oferta), contratos nuevos, **sin expensas** |
| Venta departamentos (USD/m²) | Zonaprop Index | CABA mar-2018 · GBA Oeste ago-2020 · GBA Norte dic-2020 · GBA Sur may-2025 | precio publicado, no de escritura |
| Salario mediano / promedio SIPA | datos.gob.ar `153.1_RNERACIANA_2009_M_20` / `153.1_RNERACIDIO_2009_M_21` | 1995 | **incluye SAC en jun/dic**; ~2 meses de rezago |
| RIPTE | datos.gob.ar `158.1_REPTE_0_0_5` | 1994 | sin SAC; ~1 mes de rezago |
| Índice de expensas | IPC GBA INDEC `104.1_I2C_2016_M_42` | abr-2016 | sube fuerte en jun/dic (aguinaldo de encargados) |
| Guía para interpolar alquiler | IPC nacional nivel general `148.3_INIVELNAL_DICI_M_26` | dic-2016 | ver trampas: el IPC "Alquiler de la vivienda" no sirve de guía |
| Dólar MEP | argentinadatos `/cotizaciones/dolares/bolsa` | oct-2018 | antes: CCL (`contadoconliqui`, 2013+) × factor MEP/CCL de los 6 primeros meses comunes (≈1,0016) |
| Dólar oficial | BCRA API v4, variable 5 (A3500) | 2010 | `verify=False` (el certificado del BCRA no valida) |

"Desde" = primer mes con dato en `data/processed/zonaprop_series.csv` (incluye meses derivados).
Zonaprop publica la venta de CABA desde dic-2011 y el alquiler desde ~2012, pero los PDFs anteriores
a sep-2017 no están en el Internet Archive.

### Zonaprop: cómo se arma la serie

- Los PDFs se descubren con la API CDX del Internet Archive (prefijos `noticias/` y `blog/` de
  `wp-content/uploads`) y probando las URLs actuales del sitio (`blog/wp-content/uploads/AAAA/MM/
  INDEX_<REGION>_REPORTE_AAAA-MM.pdf`, carpeta = mes del informe + 1, a veces +0/+2, sufijos `-1`/`-2`).
  Catálogo: `data/reference/zonaprop_catalogo.csv`.
- Nombres históricos: `INDEX-BA-Reporte-Mercado-AAAA-MM.pdf` (CABA 2017-2020),
  `INDEX-GBA-NORTE-Reporte-Mercado-…` (2020), `INDEX_<REG>_REPORTE_…` (2020+), `INDEX_GBA_REPORTE_…`
  (= GBA Norte, 2026). Algunos están en carpetas que no coinciden con el mes (ej. 2019/10 tiene
  informes de 2020). `RSA` = Rosario y `CBA` = Córdoba existen pero no se usan (fuera de la v1).
- `extraer()` lee las 3 primeras páginas (portada + resumen ejecutivo) y saca, con expresiones
  regulares, el **nivel** (primer "USD x por m2"; primer "2 ambientes … $x por mes") y las
  **variaciones** que acompañan a cada nivel (la más cercana): mensual, acumulada en el año y 12 meses.
  Si no lo encuentra en el resumen, busca en todo el PDF (`*_donde = motor:completo`, menos confiable).
- Motores de texto, en orden: **pypdf**; **PyMuPDF `get_text`** (los informes 2022-2024 tienen el texto
  en una capa que pypdf no ve); para PDFs truncados, **PyMuPDF `get_texttrace`** (ver trampas).
- Cada informe aporta hasta 4 niveles: el publicado (t), t−1 (con la var. mensual), t−12 (con la var.
  12 meses) y diciembre del año anterior (con la acumulada). Prioridad: publicado > derivado_mes >
  derivado_12m > derivado_anio > publicado_completo. Las variaciones vienen con 1 decimal: un nivel
  derivado tiene un error de redondeo de hasta ±0,05%. Las variaciones "en términos reales" se
  descartan.
- **Empalme por revisiones** (`_empalmar`): Zonaprop a veces revisa la serie (GBA Oeste bajó ~4% su
  nivel de venta entre los informes de ene y mar-2026). Se recorren los informes del más nuevo al más
  viejo; si los niveles de un informe se solapan con los ya aceptados y difieren de forma consistente
  entre 1% y 15%, ese informe y todos los anteriores se reescalan. Toda la serie queda en la escala
  del último informe. `zonaprop.chequeos()` lista los empalmes y las diferencias que quedan.
- Huecos que quedan: **alquiler** se interpola siguiendo el IPC nacional nivel general (camino de la
  guía + corrección lineal para empalmar en los dos extremos, en logaritmos); **venta**, log-lineal.
  Columna `tipo_alquiler` / `tipo_venta` = origen de cada dato.

## 4. Trampas

- **Aguinaldo**: la mediana y el promedio SIPA publicados incluyen el SAC en junio y diciembre (la
  mediana de jun-2026 es 50% más alta que la de mayo). `indice.sin_aguinaldo` reemplaza esos meses
  por la media geométrica de los vecinos (o, si falta el mes siguiente, mes anterior × variación del
  RIPTE). Dividir por 1,5 subestima (no todos cobran SAC completo).
- **Zonaprop mide precios de oferta**, no de cierre. El precio de escritura no se observa; como
  indicio, el informe de ago-2026 dice que el 26% de los avisos de venta se retasó a la baja en los
  últimos 6 meses, con un descuento promedio de 5,9%. El alquiler es de **contratos nuevos**: durante
  la ley 27.551 (2020-2023) subió mucho más rápido que los contratos vigentes; tras su derogación
  (DNU 70/2023, dic-2023) la oferta creció (ago-2026: 3,4 veces la de feb-2023, según Zonaprop) y los
  precios se desaceleraron.
- **Wayback**: hay capturas truncadas a 1 MiB (`x-archive-orig-content-length: 1048576`, sin
  `%%EOF`); se prueban otras capturas de la misma URL y, si ninguna está completa, se guarda la
  truncada como `.parcial.pdf`. Ni pypdf ni el texto común de PyMuPDF sirven ahí: faltan las fuentes
  (están al final del archivo) y PyMuPDF **une dígitos repetidos** ("$ 33.357" → "$ 3.357"). La traza
  de glifos (`get_texttrace`) sí lee bien; se normalizan los espacios ("33 . 357" → "33.357"). Probado:
  la copia truncada y la completa de CABA feb-2021 dan las mismas cifras.
- El sitio de Zonaprop tiene Cloudflare en la API de WordPress (no saltearlo: solo se piden PDFs
  estáticos). Los informes viejos en `/noticias/…` redirigen a una ruta rota: solo quedan en el Wayback.
- **El IPC "Alquiler de la vivienda" no sirve para interpolar** el alquiler de Zonaprop: mide contratos
  vigentes con ajustes anuales (abr-2024: +40% en un mes) y genera saltos falsos. Se usa el IPC general.
- En los PDFs de 2026 los títulos del resumen están corridos ("Venta" arriba del párrafo de alquiler):
  por eso se toma la variación **más cercana** al nivel y no la del título.
- El IPC GBA de gastos comunes salta en junio y diciembre (aguinaldo de encargados): las expensas
  estimadas también. Es real, no un error.
- El ancla de expensas es una **mediana de avisos de alquiler** (unidades que se alquilan), no el
  promedio de todos los consorcios (ConsorcioAbierto da ~$355.000 en jul-2026 para todas las
  unidades, de todos los tamaños).
- **Mes en curso**: el dólar del último mes es un promedio parcial (cambia día a día). Por eso un ZIP
  de Colab corrido otro día difiere en esa fila de `tipo_de_cambio.csv`; el índice no la usa (llega
  hasta el último mes con salario).
- `src/graficos.py` **no debe forzar** `matplotlib.use('Agg')`: en un notebook apaga los gráficos.
  El backend sin pantalla se fija solo en `scripts/construir.py`.

## 5. Hacia la versión definitiva: relevamiento propio de INECO

Lo que describe la sección del informe (`docs/informe_indicadores/seccion_inmobiliario.tex`) y
todavía **no está implementado**:

- **Fuente**: avisos de portales inmobiliarios, por convenio o *web scraping*. Solo con convenio o
  respetando los términos de uso y el `robots.txt` del sitio; **nunca saltear protecciones
  anti-bot** (Cloudflare, captchas).
- **Variables por aviso**: operación (venta/alquiler), tipo de inmueble, barrio o partido, superficie
  cubierta, ambientes, antigüedad, precio y moneda, expensas, fechas de alta y baja.
- **Limpieza**: duplicados (misma unidad en varias inmobiliarias o portales), avisos sin precio o
  superficie, atípicos de precio por m² dentro de cada zona.
- **Unidad de referencia**: departamento de 2 ambientes y 50 m² cubiertos (la misma del piloto).
  Expensas = mediana del $/m² informado en los avisos × 50 m², en cada región (reemplaza el ancla × IPC).
- **Ajuste por composición**: medianas dentro de estratos (zona × ambientes × antigüedad) agregadas
  con ponderaciones fijas del stock de avisos de un año base.
- **Oferta vs. cierre**: seguir la brecha con el monto de escrituras del Colegio de Escribanos.
- **Encastre en el código**: la nueva fuente tiene que producir la misma tabla larga que
  `zonaprop.series()` (`periodo`, `region`, `alquiler_2amb`, `venta_usd_m2`, `tipo_*`) y una tabla
  de expensas por región como la de `indice.expensas()`. Así `indice.calcular`, la exportación, los
  gráficos y el notebook no cambian. Zonaprop puede quedar como validación cruzada.

## 6. Mapa del código

| Archivo | Qué hace |
|---|---|
| `src/fuentes.py` | rutas del repo; descarga con cache de datos.gob.ar (salarios, IPC), argentinadatos (MEP, CCL) y BCRA (A3500) |
| `src/zonaprop.py` | catálogo de PDFs (Wayback + sitio), descarga, extracción por regex, `chequeos`, `_empalmar`, `series` (niveles mensuales + huecos) |
| `src/indice.py` | `sin_aguinaldo`, `salarios`, `expensas`, `calcular` (tabla larga con todos los indicadores) |
| `src/pipeline.py` | `construir()`: arma el diccionario `R` que usan construir.py y el notebook |
| `src/exportar.py` | CSV, Excel (7 hojas), gráficos PNG y ZIP del notebook; `ultimo_dato` |
| `src/graficos.py` | 4 gráficos (alquiler % salario y salarios por m², con mediana y con RIPTE) |
| `scripts/actualizar_zonaprop.py` | descubre/baja/extrae los PDFs → `data/reference/zonaprop_{catalogo,valores}.csv` |
| `scripts/construir.py` | arma todo → `data/processed/*.csv`, `output/indice_inmobiliario.xlsx`, `output/graficos/` |
| `scripts/gen_notebooks.py` | genera `notebooks/01_indice_inmobiliario.ipynb` |
| `scripts/comparar_zip.py` | compara un ZIP de Colab con `data/processed/` |
| `tests/` | extracción de PDFs, URLs, empalme, interpolación, SAC, expensas, ratios |

Flujo: `actualizar_zonaprop.py` (PDF → `zonaprop_valores.csv`, versionado) → `construir.py` /
notebook (`zonaprop_valores.csv` + APIs → índice). Los notebooks nunca leen PDFs.
