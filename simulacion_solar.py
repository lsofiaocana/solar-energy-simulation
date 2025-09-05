# -*- coding: utf-8 -*-
"""
Created on Tue Sep  2 21:15:11 2025

@author: laura
"""
import csv
import numpy as np
import math
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import pandas as pd
x=float(input("Dame la latitud, ej. 6.25: "))
latitud = math.radians(x)

def diaAno(ano, mes, dia):
    fecha = datetime.date(ano, mes, dia)
    return fecha.timetuple().tm_yday

def solarPosition(dAno,time,latitud):
    decSolar = math.radians(23.45 * math.sin(math.radians((360/365)*(284+dAno))))
    LocalSolarTime = time - 1 + 14.6/60
    aHorario = math.radians(15*(LocalSolarTime - 12))
    aSolar = math.degrees(math.asin((math.sin(latitud))*(math.sin(decSolar)) +(math.cos(latitud))*(math.cos(decSolar))*(math.cos(aHorario))))
    acimut = math.degrees(math.atan2(math.sin(aHorario),(math.cos(aHorario)*math.sin(latitud)-math.tan(decSolar)*math.cos(latitud))))
    return acimut,aSolar


def solarIrradiance(dAno, time, latitud):     

    # --- 1) Declinación y ángulo horario ---
    decSolar_deg = 23.45 * math.sin(math.radians((360/365) * (284 + dAno)))
    LocalSolarTime = time - 1 + 14.6/60
    decSolar = math.radians(decSolar_deg)
    aHorario = math.radians(15.0 * (LocalSolarTime - 12.0))
    sin_h = math.sin(latitud)*math.sin(decSolar) + math.cos(latitud)*math.cos(decSolar)*math.cos(aHorario)
    sin_h = max(-1.0, min(1.0, sin_h))         # protección numérica
    altitud = math.degrees(math.asin(sin_h))   # altitud en grados
    # Si es de noche (h <= 0): todo cero
    if altitud <= 0:
        radDirecNormal = 0.0
        radDirecHorizontal = 0.0
        radDifHorizonal = 0.0
        radGlobalHorizontal = 0.0
        return radGlobalHorizontal, radDirecNormal, radDifHorizonal, radDirecHorizontal
    cteSolar = 1367.0
    irrExtr = cteSolar * (1 + 0.033 * math.cos(math.radians(360 * dAno / 365.0)))
    masaAire = 1.0 / (math.sin(math.radians(altitud)) + 0.50572 * ((altitud + 6.07995) ** -1.6364))    
    coefTurb = 0.18         # (0.12 cielo muy claro, 0.25 más turbio)
    radDirecNormal = irrExtr * math.exp(-coefTurb * masaAire)
    radDirecHorizontal = radDirecNormal * math.sin(math.radians(altitud))  # G_bh
    fracDifusa = 0.15       # fracción difusa (puedes ajustar 0.10–0.30)
    radDifHorizonal = (fracDifusa / (1.0 - fracDifusa)) * radDirecHorizontal
    radGlobalHorizontal = radDirecHorizontal + radDifHorizonal
    return radGlobalHorizontal, radDirecNormal, radDifHorizonal, radDirecHorizontal

# - aSolar: altitud solar (°)
# - acimut: acimut solar (°) con 0°=Sur; +Oeste; -Este (igual a solarPosition)
# - incliPv: inclinación del panel β (°) [0=horizontal, 90=vertical]
# - azimuthPv: acimut del panel γ (°) [0=Sur; +Oeste; -Este]
def cosIncidenciaAltiAzim(alSolar, acimutSolar, inclinacionPv, acimutPv):
    # Fórmula: cosθ = sin h * cosβ + cos h * sinβ * cos(A_solar - γ)
    h  = math.radians(alSolar) #altitud solar
    B  = math.radians(inclinacionPv) #inclinacion del panel
    dA = math.radians(acimutSolar - acimutPv)
    cos_t = math.sin(h)*math.cos(B) + math.cos(h)*math.sin(B)*math.cos(dA)
    return max(0.0, cos_t)  # si es negativo, el sol no "ve" al panel

#  Entradas del panel y fecha 
areaPv = float(input("Área del panel (m^2), ej. 1.95: "))
eficienciaPv = float(input("Eficiencia del panel (0-1), ej. 0.21: "))
incliPv = float(input("Inclinación del panel β (°), ej. 15: "))
azimuthPv = float(input("Azimut del panel γ (0=Sur; +90=Oeste; -90=Este): "))

ano = int(input("Año (YYYY): "))
mes = int(input("Mes (1-12): "))
dia = int(input("Día (1-31): "))

# Día del año con tu función
dAno = diaAno(ano, mes, dia)

# Parámetro simple para reflexión del suelo
albedo = 0.2  # 0.2 típico

# -------------------- Simulación hora a hora --------------------
horas = np.arange(0, 24, 0.5)
altitudes = []
potencias_W = []
energia_kWh = 0.0
GHI_model = []

for h in horas:
    acimut, aSolar = solarPosition(dAno, h, latitud)  # devuelve (acimut°, altitud°)
    altitudes.append(aSolar)

    # Irradiancias base 
    GHI, DNI, DHI, G_bh = solarIrradiance(dAno, h, latitud)
    GHI_model.append(GHI)  # guardamos el GHI de esta hora (W/m²)

    if aSolar <= 0 or (DNI == 0 and GHI == 0):
        potencias_W.append(0.0)
        continue

    # 3) Proyección al plano del panel usando aSolar y acimut 
    cos_t = cosIncidenciaAltiAzim(aSolar, acimut, incliPv, azimuthPv)

    # Directa en el plano
    Gbt = DNI * cos_t
    # Difusa en el plano (Liu & Jordan isotrópico; usa DHI de tu función)
    Gdt = DHI * (1 + math.cos(math.radians(incliPv))) / 2.0
    # Reflejada desde el suelo (usa GHI de tu función)
    Grt = GHI * albedo * (1 - math.cos(math.radians(incliPv))) / 2.0
    # Irradiancia total en el panel
    Gt = max(0.0, Gbt + Gdt + Grt)

    # 4) Potencia eléctrica y energía
    P = Gt * areaPv * eficienciaPv              # W
    potencias_W.append(P)
    energia_kWh += P / 1000.0                   # kWh por hora (paso 1 h)
#  Guardar resultados con FECHA y HORA (hh:mm) 
# Paso en minutos detectado a partir del vector 'horas'
paso_min = int(round((horas[1] - horas[0]) * 60)) if len(horas) > 1 else 60

# Fecha base: el día elegido a las 00:00
base_dt = datetime.datetime(ano, mes, dia, 0, 0)

# Lista de timestamps y hora en formato hh:mm
fechas = [base_dt + datetime.timedelta(minutes=paso_min * i) for i in range(len(horas))]
horas_str = [dt.strftime("%H:%M") for dt in fechas]  # "00:00", "00:30", ...
#  Exportar simulación con datetime para comparar con NASA 
with open("simulacion_solar.csv", mode="w", newline="") as f:
    w = csv.writer(f)
    # añadimos la columna de GHI:
    w.writerow(["datetime", "AltitudSolar(°)", "Potencia(W)", "GHI(W/m²)"])
    for i in range(len(fechas)):
        w.writerow([
            fechas[i].strftime("%Y-%m-%d %H:%M"),
            round(altitudes[i], 2),
            round(potencias_W[i], 2),
            round(GHI_model[i], 1)  # GHI 
        ])
print("Archivo 'simulacion_solar.csv' guardado.")
# Gráfica de altitud solar
plt.figure()
plt.plot(fechas, altitudes)
plt.xlabel("Hora del día")
plt.ylabel("Altitud solar (°)")
plt.title("Altitud del sol a lo largo del día")
plt.grid(True)
# Formato del eje x como horas hh:mm
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gcf().autofmt_xdate()  
plt.tight_layout()
#  Gráfica de potencia 
plt.figure()
plt.plot(fechas, potencias_W)
plt.xlabel("Hora del día")
plt.ylabel("Potencia eléctrica del panel (W)")
plt.title("Potencia del panel durante el día")
plt.grid(True)
# Formato del eje x como horas hh:mm
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gcf().autofmt_xdate()
plt.tight_layout()

plt.show()
NASA = "POWER_Point_Hourly_20250101_20250101_006d62N_076d24W_LST.csv"
SIM  = "simulacion_solar.csv"

def fila_encabezado(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            s = line.strip().upper()
            if s.startswith("YEAR,") or s.startswith("YEAR;") or s.startswith("LST") or s.startswith("TIME") or s.startswith("LOCAL_TIME"):
                return i
    return 0

# --- NASA: leer desde el encabezado detectado, autodetectar separador y saltar líneas malas ---
h = fila_encabezado(NASA)
nasa = pd.read_csv(NASA, skiprows=h, sep=None, engine="python", on_bad_lines="skip")
if nasa.shape[1] == 1:  # por si el separador era ';'
    nasa = pd.read_csv(NASA, skiprows=h, sep=";", engine="python", on_bad_lines="skip")

# datetime desde YEAR, MO, DY, HR
nasa["datetime"] = pd.to_datetime(dict(year=nasa["YEAR"], month=nasa["MO"], day=nasa["DY"], hour=nasa["HR"]))
# GHI NASA -> W/m² (si viene en kWh/m²·h)
ghi = pd.to_numeric(nasa["ALLSKY_SFC_SW_DWN"], errors="coerce")
nasa["GHI_Wm2"] = (ghi * 1000) if ghi.max() <= 5 else ghi

# --- Simulación ---
sim = pd.read_csv(SIM, parse_dates=["datetime"])

# Alinear por hora y unir
nasa["hora"] = nasa["datetime"].dt.floor("H")
sim["hora"]  = sim["datetime"].dt.floor("H")
df = sim.merge(nasa[["hora","GHI_Wm2"]], on="hora", how="inner")

# Gráfica
plt.figure(figsize=(12,5))
plt.plot(df["hora"], df["GHI_Wm2"],   label="NASA GHI (W/m²)")
plt.plot(df["hora"], df["GHI(W/m²)"], label="Modelo GHI (W/m²)")
plt.xlabel("Hora del día"); plt.ylabel("Irradiancia (W/m²)"); plt.title("NASA vs Modelo")
plt.legend(); plt.grid(True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M")); plt.gcf().autofmt_xdate()
plt.tight_layout(); plt.show()
