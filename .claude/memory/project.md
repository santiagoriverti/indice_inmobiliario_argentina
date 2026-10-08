# Historial de sesiones — indice_inmobiliario_argentina

## Sesión 1 — 2026-10-07: arranque del proyecto

- Objetivo del usuario: índice inmobiliario que refleje el costo de alquilar + expensas respecto del
  salario y la cantidad de salarios para comprar un m².
- Decisiones (AskUserQuestion): CABA + GBA (Norte/Oeste/Sur) · mediana SIPA + RIPTE · MEP + oficial
  como sensibilidad · expensas = ancla + índice.
- Cambio respecto de lo elegido: el IPCBA no tiene la apertura de expensas por API → se usa el IPC
  GBA de INDEC "Reparaciones y gastos comunes de la vivienda" (`104.1_I2C_2016_M_42`). Avisar al
  usuario (hecho en el resumen de la sesión).
- Zonaprop: solo PDFs; la API de WordPress tiene Cloudflare (no se saltea). Los informes viejos
  salen del Wayback (CDX). Capturas truncadas a 1 MiB → probar otras capturas.
- Ancla de expensas: Propio jun-2026, mediana 2 amb $171.545 ($3.995/m²) en avisos de alquiler CABA
  (vía iProfesional 01-09-2026). Alternativas vistas: ConsorcioAbierto jul-2026 $354.652 promedio
  de todas las unidades; Octopus ago-2026 $309.625.
- Fuentes descartadas/pendientes: IDECBA publica un informe trimestral de alquileres (Argenprop,
  $/m² por ambientes) — posible validación cruzada; Zonaprop también tiene Rosario (RSA) y Córdoba
  (CBA).
