# CLAUDE.md — instrucciones para sesiones de Claude en este repo

## Al empezar

1. `git pull` antes de cualquier cambio (el usuario trabaja desde más de una PC).
2. Leer **`ESTADO.md`** (estado, cifras vigentes, próximos pasos, rutina de actualización).
3. Si hay que tocar cálculos: leer **`CONTEXTO.md`** (definiciones, decisiones, fuentes, trampas).
4. Historial de sesiones: `.claude/memory/project.md`.

## Reglas del usuario

- **Commits solo con el usuario (Santiago Riverti). NUNCA agregar `Co-Authored-By: Claude`** ni
  ninguna atribución a Claude en commits o PRs. Commit/push solo cuando el usuario lo pide.
- Idioma: español (rioplatense) en respuestas, commits y documentación.
- El usuario corre los notebooks en **Google Colab** (cada notebook clona el repo desde GitHub: un
  cambio no llega a Colab hasta que se pushea).
- **Cada notebook termina descargando un ZIP con todo** (Excel, gráficos PNG, CSV y LEEME.txt) vía
  `src.exportar.zip_resultados`. Escribe en `_descargas/` (ignorado); no toca `data/processed` ni
  `output/`, que solo actualiza `scripts/construir.py`.

## Reglas técnicas que muerden

- Windows: correr Python con `PYTHONUTF8=1`.
- **Los `.ipynb` se generan con `python scripts/gen_notebooks.py`**: no editarlos a mano ni con
  NotebookEdit. Cambiar el script y regenerar. Se versionan sin outputs.
- **No escribir scripts ni ediciones con heredocs de bash** (rompen `\\` y `\n`). Usar las
  herramientas de archivos o un `.py` aparte.
- **Zonaprop solo publica PDFs.** Los informes viejos no están más en su sitio: se bajan del
  Internet Archive (Wayback). Hay capturas truncadas a 1 MiB (sin `%%EOF`): `zonaprop.descargar`
  las detecta y prueba otras capturas. El sitio de Zonaprop tiene Cloudflare en la API de WordPress:
  **no intentar saltearlo**; solo se piden los PDFs estáticos.
- Los notebooks **no bajan PDFs**: leen `data/reference/zonaprop_valores.csv` (versionado). Para
  sumar un mes: `python scripts/actualizar_zonaprop.py` y después `python scripts/construir.py`.
- Si un informe no aparece solo, se puede agregar a mano en `data/reference/zonaprop_catalogo.csv`
  con `origen=manual` (se respeta al redescubrir).
- La mediana SIPA trae el aguinaldo en junio y diciembre: `indice.sin_aguinaldo` lo saca. No usar la
  serie cruda.
- `data/cache/` guarda las descargas (ignorado). `--refrescar` en construir.py baja todo de nuevo.
- Antes de commitear resultados nuevos: `python -m pytest tests -q`.

## Cierre de sesión

Actualizar `ESTADO.md` (fecha, cobertura, cifras, próximos pasos) y `.claude/memory/project.md`.
Commit + push si el usuario lo pide (si el push pide credenciales, lo hace el usuario: Claude no
ingresa tokens).
