import csv
import re
import sqlite3

INSEGURAS = [re.compile(p) for p in (
    r".*OPEN.*",
    r".*WEP.*",
    r".*WPA(?![2-9]).*",
    r".*TKIP.*",
)]


def extrae_wiglecsv(path=None):
    """
    path: ruta del archivo .wiglecsv - lista de Deteccion (None si no hay ruta)
    Lee el CSV de WiGLE, salta las dos líneas de cabecera y crea una Deteccion por
    fila. Descarta las filas corruptas o con datos no numéricos y las que no son WIFI.
    """
    if not path:
        return None
    with open(path, encoding='utf-8', errors='replace', newline='') as f:
        datos = list(csv.reader(f))
    if len(datos) < 3:
        return []
    cabecera = datos[1]
    lista_detecciones = []
    for fila in datos[2:]:
        if len(fila) != len(cabecera):
            continue
        try:
            deteccion = Deteccion(cabecera, fila)
        except (ValueError, KeyError):
            continue
        if getattr(deteccion, 'Type', 'WIFI') == 'WIFI':
            lista_detecciones.append(deteccion)
    return lista_detecciones


class Deteccion:
    def __init__(self, cabecera, fila):
        """
        cabecera: nombres de columna, fila: valores de una fila del CSV - instancia de Deteccion
        Crea un atributo por cada columna, convierte a número RSSI, latitud y longitud,
        y marca la detección como insegura si su AuthMode coincide con algún patrón de INSEGURAS.
        """
        self.__dict__ = dict(zip(cabecera, fila))
        self.RSSI = int(self.RSSI)
        self.CurrentLatitude = float(self.CurrentLatitude)
        self.CurrentLongitude = float(self.CurrentLongitude)
        self.insegura = any(p.match(self.AuthMode) for p in INSEGURAS)


def lee_string(path=None):
    """
    path: ruta del archivo .kismet - str con el contenido (None si no hay ruta)
    Abre el .kismet como base de datos SQLite en solo lectura y devuelve el JSON de
    todos los dispositivos de la tabla devices. Si no es una base de datos válida,
    lo lee como texto plano en latin-1.
    """
    if not path:
        return None
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            filas = con.execute("SELECT device FROM devices").fetchall()
        finally:
            con.close()
        return "\n".join(
            f[0].decode('utf-8', errors='replace') if isinstance(f[0], bytes) else str(f[0])
            for f in filas
        )
    except sqlite3.DatabaseError:
        with open(path, "r", encoding='latin-1') as f:
            return f.read()
