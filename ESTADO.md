# ESTADO — indice_inmobiliario_argentina

**Última actualización:** 2026-10-08 (cierre de la sesión 1, que empezó el 2026-10-07). Punto de
entrada para retomar: este archivo → `CLAUDE.md` (reglas) → `CONTEXTO.md` (método, trampas, mapa del
código) → `.claude/memory/project.md` (historial de sesiones).

## 0. Estado en una línea

Primera versión funcionando y **verificada en Colab** (commit `3ff744a`, 2026-10-08: el ZIP coincide
con lo versionado). Datos de Zonaprop a sep-2026, índice a jun-2026 (último mes con salario). Sección
del informe INECO escrita (`docs/informe_indicadores/seccion_inmobiliario.tex`). Sin trabajo a medias.
**Zonaprop es una prueba piloto**: la versión definitiva usará un relevamiento propio de INECO
(convenios con portales o *web scraping*), todavía no implementado (CONTEXTO §5).

## 1. Cobertura de datos

| Fuente | Último dato | Cómo se actualiza |
|---|---|---|
| Zonaprop CABA (alquiler / venta) | sep-2026 | `python scripts/actualizar_zonaprop.py` (busca el PDF nuevo) |
| Zonaprop GBA Norte / Oeste / Sur | sep-2026 | ídem |
| Mediana y promedio SIPA | jun-2026 (jun sin SAC imputado con RIPTE) | automático (`construir.py --refrescar`) |
| RIPTE | jul-2026 | automático |
| IPC GBA gastos comunes (expensas) / IPC nacional | ago-2026 | automático |
| Dólar MEP / oficial | oct-2026 (mes en curso, parcial) | automático |
| Ancla de expensas (solo CABA) | jun-2026 (Propio, $171.545) | **manual**: `data/reference/expensas_ancla.csv` |

Series de Zonaprop (`data/processed/zonaprop_series.csv`, primer mes con dato):

| Región | Alquiler desde | Venta desde | Meses de alquiler: publicados / derivados / interpolados |
|---|---|---|---|
| CABA | oct-2017 | mar-2018 | 45 / 15 / 48 (58% no publicado) |
| GBA Norte | feb-2023 | dic-2020 | 17 / 6 / 21 |
| GBA Oeste | dic-2020 | ago-2020 | 20 / 16 / 34 |
| GBA Sur | dic-2025 | may-2025 | 6 / 3 / 1 |

Huecos grandes de CABA: jul-2018 a jun-2020 (no está en el Internet Archive) y feb a dic-2024
(informes que son imagen pura). 105 informes en el catálogo (104 PDF completos + 1 truncado).

## 2. Cifras vigentes (`python scripts/construir.py`)

**Jun-2026** (salario mediano bruto sin SAC $1.666.213; RIPTE $1.915.879):

| Región | Alquiler 2 amb | % salario mediano | + expensas | % RIPTE | USD/m² | salarios/m² (MEP) | años de salario 50 m² |
|---|---|---|---|---|---|---|---|
| CABA | $860.106 | 51,6% | 61,9% | 44,9% (53,8% c/exp.) | 2.467 | 2,18 (oficial 2,15) | 8,4 |
| GBA Norte | $800.743 | 48,1% | — | 41,8% | 2.404 | 2,13 | 8,2 |
| GBA Oeste | $632.324 | 38,0% | — | 33,0% | 1.577 | 1,39 | 5,4 |
| GBA Sur | $621.578 | 37,3% | — | 32,4% | 1.665 | 1,47 | 5,7 |

Años de salario = 50 × salarios por m² / 13 (no es una columna del pipeline: se calcula aparte).
Expensas CABA = 19,9% del alquiler.

**CABA, promedios anuales** (% salario mediano · con expensas · salarios/m² MEP · oficial):

| Año | Alquiler | + expensas | m² MEP | m² oficial |
|---|---|---|---|---|
| 2017 (oct-dic) | 45,1 | 56,0 | — | — |
| 2018 | 47,2 | 58,1 | 2,96 | 2,95 |
| 2019 | 46,2 | 56,9 | 3,84 | 3,59 |
| 2020 | 50,9 | 60,8 | 6,21 | 3,91 |
| 2021 | 55,3 | 64,3 | 5,64 | 3,29 |
| 2022 | 55,9 | 64,3 | 4,69 | 2,44 |
| 2023 | 63,8 | 71,2 | 4,31 | 2,23 |
| 2024 | 60,6 | 67,4 | 3,13 | 2,44 |
| 2025 | 51,0 | 60,1 | 2,45 | 2,31 |
| 2026 (ene-jun) | 52,1 | 62,0 | 2,27 | 2,22 |

**CABA, meses clave**: máximo del alquiler ene-2024 74,0% (79,9% con expensas); salarios/m² máximo
oct-2020 7,16 (oficial 3,76; 27,5 años de salario), mar-2018 2,27, nov-2023 4,79 (18,4 años),
jun-2026 2,18 = mínimo de la serie. Entre nov-2023 y jun-2026 el salario mediano pasó de USD 453 a
USD 1.131 al MEP (×2,5) y el precio del m² subió 13,6% (2.171 → 2.467).

## 3. Dónde se citan las cifras (actualizar todo junto si cambian)

| Documento | Qué cifras |
|---|---|
| `ESTADO.md` §2 | todas |
| `docs/informe_indicadores/seccion_inmobiliario.tex` | cuadro jun-2026 (alquiler, % salario, con expensas, salarios/m², años de salario); salario $1.666.213; ancla $171.545; 58% de meses no publicados; RIPTE 44,9/53,8; promedios 2018-19, 2023, 2025, 2026; ene-2024 74,0/79,9; oferta ×3,4 (Zonaprop ago-2026); 2,18/2,15, USD 2.467, 2,27 (mar-2018), 7,16 (oct-2020), 8,4/18,4/27,5 años, GBA 5,4-5,7; salario USD 450→1.130 y precio +14%; 2020: 6,2 vs 3,9 |
| Figuras del informe | `output/graficos/G01_alquiler_pct_salario_mediano.png` y `G03_salarios_por_m2_mediano.png` → carpeta `figuras/` del Overleaf del usuario |
| `README.md` | sin cifras |

La sección es parte del informe INECO "Propuesta de Indicadores Económicos" (documento completo en
el Overleaf del usuario). La metodología describe el relevamiento propio (genérico); los resultados
están rotulados como "preliminares" (prueba piloto con Zonaprop).

## 4. Verificación

- `python -m pytest tests -q` → 18 passed.
- `python scripts/actualizar_zonaprop.py --solo-extraer`: 89 informes con alquiler, 96 con venta;
  142 comparaciones derivado vs publicado, 1 fuera de tolerancia (CABA ago-2021, −0,34%).
  3 empalmes por revisión: GBA Oeste alquiler (×0,988) y venta (×0,957) entre ene y mar-2026;
  GBA Norte venta dic-2020 (×1,034, cifra tomada fuera del resumen).
- **Colab (2026-10-08, commit `3ff744a`)**: `python scripts/comparar_zip.py <zip>` → índice, series de
  Zonaprop, salarios y expensas idénticos (dif. máx. 4e-16); única diferencia: `tipo_de_cambio.csv`
  fila 2026-10 (mes en curso, promedio parcial del dólar). Esperable.
- Sección LaTeX compilada con pdflatex (MiKTeX) con el preámbulo del informe: sin errores, sin
  referencias indefinidas ni cajas desbordadas.

## 5. Próximos pasos posibles (a decidir con el usuario)

1. **Relevamiento propio de INECO** (la versión definitiva): diseñar el módulo que tome avisos por
   convenio o *web scraping* y produzca la misma tabla que `zonaprop.series()` + expensas observadas
   por región (CONTEXTO §5). Antes: definir con el usuario portales, convenios y frecuencia.
2. **Llenar huecos de Zonaprop** (mientras dure el piloto): 8 informes son imagen pura (CABA sep-2017,
   feb/may/jul/sep/oct-2024; GBA Norte abr-2024; GBA Oeste sep-2024) → OCR, o cifras de la prensa en
   una tabla con fuente. Otros 8 no traen el alquiler en el texto (CABA dic-2023; GBA Norte dic-2020 y
   jul/ago/nov-2021; GBA Oeste ago/dic-2020 y ene-2021) y 1 no trae la venta (CABA oct-2017): revisar la
   redacción de esos PDFs.
3. **Ancla de expensas para GBA** (hoy solo CABA) y validar la de CABA con otra fuente.
4. Agregar al pipeline la columna **años de salario** (hoy se calcula aparte para el informe).
5. **Índice compuesto** (base 100) que combine los dos indicadores, si el usuario lo quiere.
6. Validación cruzada con el informe trimestral de alquileres del IDECBA (Argenprop, $/m²).
7. Variantes: salario neto (~83% del bruto); Rosario y Córdoba (Zonaprop también los publica).

## 6. Rutina mensual (mientras el piloto use Zonaprop)

1. `git pull`.
2. `python scripts/actualizar_zonaprop.py` (descubre el informe nuevo, lo baja y extrae; revisar que
   el chequeo no muestre diferencias nuevas fuera de tolerancia ni empalmes nuevos inesperados).
3. `python scripts/construir.py --refrescar`.
4. `python -m pytest tests -q`.
5. Actualizar §1-§3 de este archivo y, si cambian las cifras citadas, la sección LaTeX.
6. Commit + push si el usuario lo pide. El usuario corre el notebook en Colab y pasa el ZIP:
   `python scripts/comparar_zip.py <zip>`.

## 7. PC nueva

1. `git clone https://github.com/santiagoriverti/indice_inmobiliario_argentina.git` (repo público).
   En esta PC el push usa Git Credential Manager (`credential.helper=manager`); en otra, el usuario
   se autentica la primera vez. Claude no ingresa tokens.
2. `pip install -r requirements.txt` (Python 3.12+; probado con 3.14 local y el de Colab). Incluye
   pypdf y PyMuPDF, que solo usa `actualizar_zonaprop.py`.
3. `PYTHONUTF8=1 python -m pytest tests -q` → 18 passed.
4. `PYTHONUTF8=1 python scripts/construir.py --refrescar` reconstruye todo sin PDFs (usa
   `data/reference/zonaprop_valores.csv`, versionado). Sin `--refrescar` también funciona: si falta
   el cache, lo baja.
5. Solo si hay que releer los PDFs: `python scripts/actualizar_zonaprop.py` los vuelve a bajar a
   `data/cache/zonaprop/` (~150 MB, ignorado por git; tarda: el Internet Archive es lento y a veces
   rechaza pedidos, el script reintenta).
