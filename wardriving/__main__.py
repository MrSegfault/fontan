import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from . import filtrado, lector, trazador


def mapea_puntos(path_archivo):
    """
    path_archivo: ruta del .wiglecsv - nada
    Lee las detecciones, crea las capas del mapa (todos los puntos con mapa de calor,
    mayor RSSI por MAC y por SSID, y APs vulnerables), genera la tabla enlazada con
    los marcadores y abre el resultado en el navegador.
    """
    detecciones = lector.extrae_wiglecsv(path_archivo)
    if not detecciones:
        print("No hay detecciones WIFI válidas en el archivo")
        return

    mayor_rssi_mac = filtrado.filtrar_mayor_rssi_mac(detecciones)
    mapa = trazador.Mapa(detecciones[0].CurrentLatitude, detecciones[0].CurrentLongitude, 17)
    mapa.anade_detecciones([], nombre_grupo="Ninguno", mapa_calor=False)
    mapa.anade_detecciones(detecciones, nombre_grupo="Todos los puntos", mapa_calor=True)
    mapa.anade_detecciones(mayor_rssi_mac, nombre_grupo="Mayor RSSI por MAC", mapa_calor=False)
    mapa.anade_detecciones(filtrado.filtrar_mayor_rssi_ssid(detecciones), nombre_grupo="Mayor RSSI por SSID", mapa_calor=False)
    mapa.anade_detecciones(filtrado.filtrar_vulnerables(detecciones), nombre_grupo="APs Vulnerables", mapa_calor=False)
    trazador.crea_tabla(mayor_rssi_mac, mapa.enlace())
    mapa.dibuja_mapa()


def extrae_ocultos(path_archivo):
    """
    path_archivo: ruta del .kismet - nada
    Imprime por pantalla los SSID de los probe requests capturados, sin repetidos.
    """
    contenido = lector.lee_string(path_archivo)
    for ssid in filtrado.extraer_ssid_probes(contenido):
        print(ssid)


def main():
    """
    nada - nada
    Pide un archivo con un diálogo (ocultando la ventana vacía de Tk) y, según su
    extensión, genera el mapa (.wiglecsv) o lista los SSID de los probes (.kismet).
    """
    raiz = tk.Tk()
    raiz.withdraw()
    path_archivo = filedialog.askopenfilename(
        initialdir=Path(__file__).resolve().parent / "archivos",
        title="Archivo a leer",
        filetypes=[("Wigle CSV", "*.wiglecsv"), ("Kismet Database", "*.kismet"), ("All files", "*.*")],
    )
    raiz.destroy()

    if not path_archivo:
        print("No se ha seleccionado ningún archivo")
        return

    match os.path.splitext(path_archivo)[1]:
        case ".kismet":
            extrae_ocultos(path_archivo)
        case ".wiglecsv":
            mapea_puntos(path_archivo)
        case _:
            print("Los archivos deben ser .kismet o .wiglecsv")


if __name__ == "__main__":
    main()
