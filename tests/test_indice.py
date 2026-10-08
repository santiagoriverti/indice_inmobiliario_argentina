import numpy as np
import pandas as pd
import pytest

from src import indice


def test_sin_aguinaldo():
    idx = pd.period_range('2025-05', '2026-01', freq='M')
    s = pd.Series([100, 150, 110, 112, 114, 116, 118, 180, 122.0], index=idx)
    guia = pd.Series(np.linspace(1, 1.2, len(idx)), index=idx)
    out = indice.sin_aguinaldo(s, guia)
    assert out[pd.Period('2025-06', 'M')] == pytest.approx(np.sqrt(100 * 110))
    assert out[pd.Period('2025-12', 'M')] == pytest.approx(np.sqrt(118 * 122))
    assert out[pd.Period('2025-07', 'M')] == 110


def test_sin_aguinaldo_ultimo_mes_usa_guia():
    idx = pd.period_range('2026-05', '2026-06', freq='M')
    s = pd.Series([100, 160.0], index=idx)
    guia = pd.Series([200, 210.0], index=idx)
    assert indice.sin_aguinaldo(s, guia).iloc[-1] == pytest.approx(105)


def test_expensas_ancla():
    idx = pd.period_range('2026-05', '2026-07', freq='M')
    series = pd.DataFrame({'ipc_gba_gastos_comunes': [90, 100, 110.0]}, index=idx)
    ancla = pd.DataFrame({'region': ['CABA'], 'periodo': ['2026-06'], 'monto_2amb': [1000]})
    e = indice.expensas(series, ancla)['CABA']
    assert list(e.round(6)) == [900, 1000, 1100]


def test_calcular_ratios():
    p = pd.period_range('2026-01', '2026-01', freq='M')
    zp = pd.DataFrame({'periodo': p, 'region': 'CABA', 'alquiler_2amb': [500.0],
                       'tipo_alquiler': 'publicado', 'venta_usd_m2': [2.0], 'tipo_venta': 'publicado'})
    sal = pd.DataFrame({'mediana': [1000.0], 'ripte': [2000.0]}, index=p)
    exp = pd.DataFrame({'CABA': [100.0]}, index=p)
    tc = pd.DataFrame({'mep': [1000.0], 'oficial': [500.0]}, index=p)
    t = indice.calcular(zp, sal, exp, tc).iloc[0]
    assert t['pct_alquiler_mediana'] == 50 and t['pct_alquiler_expensas_mediana'] == 60
    assert t['salarios_por_m2_mediana_mep'] == 2 and t['salarios_por_m2_ripte_oficial'] == 0.5
