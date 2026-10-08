import re

import numpy as np
import pandas as pd
import pytest

from src import zonaprop as z

# Textos reales de los resumenes (normalizados como los deja texto_pdf)
T_2026 = ('El precio medio de los departamentos en CABA sube 0.2% en agosto y se ubica en USD 2.476 por '
          'm2. En 2026 acumula un incremento de 1.1%. Venta El precio medio sube 1.5% en agosto y acumula '
          '+19.2% en 2026 El alquiler medio de un departamento de 2 ambientes en la ciudad se ubica en '
          '$886.527 por mes, sube 1.5% en agosto. En 2026, el alquiler acumula +19.2%, por debajo de la '
          'inflación (+21.5%). En los últimos 12 meses, el precio medio en CABA sube 29.9%.')
T_2021 = ('El alquiler de un 2 ambientes en la ciudad se ubica en $ 33.357 por mes, 4.9% por encima del '
          'mes previo. En 2021 acumulan suba de 8.7%, levemente por encima de la inflación. VENTA '
          'El recio medio de un departamento en la Ciudad de Buenos Aires se ubica en USD 2.524 por m2, '
          '0.3% por debajo del mes previo. Los precios de venta acumulan baja de 0.8% en 2021 y 9.9% desde '
          'el máximo de 2019. El precio medio hoy es 12% inferior al de un año atrás.')


def _vars(texto, rx, anio):
    m = rx.search(texto)
    return z._entero(m.group(1)), z._variaciones(texto, m, anio)


def test_formato_2026():
    alq, v = _vars(T_2026, z.RX_ALQUILER, 2026)
    assert alq == 886527 and v == {'var_mes': 1.5, 'var_anio': 19.2, 'var_12m': 29.9}
    ven, v = _vars(T_2026, z.RX_VENTA, 2026)
    assert ven == 2476 and v['var_mes'] == 0.2 and v['var_anio'] == 1.1


def test_formato_2021_con_signos():
    alq, v = _vars(T_2021, z.RX_ALQUILER, 2021)
    assert alq == 33357 and v['var_mes'] == 4.9 and v['var_anio'] == 8.7
    ven, v = _vars(T_2021, z.RX_VENTA, 2021)
    assert ven == 2524 and v['var_mes'] == -0.3 and v['var_anio'] == -0.8 and v['var_12m'] == -12.0


@pytest.mark.parametrize('url,esperado', [
    ('https://x/2026/09/INDEX_CABA_REPORTE_2026-08.pdf', ('CABA', '2026-08')),
    ('https://x/2019/10/INDEX-BA-Reporte-Mercado-2019-12.pdf', ('CABA', '2019-12')),
    ('https://x/2019/10/INDEX-GBA-NORTE-Reporte-Mercado-2020-12.pdf', ('GBA_NORTE', '2020-12')),
    ('https://x/2026/08/INDEX_GBA_REPORTE_2026-07.pdf', ('GBA_NORTE', '2026-07')),
    ('https://x/2021/10/INDEX_CABA_REPORTE_2021-10-1.pdf', ('CABA', '2021-10')),
    ('https://x/2019/10/INDEX-GBA-NORTE-Reporte-Mercado-ANEXO-2020-01-1.pdf', None),
    ('https://x/2021/05/INDEX_RSA_REPORTE_2021-04-1.pdf', None),
])
def test_clasificar_url(url, esperado):
    assert z.clasificar_url(url) == esperado


def test_pdf_completo():
    assert z.pdf_completo(b'%PDF-1.7 ... startxref\n123\n%%EOF\n')
    assert not z.pdf_completo(b'%PDF-1.7 ... truncado')


def test_series_deriva_e_interpola():
    # dos informes con un hueco de 3 meses: el de abril deriva marzo (var. mensual)
    val = pd.DataFrame({'region': 'CABA', 'periodo': ['2026-01', '2026-04'],
                        'alquiler_2amb': [100.0, 121.0], 'alquiler_2amb_var_mes': [np.nan, 10.0],
                        'venta_usd_m2': [2000.0, 2000.0]})
    s = z.series(val).set_index('periodo')
    mar = pd.Period('2026-03', 'M')
    assert s.loc[mar, 'alquiler_2amb'] == pytest.approx(110.0)
    assert s.loc[mar, 'tipo_alquiler'] == 'derivado_mes'
    feb = pd.Period('2026-02', 'M')
    assert s.loc[feb, 'tipo_alquiler'] == 'interpolado'
    assert s.loc[feb, 'alquiler_2amb'] == pytest.approx(np.sqrt(100 * 110))
    assert s.loc[feb, 'venta_usd_m2'] == pytest.approx(2000.0)


def test_empalme_por_revision():
    # el informe de mar-2026 (serie revisada) implica dic-2025 = 1600; el de dic-2025 publicaba 1680
    val = pd.DataFrame({'region': 'GBA_OESTE', 'periodo': ['2025-11', '2025-12', '2026-03'],
                        'venta_usd_m2': [1676.0, 1680.0, 1616.0],
                        'venta_usd_m2_var_anio': [np.nan, np.nan, 1.0],
                        'alquiler_2amb': [np.nan, np.nan, np.nan]})
    _, emp = z.chequeos(val)
    assert len(emp) == 1 and emp.iloc[0]['factor'] == pytest.approx(1600 / 1680, abs=1e-4)
    s = z.series(val).set_index('periodo')
    # los informes viejos quedan en la escala nueva
    assert s.loc[pd.Period('2025-12', 'M'), 'venta_usd_m2'] == pytest.approx(1600)
    assert s.loc[pd.Period('2025-11', 'M'), 'venta_usd_m2'] == pytest.approx(1676 * 1600 / 1680)


def test_variacion_real_se_descarta():
    t = ('El alquiler de un 2 ambientes se ubica en $ 800.743 por mes, sube 1.8% en junio. En los '
         'últimos 12 meses, el precio medio de alquiler cae 7.5% en términos reales.')
    _, v = _vars(t, z.RX_ALQUILER, 2026)
    assert v['var_mes'] == 1.8 and v['var_12m'] is None


def test_interpolacion_guiada_empalma_extremos():
    idx = pd.period_range('2026-01', '2026-05', freq='M')
    nivel = pd.Series([100.0, np.nan, np.nan, np.nan, 200.0], index=idx).dropna()
    guia = pd.Series([1.0, 1.5, 1.6, 1.7, 2.0], index=idx)
    s, interp = z._interpolar(nivel, guia)
    assert s.iloc[0] == pytest.approx(100) and s.iloc[-1] == pytest.approx(200)
    # la guia sube 2x igual que el nivel: el hueco copia la guia
    assert s.iloc[1] == pytest.approx(150) and interp.sum() == 3
