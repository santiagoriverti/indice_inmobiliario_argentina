# CLAUDE.md — instrucciones para sesiones de Claude en este repo

## Al empezar

1. `git pull` antes de cualquier cambio (el usuario trabaja desde más de una PC).
2. Leer **`ESTADO.md`** (estado, cifras vigentes, dónde se citan, próximos pasos, rutina, PC nueva).
3. Si hay que tocar cálculos: leer **`CONTEXTO.md`** (definiciones, decisiones, fuentes, trampas,
   versión definitiva y mapa del código).
4. Historial de sesiones: `.claude/memory/project.md`.

Contexto clave: **Zonaprop es una prueba piloto**. La versión definitiva usará un relevamiento propio
de INECO (convenios con portales o *web scraping*), todavía no implementado (CONTEXTO §5).

## Reglas del usuario

- **Commits solo con el usuario (Santiago Riverti). NUNCA agregar `Co-Authored-By: Claude`** ni
  ninguna atribución a Claude en commits o PRs. Commit/push solo cuando el usuario lo pide.
- Idioma: español (rioplatense) en respuestas, commits y documentación.
- El usuario corre los notebooks en **Google Colab** (cada notebook clona el repo desde GitHub: un
  cambio no llega a Colab hasta que se pushea).
- **Cada notebook termina descargando un ZIP con todo** (Excel, gráficos PNG, CSV y LEEME.txt) vía
  `src.exportar.zip_resultados`. Escribe en `_descargas/` (ignorado); no toca `data/processed` ni
  `output/`, que solo actualiza `scripts/construir.py`.
- Cuando el usuario pasa un ZIP de Colab: `python scripts/comparar_zip.py <zip>`. Esperable: solo
  difiere la fila del mes en curso de `tipo_de_cambio.csv` (promedio parcial del dólar) y, si Colab
  bajó datos más nuevos, filas "solo en el ZIP". Chequear la "Version del repo" que imprime.
- `docs/informe_indicadores/seccion_inmobiliario.tex` es la sección del informe INECO "Propuesta de
  Indicadores Económicos" (el documento completo está en el Overleaf del usuario; las figuras G01 y
  G03 van en su carpeta `figuras/`). La metodología es **genérica** (relevamiento propio) y las
  cifras de Zonaprop van como "resultados preliminares". Si cambian las cifras, actualizar todos los
  documentos de la tabla de `ESTADO.md` §3 y recompilar (abajo).
- **Cifras citadas = las que salen de `data/processed/` / `construir.py`.** Verificar cada número y
  cada redondeo contra los datos antes de escribirlo (en la sesión 1 hubo que corregir la sección por
  frases que no coincidían exactamente con lo que mide cada columna).

## Reglas técnicas que muerden

- Windows: correr Python con `PYTHONUTF8=1`.
- **Los `.ipynb` se generan con `python scripts/gen_notebooks.py`**: no editarlos a mano ni con
  NotebookEdit. Cambiar el script y regenerar. Se versionan sin outputs.
- **No escribir scripts ni ediciones con heredocs de bash** (rompen `\\` y `\n`). Usar las
  herramientas de archivos o un `.py` aparte.
- Para probar el notebook sin ensuciar el del repo: copiarlo a `_local_run/` (ignorado) y correr
  `python -m jupyter nbconvert --to notebook --execute --inplace _local_run/01_indice_inmobiliario.ipynb`.
- La celda de configuración del notebook hace `git fetch` + `reset --hard` y borra `src.*` de
  `sys.modules` (Colab reutiliza sesiones con módulos viejos). Mantenerlo así.
- `src/graficos.py` **no debe forzar** `matplotlib.use('Agg')` (apaga los gráficos del notebook):
  solo `scripts/construir.py` fija el backend.
- **Zonaprop solo publica PDFs.** Los informes viejos no están más en su sitio: se bajan del
  Internet Archive (Wayback). Hay capturas truncadas a 1 MiB: `zonaprop.descargar` prueba otras
  capturas y, si no hay completa, guarda `.parcial.pdf`, que se lee con PyMuPDF `get_texttrace`
  (el `get_text` común une dígitos repetidos). El sitio de Zonaprop tiene Cloudflare en la API de
  WordPress: **no intentar saltearlo**; solo se piden los PDFs estáticos.
- **Web scraping** (relevamiento propio): solo con convenio o respetando términos de uso y
  `robots.txt`; nunca saltear protecciones anti-bot. Los PDFs y datos crudos de terceros no se
  versionan (el repo es **público**); tampoco tokens ni credenciales.
- Los notebooks **no bajan PDFs**: leen `data/reference/zonaprop_valores.csv` (versionado). Para
  sumar un mes: `python scripts/actualizar_zonaprop.py` y después `python scripts/construir.py`.
- Si un informe no aparece solo, se puede agregar a mano en `data/reference/zonaprop_catalogo.csv`
  con `origen=manual` (y `wayback_ts` si es una copia del Internet Archive); se respeta al redescubrir.
- Las cifras extraídas se validan con `zonaprop.chequeos()` (lo imprime `actualizar_zonaprop.py`):
  niveles derivados de variaciones vs. publicados y empalmes por revisión de Zonaprop. Un empalme
  nuevo o una diferencia > 0,3% hay que mirarlos a mano antes de aceptar los datos.
- La mediana SIPA trae el aguinaldo en junio y diciembre: `indice.sin_aguinaldo` lo saca. No usar la
  serie cruda.
- `data/cache/` guarda las descargas (ignorado). `--refrescar` en construir.py baja todo de nuevo.
- Antes de commitear resultados nuevos: `python -m pytest tests -q` (18 passed).
- Sección LaTeX: en esta PC hay MiKTeX. Para probarla, copiar el `.tex` y las figuras a una carpeta
  temporal con un documento mínimo con el preámbulo del informe (`\input{seccion_inmobiliario}`) y
  correr `pdflatex -interaction=nonstopmode` dos veces; revisar que no haya errores ni referencias
  indefinidas.

## Cierre de sesión

Actualizar `ESTADO.md` (fecha, cobertura, cifras, verificación, próximos pasos) y
`.claude/memory/project.md`. Commit + push si el usuario lo pide (si el push pide credenciales, lo
hace el usuario: Claude no ingresa tokens).
