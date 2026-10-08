# ESTADO — indice_inmobiliario_argentina

**Última actualización:** 2026-10-07 (sesión 1, arranque). Punto de entrada para retomar: este
archivo → `CLAUDE.md` (reglas) → `CONTEXTO.md` (método y trampas) → `.claude/memory/project.md` (historial).

## 0. Estado en una línea

Primera versión funcionando de punta a punta (local): Zonaprop (105 informes PDF) + salarios + dólar →
índice mensual por región, Excel, CSV, 4 gráficos y notebook de Colab (probado en local con nbconvert,
**falta probarlo en Colab**: necesita el push).

## 1. Cobertura de datos

| Fuente | Último dato | Cómo se actualiza |
|---|---|---|
| Zonaprop CABA (alquiler / venta) | sep-2026 | `python scripts/actualizar_zonaprop.py` (busca el PDF nuevo) |
| Zonaprop GBA Norte / Oeste / Sur | sep-2026 | ídem |
| Mediana y promedio SIPA | jun-2026 (jun sin SAC imputado con RIPTE) | automático (`--refrescar`) |
| RIPTE | jul-2026 | automático |
| IPC GBA gastos comunes (expensas) / IPC nacional | ago-2026 | automático |
| Dólar MEP / oficial | oct-2026 (parcial) | automático |
| Ancla de expensas | jun-2026 (Propio) | **manual**: `data/reference/expensas_ancla.csv` |

Series de Zonaprop (`data/processed/zonaprop_series.csv`): alquiler CABA desde oct-2017, venta CABA
desde mar-2018; GBA Oeste desde 2020; GBA Norte alquiler desde 2023 (venta 2020); GBA Sur desde
2025-26. El índice llega hasta el último mes con salario (jun-2026).

Origen de los meses de alquiler en CABA: 45 publicados, 15 derivados de variaciones, 48 interpolados
(los huecos grandes: jul-2018 a jun-2020 y feb a dic-2024).

## 2. Cifras vigentes (`python scripts/construir.py`)

**Jun-2026** (salario mediano bruto sin SAC $1.666.213):

| Región | Alquiler 2 amb | % salario mediano | + expensas | % RIPTE | USD/m² | salarios/m² (MEP) |
|---|---|---|---|---|---|---|
| CABA | $860.106 | 51,6% | 61,9% | 44,9% | 2.467 | 2,18 (oficial 2,15) |
| GBA Norte | $800.743 | 48,1% | — | 41,8% | 2.404 | 2,13 |
| GBA Oeste | $632.324 | 38,0% | — | 33,0% | 1.577 | 1,39 |
| GBA Sur | $621.578 | 37,3% | — | 32,4% | 1.665 | 1,47 |

CABA en el tiempo (% salario mediano · con expensas · salarios/m² MEP · oficial):
dic-2019 47,2 · 57,8 · 4,72 · 3,90 — nov-2023 69,8 · 76,5 · 4,79 · 1,90 — **ene-2024 (máximo) 74,0 · 79,9**
· 4,62 · 3,26 — jun-2025 50,9 · 60,4 · 2,24 · 2,23 — jun-2026 51,6 · 61,9 · 2,18 · 2,15.
Máximo de salarios por m² en CABA: oct-2020 (7,16 con MEP); mínimo de la serie: jun-2026 (2,18).

## 3. Verificación

- `python -m pytest tests -q` → 18 passed.
- `python scripts/actualizar_zonaprop.py --solo-extraer`: 89 informes con alquiler, 96 con venta;
  142 comparaciones derivado vs publicado, 1 fuera de tolerancia (CABA ago-2021, −0,34%).
  3 empalmes por revisión: GBA Oeste alquiler (×0,988) y venta (×0,957) entre ene y mar-2026;
  GBA Norte venta dic-2020 (×1,034, cifra tomada fuera del resumen).
- Notebook 01 ejecutado en local (`_local_run/`): sin errores, 4 gráficos, ZIP generado.

## 4. Próximos pasos posibles (a decidir con el usuario)

1. **Push y prueba en Colab** del notebook 01.
2. **Llenar huecos de Zonaprop**: 8 informes son imagen pura, sin texto (CABA sep-2017, feb/may/jul/
   sep/oct-2024; GBA Norte abr-2024; GBA Oeste sep-2024) → OCR, o cargar a mano las cifras de la
   prensa en una tabla con fuente. Otros 8 no traen el alquiler en el texto (CABA dic-2023; GBA Norte
   dic-2020 y 2021; GBA Oeste ago/dic-2020 y ene-2021) y 1 no trae la venta (CABA oct-2017): revisar
   la redacción. El hueco jul-2018 a jun-2020 de CABA no está en el Internet Archive.
3. **Ancla de expensas para GBA** (hoy solo CABA) y validar el ancla de CABA con otra fuente
   (ConsorcioAbierto, Octopus, IPCBA).
4. **Índice compuesto** (base 100) que combine los dos indicadores, si el usuario lo quiere.
5. Validación cruzada con el informe trimestral de alquileres del IDECBA (Argenprop, $/m²).
6. Variantes: salario neto (~83% del bruto), años de salario para un 2 ambientes de 50 m², Rosario y
   Córdoba (Zonaprop también los publica).

## 5. Rutina mensual

1. `python scripts/actualizar_zonaprop.py` (descubre el informe nuevo, lo baja y extrae; revisar que
   el chequeo no muestre diferencias nuevas fuera de tolerancia).
2. `python scripts/construir.py --refrescar`.
3. `python -m pytest tests -q`; actualizar §1-§2 de este archivo; commit + push si el usuario lo pide.

## 6. PC nueva

`pip install -r requirements.txt` (incluye pypdf y PyMuPDF, solo para leer los PDFs). Los PDFs no se
versionan: `actualizar_zonaprop.py` los vuelve a bajar a `data/cache/zonaprop/` (~150 MB). Para solo
reconstruir el índice alcanza con `construir.py`, que usa `data/reference/zonaprop_valores.csv`.
