import re


def _mayor_rssi_por(detecciones, clave):
    """
    detecciones: lista de Deteccion, clave: función que da la clave de agrupación - lista de Deteccion
    Agrupa las detecciones por la clave y se queda con la de mayor señal de cada grupo.
    El RSSI es negativo, así que la señal más fuerte es el valor mayor (más cercano a 0).
    """
    dict_detecciones = {}
    for i in detecciones:
        k = clave(i)
        if k not in dict_detecciones or i.RSSI > dict_detecciones[k].RSSI:
            dict_detecciones[k] = i
    return list(dict_detecciones.values())


def filtrar_mayor_rssi_mac(detecciones):
    """
    detecciones: lista de Deteccion - lista de Deteccion
    Devuelve una detección por MAC, la de mayor señal.
    """
    return _mayor_rssi_por(detecciones, lambda i: i.MAC)


def filtrar_mayor_rssi_ssid(detecciones):
    """
    detecciones: lista de Deteccion - lista de Deteccion
    Devuelve una detección por SSID, la de mayor señal. Las redes ocultas se agrupan por MAC.
    """
    return _mayor_rssi_por(detecciones, lambda i: i.SSID or i.MAC)


def filtrar_vulnerables(detecciones):
    """
    detecciones: lista de Deteccion - lista de Deteccion
    Devuelve los APs inseguros, uno por MAC (el de mayor señal).
    """
    return [i for i in filtrar_mayor_rssi_mac(detecciones) if i.insegura]


def extraer_ssid_probes(contenido):
    """
    contenido: texto con el JSON de dispositivos de Kismet - lista de str ordenada
    Extrae los SSID solicitados en los probe requests, sin repetidos.
    """
    resultado = re.findall(r'"dot11\.probedssid\.ssid": "(?!")(.+?)"', contenido)
    return sorted(set(resultado))
