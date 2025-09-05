# Simulación de Irradiancia Solar y Potencia Fotovoltaica en Python

Modelo en Python que calcula la posición solar, la irradiancia (directa, difusa y global) y la potencia de un panel FV según latitud, fecha, inclinación y acimut.  
Incluye comparación de **GHI** del modelo con **NASA POWER** para validar resultados.
---
# Valores recomendados (reproducibilidad de la comparación)
Para que la gráfica **NASA vs Modelo** funcione sin ajustes:
- **Latitud:** `6.25`  (Medellín, Colombia)  
- **Fecha:** `2025-01-01` (Año `2025`, Mes `1`, Día `1`)  
- **Área del panel (m²):** `1.95`  
- **Eficiencia (0–1):** `0.21`  
- **Inclinación (°):** `15`  
- **Acimut (°):** `0`  (0 = Sur; +90 = Oeste; -90 = Este)
**Archivo NASA esperado (en la misma carpeta):**  
`POWER_Point_Hourly_20250101_20250101_006d62N_076d24W_LST.csv`  
> Puedes cambiar el nombre en el script (variable `NASA`) si tu archivo tiene otro nombre o coordenadas cercanas.
---
#  Archivos principales
- `simulacion_solar.py` — Script principal.
- `simulacion_solar.csv` — Resultados horarios (se genera al ejecutar).
- `POWER_Point_Hourly_...csv` — Archivo NASA para la comparación (descárgalo).
---
#  Requisitos
- Python 3.8+
- Librerías:
  - `numpy`, `matplotlib`, `pandas`
  - `math`, `datetime`, `csv` (vienen con Python)

Instalación rápida:
```bash
pip install numpy matplotlib pandas
