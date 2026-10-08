"""Zonaprop Index: catalogo de informes PDF, descarga y extraccion de las cifras principales.

Zonaprop publica un informe mensual por region (CABA, GBA Norte, GBA Oeste, GBA Sur) solo en PDF.
Los informes viejos ya no estan en su sitio: se recuperan del Internet Archive (Wayback Machine).

Flujo (lo corre `scripts/actualizar_zonaprop.py`):
1. `descubrir()` arma el catalogo (region, periodo, url) con la API CDX del Wayback y probando las
   URLs actuales del sitio -> `data/reference/zonaprop_catalogo.csv` (versionado, editable a mano).
2. `descargar()` baja cada PDF a `data/cache/zonaprop/` (ignorado por git).
3. `extraer()` lee el texto del PDF y saca precio de venta USD/m2, alquiler de 2 ambientes y sus
   variaciones -> `data/reference/zonaprop_valores.csv` (versionado: los notebooks no bajan PDFs).
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from . import fuentes

REGIONES = ['CABA', 'GBA_NORTE', 'GBA_OESTE', 'GBA_SUR']
CATALOGO = fuentes.REFERENCIA / 'zonaprop_catalogo.csv'
VALORES = fuentes.REFERENCIA / 'zonaprop_valores.csv'
DIR_PDF = fuentes.CACHE / 'zonaprop'

SITIO = 'https://www.zonaprop.com.ar/blog/wp-content/uploads/{carpeta}/{nombre}'
CDX = 'http://web.archive.org/cdx/search/cdx'
PREFIJOS_CDX = ['zonaprop.com.ar/noticias/wp-content/uploads/',
                'zonaprop.com.ar/blog/wp-content/uploads/']
WAYBACK = 'https://web.archive.org/web/{ts}id_/{url}'

# INDEX_CABA_REPORTE_2026-08.pdf, INDEX-BA-Reporte-Mercado-2019-10.pdf,
# INDEX-GBA-NORTE-Reporte-Mercado-2020-12.pdf, INDEX_GBA_REPORTE_2026-07.pdf (= GBA Norte)
_RE_NOMBRE = re.compile(
    r'INDEX[_-](?P<reg>CABA|BA|GBA[_-]NORTE|GBA[_-]OESTE|GBA[_-]SUR|GBA)[_-]'
    r'(?:REPORTE|Reporte[_-]Mercado)[_-](?P<anio>20\d\d)-(?P<mes>\d\d)', re.IGNORECASE)
_REG_NOMBRE = {'CABA': 'CABA', 'BA': 'CABA', 'GBA_NORTE': 'GBA_NORTE', 'GBA': 'GBA_NORTE',
               'GBA_OESTE': 'GBA_OESTE', 'GBA_SUR': 'GBA_SUR'}


def clasificar_url(url: str) -> tuple[str, str] | None:
    """(region, 'AAAA-MM') a partir del nombre del archivo, o None si no es un informe mensual."""
    nombre = url.rsplit('/', 1)[-1]
    if 'anexo' in nombre.lower():
        return None
    m = _RE_NOMBRE.search(nombre)
    if not m:
        return None
    reg = _REG_NOMBRE[m['reg'].upper().replace('-', '_')]
    return reg, f"{m['anio']}-{m['mes']}"


# ---------------------------------------------------------------- 1. catalogo

def _cdx(prefijo: str, match: str = 'prefix') -> pd.DataFrame:
    """Capturas del Wayback (sin colapsar: hay capturas truncadas a 1 MiB y conviene la ultima)."""
    params = {'url': prefijo, 'matchType': match, 'filter': ['mimetype:application/pdf',
              'statuscode:200'], 'fl': 'timestamp,original', 'limit': 50000}
    for i in range(3):
        try:
            r = requests.get(CDX, params=params, headers=fuentes.HEADERS, timeout=120)
            if r.ok and not r.text.lstrip().startswith('<'):
                break
        except requests.RequestException:
            pass
        print(f'  CDX sin respuesta ({prefijo}), reintento {i + 1}', flush=True)
        time.sleep(15 * (i + 1))
    else:
        raise RuntimeError(f'El CDX del Wayback no respondio para {prefijo}')
    filas = [ln.split(' ', 1) for ln in r.text.splitlines() if ln.strip()]
    return pd.DataFrame(filas, columns=['ts', 'original'])


def catalogo_wayback() -> pd.DataFrame:
    filas = []
    for pref in PREFIJOS_CDX:
        cap = _cdx(pref).sort_values('ts').drop_duplicates('original', keep='last')
        for ts, url in cap.itertuples(index=False):
            c = clasificar_url(url)
            if c:
                filas.append({'region': c[0], 'periodo': c[1], 'url': url, 'origen': 'wayback',
                              'wayback_ts': ts})
        print(f'  wayback {pref}: {len(filas)} informes acumulados', flush=True)
    return pd.DataFrame(filas, columns=['region', 'periodo', 'url', 'origen', 'wayback_ts'])


def _existe(url: str) -> bool:
    try:
        r = requests.head(url, headers=fuentes.HEADERS, timeout=30, allow_redirects=False)
    except requests.RequestException:
        return False
    return r.status_code == 200 and 'pdf' in r.headers.get('Content-Type', '')


def _buscar_en_sitio(reg: str, p: pd.Period) -> str | None:
    nombres = [f'INDEX_{reg}_REPORTE_{p}{suf}.pdf' for suf in ('', '-1', '-2')]
    if reg == 'GBA_NORTE':
        nombres.append(f'INDEX_GBA_REPORTE_{p}.pdf')
    for desfase in (1, 0, 2):
        carpeta = (p + desfase).strftime('%Y/%m')
        for nombre in nombres:
            url = SITIO.format(carpeta=carpeta, nombre=nombre)
            if _existe(url):
                return url
    return None


def catalogo_sitio(desde: str, hasta: str, faltantes: set[tuple[str, str]] | None = None,
                   hilos: int = 6) -> pd.DataFrame:
    """Prueba las URLs actuales (carpeta = mes del informe +1, +0 o +2; sufijos '', -1, -2)."""
    from concurrent.futures import ThreadPoolExecutor

    tareas = [(reg, p) for p in pd.period_range(desde, hasta, freq='M') for reg in REGIONES
              if faltantes is None or (reg, str(p)) in faltantes]
    with ThreadPoolExecutor(hilos) as ex:
        urls = list(ex.map(lambda t: _buscar_en_sitio(*t), tareas))
    filas = [{'region': reg, 'periodo': str(p), 'url': u, 'origen': 'sitio', 'wayback_ts': ''}
             for (reg, p), u in zip(tareas, urls) if u]
    print(f'  sitio: {len(filas)} de {len(tareas)} informes probados', flush=True)
    return pd.DataFrame(filas, columns=['region', 'periodo', 'url', 'origen', 'wayback_ts'])


def descubrir(desde_sitio: str = '2024-01', hasta: str | None = None) -> pd.DataFrame:
    """Une Wayback + sitio (el sitio solo para los meses que el Wayback no tiene). Prioriza el
    sitio; entre copias del Wayback, la mas reciente. Conserva filas cargadas a mano (origen
    'manual') del catalogo existente."""
    hasta = hasta or str(pd.Period.now('M') - 1)
    wb = catalogo_wayback()
    todos = {(r, str(p)) for p in pd.period_range(desde_sitio, hasta, freq='M') for r in REGIONES}
    tiene = set(zip(wb['region'], wb['periodo'])) if len(wb) else set()
    sitio = catalogo_sitio(desde_sitio, hasta, todos - tiene)
    partes = [sitio, wb]
    if CATALOGO.exists():
        viejo = pd.read_csv(CATALOGO, dtype=str).fillna('')
        partes.append(viejo[viejo['origen'] == 'manual'])
    cat = pd.concat(partes, ignore_index=True)
    orden = {'manual': 0, 'sitio': 1, 'wayback': 2}
    cat['_o'] = cat['origen'].map(orden)
    cat = (cat.sort_values(['region', 'periodo', '_o', 'wayback_ts'], ascending=[True, True, True, False])
              .drop_duplicates(['region', 'periodo']).drop(columns='_o'))
    return cat.reset_index(drop=True)


# ---------------------------------------------------------------- 2. descarga

def ruta_pdf(region: str, periodo: str, parcial: bool = False) -> Path:
    return DIR_PDF / f'{region}_{periodo}{".parcial" if parcial else ""}.pdf'


def url_descarga(fila) -> str:
    """Con `wayback_ts` (origen wayback, o manual con captura) baja la copia del Internet Archive."""
    if str(fila.get('wayback_ts', '') or '').strip():
        return WAYBACK.format(ts=fila['wayback_ts'], url=fila['url'])
    return fila['url']


def pdf_completo(contenido: bytes) -> bool:
    """El Wayback guarda algunas capturas truncadas a 1 MiB (sin %%EOF): no se pueden leer."""
    return contenido[:4] == b'%PDF' and b'%%EOF' in contenido[-2048:]


def _bajar(url: str) -> bytes | None:
    """Contenido del PDF (completo o truncado) o None si no es un PDF."""
    try:
        r = requests.get(url, headers=fuentes.HEADERS, timeout=180)
    except requests.RequestException:
        return None
    return r.content if r.ok and r.content[:4] == b'%PDF' else None


def descargar(cat: pd.DataFrame, pausa: float = 1.5) -> list[str]:
    """Baja los PDFs que falten en el cache. Si la captura del Wayback esta truncada, prueba las
    demas capturas de esa URL; si ninguna esta completa, guarda la truncada mas larga como
    `<region>_<periodo>.parcial.pdf` (se lee con PyMuPDF). Devuelve los que no estan completos."""
    DIR_PDF.mkdir(parents=True, exist_ok=True)
    fallas = []
    for _, f in cat.iterrows():
        destino = ruta_pdf(f['region'], f['periodo'])
        parcial = ruta_pdf(f['region'], f['periodo'], parcial=True)
        if destino.exists() and pdf_completo(destino.read_bytes()):
            continue
        if parcial.exists():
            fallas.append(f"{f['region']} {f['periodo']} (parcial)")
            continue
        contenido = _bajar(url_descarga(f))
        mejor = contenido
        if (contenido is None or not pdf_completo(contenido)) and str(f.get('wayback_ts', '') or '').strip():
            otras = _cdx(f['url'], match='exact').sort_values('ts', ascending=False)
            for ts in otras['ts']:
                if ts == f['wayback_ts']:
                    continue
                time.sleep(pausa)
                c = _bajar(WAYBACK.format(ts=ts, url=f['url']))
                if c and pdf_completo(c):
                    mejor = c
                    break
                if c and (mejor is None or len(c) > len(mejor)):
                    mejor = c
        if mejor and pdf_completo(mejor):
            destino.write_bytes(mejor)
            print(f"  bajado {f['region']} {f['periodo']}", flush=True)
        elif mejor:
            parcial.write_bytes(mejor)
            fallas.append(f"{f['region']} {f['periodo']} (parcial)")
            print(f"  PARCIAL {f['region']} {f['periodo']}", flush=True)
        else:
            fallas.append(f"{f['region']} {f['periodo']}")
            print(f"  FALLA {f['region']} {f['periodo']}", flush=True)
        time.sleep(pausa)
    return fallas


# ---------------------------------------------------------------- 3. extraccion

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre',
         'octubre', 'noviembre', 'diciembre']
_MES = '(?:' + '|'.join(MESES + ['setiembre']) + ')'
_NUM = r'(\d+(?:[.,]\d+)?)'
_NEG = ('baja', 'cae', 'caída', 'caida', 'retrocede', 'retroceso', 'desciende', 'descenso',
        'se reduce', 'reducción', 'debajo', 'abajo', 'inferior', 'disminuye')

# niveles: primer match en las paginas de resumen
RX_ALQUILER = re.compile(r'(?:2|dos)\s+ambientes[^$]{0,120}?\$\s?(\d{1,3}(?:[.,]\d{3})+)\s*'
                         r'(?:por\s+mes|mensuales|/\s*mes|al\s+mes)', re.IGNORECASE)
_M2 = r'm(?:\s?2|²)'
RX_VENTA = re.compile(r'USD\s?(\d{1,2}[.,]\d{3}|\d{3,5})\s*(?:por\s+' + _M2 + r'|/\s*' + _M2 + r'|el\s+'
                      + _M2 + r'|por\s+metro)|(\d{1,2}[.,]\d{3})\s*usd\s*/\s*' + _M2,  # 2019: "2.557 usd/m2"
                      re.IGNORECASE)
# variaciones (se toma la mas cercana al nivel, dentro de una ventana)
RX_MES = [
    re.compile(r'(sube|baja|cae|aumenta|crece|retrocede|desciende|se\s+incrementa|se\s+reduce|'
               r'disminuye)\s+(?:un\s+)?' + _NUM + r'\s*%\s+(?:en\s+(?:el\s+mes|' + _MES +
               r')|mensual|respecto\s+(?:al|del)\s+mes|frente\s+al\s+mes)', re.IGNORECASE),
    re.compile(_NUM + r'\s*%\s+por\s+(encima|debajo|arriba|abajo)\s+del?\s+(?:lo\s+registrado\s+'
               r'(?:en\s+)?el\s+)?mes\s+(?:previo|anterior)', re.IGNORECASE),
    re.compile(r'(suba|baja|caída|caida|aumento|incremento)\s+mensual\s+de(?:l)?\s+' + _NUM + r'\s*%',
               re.IGNORECASE),
    re.compile(r'(suba|baja|caída|caida|aumento|incremento|alza)\s+de\s+' + _NUM + r'\s*%\s+(?:respecto|'
               r'frente|en\s+relación)\s+al\s+mes', re.IGNORECASE),
]
# "cae 7.5% en terminos reales", "caida real de": variaciones deflactadas, no sirven para derivar
RX_REAL = re.compile(r'\s*(?:en\s+)?(?:términos\s+reales|real\b)', re.IGNORECASE)
RX_ESTABLE = re.compile(r'(?:se\s+mantiene|permanece|se\s+mantuvo|se\s+mantienen|se\s+mantuvieron)'
                        r'\s+estables?', re.IGNORECASE)
RX_ANIO = [
    re.compile(r'en\s+(20\d\d),?\s+(?:el\s+\w+\s+|los\s+precios\s+(?:de\s+\w+\s+)?)?acumulan?\s+'
               r'(?:un[a]?\s+)?(incremento|suba|aumento|alza|baja|caída|caida|descenso|retroceso)?'
               r'\s*(?:de\s+)?\+?' + _NUM + r'\s*%', re.IGNORECASE),
    re.compile(r'acumulan?\s+(?:un[a]?\s+)?(incremento|suba|aumento|alza|baja|caída|caida|descenso|'
               r'retroceso)?\s*(?:de\s+)?\+?' + _NUM + r'\s*%\s+en\s+(?:el\s+año\s+|lo\s+que\s+va\s+'
               r'de\s+)?(20\d\d)', re.IGNORECASE),
]
RX_12M = [
    re.compile(r'(?:últimos\s+12\s+meses|último\s+año|interanual(?:mente)?)[,]?\s+[^%]{0,60}?'
               r'(sube|baja|cae|aumenta|crece|retrocede)\s+(?:un\s+)?' + _NUM + r'\s*%', re.IGNORECASE),
    re.compile(r'(sube|baja|cae|aumenta|crece|retrocede)\s+(?:un\s+)?' + _NUM +
               r'\s*%\s+(?:interanual|en\s+los\s+últimos\s+12\s+meses|en\s+el\s+último\s+año)',
               re.IGNORECASE),
    re.compile(_NUM + r'\s*%\s+(inferior|superior)\s+al\s+de\s+un\s+año\s+atrás', re.IGNORECASE),
]


def _pct(signo_texto: str | None, numero: str) -> float:
    x = float(numero.replace(',', '.'))
    if signo_texto and any(n in signo_texto.lower() for n in _NEG):
        x = -x
    return x


def _entero(s: str) -> int:
    return int(re.sub(r'[.,\s]', '', s))


def _normalizar(t: str) -> str:
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'(?<=\d) ?\. ?(?=\d)', '.', t)           # "33 . 357" -> "33.357"
    t = re.sub(r'(?<=\d) ?, ?(?=\d{3}(?!\d))', ',', t)  # coma solo como separador de miles
    t = re.sub(r'(?<=\d) (?=%)', '', t)                 # "8.7 %" -> "8.7%"
    return t.strip()


def texto_pdf(ruta: Path, paginas: int | None = None, motor: str = 'pypdf') -> list[str]:
    """Texto por pagina, con los espacios normalizados.

    - `pypdf`: el default para PDFs completos.
    - `mupdf`: PyMuPDF `get_text`. Lee el texto de los informes 2022-2024 que pypdf no ve.
    - `traza`: PyMuPDF `get_texttrace` (glifos tal como se dibujan). Para PDFs truncados: ahi
      `get_text` une digitos repetidos porque faltan las fuentes ("33.357" -> "3.357").
    """
    if motor == 'pypdf':
        import logging

        from pypdf import PdfReader

        logging.getLogger('pypdf').setLevel(logging.ERROR)  # "Ignoring wrong pointing object"
        r = PdfReader(str(ruta))
        pags = r.pages if paginas is None else r.pages[:paginas]
        return [re.sub(r'\s+', ' ', (p.extract_text() or '')).strip() for p in pags]

    import pymupdf

    pymupdf.TOOLS.mupdf_display_errors(False)
    doc = pymupdf.open(str(ruta))
    n = doc.page_count if paginas is None else min(paginas, doc.page_count)
    pags = []
    for i in range(n):
        try:
            if motor == 'traza':
                t = ' '.join(''.join(chr(c[0]) for c in s['chars']) for s in doc[i].get_texttrace())
            else:
                t = doc[i].get_text()
        except Exception:  # noqa: BLE001 - pagina fuera de la parte descargada
            t = ''
        pags.append(_normalizar(t))
    return pags


def _cercana(texto: str, ini: int, fin: int, patrones, conv, antes: int, despues: int):
    """Variacion cuyo match esta mas cerca del tramo [ini, fin) dentro de la ventana."""
    a, b = max(0, ini - antes), min(len(texto), fin + despues)
    mejor = None
    for rx in patrones:
        for m in rx.finditer(texto, a, b):
            if RX_REAL.match(texto, m.end()):
                continue
            dist = ini - m.end() if m.end() <= ini else max(0, m.start() - fin)
            val = conv(m)
            if val is not None and (mejor is None or dist < mejor[0]):
                mejor = (dist, val)
    return None if mejor is None else mejor[1]


def _conv_mes(m):
    g = m.groups()
    if g[0] and not re.match(r'\d', g[0]):   # (verbo, numero)
        return _pct(g[0], g[1])
    return _pct(g[1], g[0])                  # (numero, encima/debajo)


def _variaciones(texto: str, m: re.Match, anio: int) -> dict:
    ini, fin = m.start(), m.end()
    var_mes = _cercana(texto, ini, fin, RX_MES, _conv_mes, 160, 220)
    if var_mes is None:
        est = [e for e in RX_ESTABLE.finditer(texto, max(0, ini - 80), min(len(texto), fin + 80))]
        var_mes = 0.0 if est else None

    def conv_anio(mm):
        g = mm.groups()
        if re.fullmatch(r'20\d\d', g[0] or ''):
            a, verbo, num = g
        else:
            verbo, num, a = g
        return _pct(verbo, num) if int(a) == anio else None

    def conv_12m(mm):
        g = mm.groups()
        if re.match(r'\d', g[0]):
            return _pct(g[1], g[0])
        return _pct(g[0], g[1])

    return {'var_mes': var_mes,
            'var_anio': _cercana(texto, ini, fin, RX_ANIO, conv_anio, 120, 260),
            'var_12m': _cercana(texto, ini, fin, RX_12M, conv_12m, 60, 400)}


RX_TITULO = re.compile(_MES + r'\s+(?:de\s+)?(20\d\d)', re.IGNORECASE)


def extraer(ruta: Path, periodo: str) -> dict:
    """Cifras principales de un informe. Busca primero en las 3 primeras paginas (portada y
    resumen) y despues en todo el PDF, probando los motores de texto en orden (pypdf, PyMuPDF;
    para PDFs truncados solo la traza de PyMuPDF). `*_donde` = motor:lugar del hallazgo."""
    anio = int(periodo[:4])
    motores = ['traza'] if ruta.name.endswith('.parcial.pdf') else ['pypdf', 'mupdf']
    textos: dict[str, list[str]] = {}
    out: dict = {}
    for var, rx in (('alquiler_2amb', RX_ALQUILER), ('venta_usd_m2', RX_VENTA)):
        hallado = False
        for lugar in ('resumen', 'completo'):
            for motor in motores:
                if motor not in textos:
                    textos[motor] = texto_pdf(ruta, motor=motor)
                pags = textos[motor]
                texto = ' '.join(pags[:3] if lugar == 'resumen' else pags)
                m = rx.search(texto)
                if m:
                    out[var] = _entero(next(g for g in m.groups() if g))
                    out[f'{var}_donde'] = f'{motor}:{lugar}'
                    for k, v in _variaciones(texto, m, anio).items():
                        out[f'{var}_{k}'] = v
                    hallado = True
                    break
            if hallado:
                break
    pags = next(iter(textos.values()), [])
    out['paginas'] = len(pags)
    for p in [pags[0]] if pags else []:
        t = RX_TITULO.search(p) or RX_TITULO.search(' '.join(textos.get('mupdf', [''])[:1]))
        if t:
            mes = MESES.index(t.group(0).split()[0].lower().replace('setiembre', 'septiembre')) + 1
            out['periodo_portada'] = f'{t.group(1)}-{mes:02d}'
    return out


def extraer_todo(cat: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for _, f in cat.sort_values(['region', 'periodo']).iterrows():
        ruta = ruta_pdf(f['region'], f['periodo'])
        if not ruta.exists():
            ruta = ruta_pdf(f['region'], f['periodo'], parcial=True)
        fila = {'region': f['region'], 'periodo': f['periodo'],
                'pdf': 'parcial' if ruta.name.endswith('.parcial.pdf') else 'completo'}
        if ruta.exists():
            try:
                fila.update(extraer(ruta, f['periodo']))
            except Exception as e:  # noqa: BLE001 - un PDF roto no debe frenar el resto
                fila['error'] = f'{type(e).__name__}: {e}'
        else:
            fila['error'] = 'sin PDF'
        filas.append(fila)
    cols = ['region', 'periodo', 'periodo_portada', 'pdf', 'paginas']
    for var in VARIABLES:
        cols += [var, f'{var}_var_mes', f'{var}_var_anio', f'{var}_var_12m', f'{var}_donde']
    cols.append('error')
    return pd.DataFrame(filas).reindex(columns=cols)


def chequeos(valores: pd.DataFrame, tolerancia: float = 0.3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(comparaciones, empalmes). Comparaciones: cada nivel derivado (de una variacion) vs el
    nivel publicado de ese mismo mes, ya empalmados; una diferencia mayor a `tolerancia` (%)
    indica una variacion mal leida o una revision no empalmada. Empalmes: revisiones detectadas."""
    filas, emps = [], []
    for reg, v in valores.groupby('region'):
        v = v.set_index(pd.PeriodIndex(v['periodo'], freq='M')).sort_index()
        for var in VARIABLES:
            c = _candidatos(v, var)
            if c.empty:
                continue
            c, e = _empalmar(c)
            emps += [{'region': reg, 'variable': var, **x} for x in e]
            pub = c[c['tipo'] == 'publicado'].groupby('periodo')['valor'].first()
            der = c[c['tipo'].str.startswith('derivado') & c['periodo'].isin(pub.index)]
            for _, d in der.iterrows():
                dif = 100 * (d['valor'] / pub[d['periodo']] - 1)
                filas.append({'region': reg, 'variable': var, 'periodo': str(d['periodo']),
                              'tipo': d['tipo'], 'informe': str(d['informe']),
                              'publicado': round(pub[d['periodo']], 1),
                              'derivado': round(d['valor'], 1), 'dif_pct': round(dif, 2),
                              'ok': abs(dif) <= tolerancia})
    return pd.DataFrame(filas), pd.DataFrame(emps)


# ---------------------------------------------------------------- 4. series mensuales

VARIABLES = ['alquiler_2amb', 'venta_usd_m2']
# prioridad de cada fuente de un nivel mensual (menor = mejor). Un nivel hallado fuera del
# resumen (`publicado_completo`) es menos confiable que uno derivado: puede ser de otro cuadro.
_PRIORIDAD = {'publicado': 0, 'derivado_mes': 1, 'derivado_12m': 2, 'derivado_anio': 3,
              'publicado_completo': 4}
TOL_EMPALME = 1.0     # % de diferencia a partir del cual un solapamiento indica revision de la serie
MAX_EMPALME = 15.0    # % maximo: mas que esto es una cifra mal leida, no una revision


def _candidatos(v: pd.DataFrame, var: str) -> pd.DataFrame:
    """Niveles publicados y derivados de las variaciones que trae cada informe:
    L(t-1) = L(t) / (1 + var. mensual); L(t-12) = L(t) / (1 + var. 12 meses);
    L(dic del anio anterior) = L(t) / (1 + var. acumulada en el anio). `informe` = mes del PDF."""
    filas = []
    for p, f in v.iterrows():
        nivel = f.get(var)
        if pd.isna(nivel):
            continue
        donde = str(f.get(f'{var}_donde', 'resumen'))
        filas.append((p, 'publicado' if donde.endswith('resumen') else 'publicado_completo', nivel, p))
        for col, destino, tipo in ((f'{var}_var_mes', p - 1, 'derivado_mes'),
                                   (f'{var}_var_12m', p - 12, 'derivado_12m'),
                                   (f'{var}_var_anio', pd.Period(f'{p.year - 1}-12', 'M'),
                                    'derivado_anio')):
            x = f.get(col)
            if pd.notna(x):
                filas.append((destino, tipo, nivel / (1 + x / 100), p))
    c = pd.DataFrame(filas, columns=['periodo', 'tipo', 'valor', 'informe'])
    c['prioridad'] = c['tipo'].map(_PRIORIDAD)
    return c


def _empalmar(c: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Lleva todos los informes a la escala del mas reciente (Zonaprop revisa series: p. ej. GBA
    Oeste bajo ~4% su nivel entre los informes de ene y mar-2026).

    Recorre los informes del mas nuevo al mas viejo. Si los niveles de un informe se solapan con los
    ya aceptados y difieren (mediana) entre TOL_EMPALME y MAX_EMPALME %, de manera consistente, ese
    informe y todos los anteriores se reescalan por ese cociente. Devuelve los candidatos
    reescalados y la lista de empalmes aplicados."""
    aceptados: dict = {}
    factor, empalmes, salida = 1.0, [], []
    for inf in sorted(c['informe'].unique(), reverse=True):
        d = c[c['informe'] == inf].copy()
        d['valor'] *= factor
        solape = [aceptados[q] / x for q, x in zip(d['periodo'], d['valor']) if q in aceptados]
        if solape:
            r = float(np.median(solape))
            dif = abs(r - 1) * 100
            consistente = all(abs(s / r - 1) * 100 < TOL_EMPALME / 2 for s in solape)
            if TOL_EMPALME < dif <= MAX_EMPALME and consistente:
                factor *= r
                d['valor'] *= r
                empalmes.append({'informe': str(inf), 'factor': round(r, 4), 'solapes': len(solape)})
        for q, x in zip(d['periodo'], d['valor']):
            aceptados.setdefault(q, x)
        salida.append(d)
    return pd.concat(salida, ignore_index=True), empalmes


def _interpolar(s: pd.Series, guia: pd.Series | None) -> tuple[pd.Series, pd.Series]:
    """Completa los huecos internos en logaritmos. Con `guia` (un indice de precios), el hueco
    sigue la trayectoria de la guia corregida linealmente para empalmar en ambos extremos; sin
    guia (o si le faltan datos en el tramo), interpolacion log-lineal."""
    idx = pd.period_range(s.index.min(), s.index.max(), freq='M')
    s = s.reindex(idx)
    interp = s.isna()
    ls = np.log(s)
    conocidos = ls.dropna()
    for a, b in zip(conocidos.index[:-1], conocidos.index[1:]):
        n = (b - a).n
        if n <= 1:
            continue
        tramo = pd.period_range(a, b, freq='M')
        pasos = np.arange(n + 1) / n
        g = guia.reindex(tramo) if guia is not None else None
        if g is not None and g.notna().all():
            lg = np.log(g.to_numpy())
            camino = ls[a] + (lg - lg[0]) + pasos * ((ls[b] - ls[a]) - (lg[-1] - lg[0]))
        else:
            camino = ls[a] + pasos * (ls[b] - ls[a])
        ls[tramo[1:-1]] = camino[1:-1]
    return np.exp(ls), interp


def series(valores: pd.DataFrame, guia_alquiler: pd.Series | None = None) -> pd.DataFrame:
    """Niveles mensuales por region (tabla larga) con el origen de cada dato en `tipo_*`:
    publicado, derivado_mes / derivado_12m / derivado_anio, o interpolado."""
    salida = []
    for reg, v in valores.groupby('region'):
        v = v.set_index(pd.PeriodIndex(v['periodo'], freq='M')).sort_index()
        d = {}
        for var in VARIABLES:
            c = _candidatos(v, var)
            if c.empty:
                continue
            c, _ = _empalmar(c)
            mejor = c[c['prioridad'] == c.groupby('periodo')['prioridad'].transform('min')]
            nivel = mejor.groupby('periodo')['valor'].mean()
            tipo = mejor.groupby('periodo')['tipo'].first()
            guia = guia_alquiler if var == 'alquiler_2amb' else None
            completo, interp = _interpolar(nivel, guia)
            tipo = tipo.reindex(completo.index)
            tipo[interp.to_numpy()] = 'interpolado'
            nombre = 'alquiler' if var == 'alquiler_2amb' else 'venta'
            d[var] = completo
            d[f'tipo_{nombre}'] = tipo
        df = pd.DataFrame(d)
        df.index.name = 'periodo'
        df['region'] = reg
        salida.append(df.reset_index())
    return pd.concat(salida, ignore_index=True)
