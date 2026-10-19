import html
import json
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import folium
from folium.plugins import HeatMap, GroupedLayerControl, MeasureControl, Draw, MousePosition, OverlappingMarkerSpiderfier

BASE = Path(__file__).resolve().parent
RUTA_MAPA = BASE / "mapa.html"
RUTA_ESQUELETO = BASE / "wardriving.skel.html"
RUTA_SALIDA = BASE / "wardriving.html"

_HUECO_DETECCIONES = "const detecciones = [ /* python llena el JSON aquí */ ];"
_HUECO_ENLACE = "const enlaceMapa = { /* python llena el JSON aquí */ };"


def _escapa(valor):
    """
    valor: cualquier valor - str escapado
    Escapa un valor para meterlo en el HTML de un popup de folium. Además de < > & " ',
    neutraliza \\ ` y $, porque folium mete el popup dentro de un template literal de
    JavaScript, donde un "\\303" rompería el script y un "${...}" ejecutaría código.
    """
    return (html.escape(str(valor))
            .replace('\\', '&#92;')
            .replace('`', '&#96;')
            .replace('$', '&#36;'))


class Mapa:
    def __init__(self, lat, lon, zoom, temas=("openstreetmap",)):
        """
        lat, lon: centro inicial, zoom: zoom inicial, temas: capas base - instancia de Mapa
        Crea el mapa de folium sin capa base por defecto, añade las capas base indicadas
        y las herramientas de medir, dibujar y mostrar coordenadas.
        """
        self._mapa = folium.Map(location=[lat, lon], zoom_start=zoom, control_scale=True, tiles=None)
        for tema in temas:
            folium.TileLayer(tema).add_to(self._mapa)
        self._mapa.add_child(MeasureControl())
        Draw(export=True).add_to(self._mapa)
        MousePosition().add_to(self._mapa)
        self.grupos = []
        self._marcadores = {}

    def enlace(self):
        """
        nada - dict {"mapa": nombre de la variable JS del mapa, "marcadores": {variable JS: MAC}}
        Devuelve lo que necesita la tabla para controlar el mapa del iframe. Folium declara
        el mapa y los marcadores como variables globales, accesibles como window[nombre].
        """
        return {"mapa": self._mapa.get_name(), "marcadores": self._marcadores}

    def dibuja_mapa(self):
        """
        nada - nada (bloquea hasta Ctrl+C)
        Añade los controles de capas y el separador de marcadores superpuestos, guarda
        mapa.html y sirve la carpeta por HTTP para abrir wardriving.html en el navegador.
        """
        folium.LayerControl(collapsed=False).add_to(self._mapa)
        GroupedLayerControl(
            groups={'Puntos': self.grupos},
            collapsed=False,
        ).add_to(self._mapa)
        oms = OverlappingMarkerSpiderfier(
            keep_spiderfied=True,
            nearby_distance=20,
            circle_spiral_switchover=10,
            leg_weight=2.0
            )
        oms.add_to(self._mapa)
        self._mapa.save(str(RUTA_MAPA))
        _sirve_y_abre(RUTA_SALIDA.name)

    def anade_detecciones(self, detecciones, nombre_grupo, mapa_calor=False):
        """
        detecciones: lista de Deteccion, nombre_grupo: str, mapa_calor: bool - nada
        Crea una capa seleccionable con un marcador por detección y, si se pide,
        una capa adicional con el mapa de calor de esas detecciones.
        """
        feature = folium.FeatureGroup(name=nombre_grupo, overlay=True)
        if mapa_calor and detecciones:
            coordenadas = [[i.CurrentLatitude, i.CurrentLongitude] for i in detecciones]
            HeatMap(coordenadas).add_to(folium.FeatureGroup(name='Mapa de calor', overlay=True).add_to(self._mapa))
        self._coloca_markers(detecciones, feature)

        self._mapa.add_child(feature)
        self.grupos.append(feature)

    def _coloca_markers(self, detecciones, feature):
        """
        detecciones: lista de Deteccion, feature: FeatureGroup de folium - nada
        Añade a la capa un marcador por detección (rojo si es insegura) con un popup
        escapado, y registra el nombre JS de cada marcador con su MAC.
        """
        for i in detecciones:
            coordenada = [i.CurrentLatitude, i.CurrentLongitude]
            if i.insegura:
                marker = folium.Marker(location=coordenada, icon=folium.Icon(color='red'))
            else:
                marker = folium.Marker(location=coordenada)
            popup = "SSID: {}<br>MAC: {}<br>Auth: {}<br>Channel: {}<br>RSSI: {}".format(
                _escapa(i.SSID or "(oculta)"), _escapa(i.MAC), _escapa(i.AuthMode),
                _escapa(i.Channel), _escapa(i.RSSI))
            folium.Popup(popup, parse_html=False, max_width=1000).add_to(marker)
            marker.add_to(feature)
            self._marcadores[marker.get_name()] = i.MAC


def _sirve_y_abre(pagina):
    """
    pagina: nombre del HTML a abrir - nada (bloquea hasta Ctrl+C)
    Sirve la carpeta del proyecto solo en 127.0.0.1, sin exponerla a la red local,
    en un puerto libre. Abre la página en el navegador y espera hasta Ctrl+C.
    Hace falta servirla por HTTP porque OpenStreetMap rechaza las teselas pedidas
    desde file://, que no envían cabecera Referer.
    """
    manejador = partial(_ManejadorSilencioso, directory=str(BASE))
    with ThreadingHTTPServer(("127.0.0.1", 0), manejador) as servidor:
        url = f"http://127.0.0.1:{servidor.server_address[1]}/{pagina}"
        print(f"Mapa disponible en {url}  (Ctrl+C para cerrar)")
        webbrowser.open(url, new=0)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor cerrado")


class _ManejadorSilencioso(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        """
        args: argumentos del log - nada
        Anula el log del servidor para no imprimir una línea por cada petición.
        """
        pass


def _a_json(datos):
    """
    datos: objeto serializable - str JSON
    Convierte a JSON y escapa '<' para que un SSID con "</script>" no pueda cerrar
    el bloque de script. Las tildes, la ñ y similares ya salen como \\uXXXX.
    """
    return json.dumps(datos).replace('<', '\\u003c')


def crea_tabla(detecciones, enlace=None):
    """
    detecciones: lista de Deteccion, enlace: dict de Mapa.enlace() - nada
    Genera wardriving.html a partir del esqueleto, metiendo las detecciones y el enlace
    con el mapa como variables JS. Usa reemplazo de texto exacto, sin regex (una regex
    con ".*" sobre la línea del JSON tenía coste cuadrático), y sustituye primero el
    enlace para no buscar nunca dentro del JSON de detecciones.
    """
    content = RUTA_ESQUELETO.read_text(encoding='utf-8')
    for hueco in (_HUECO_ENLACE, _HUECO_DETECCIONES):
        if hueco not in content:
            raise ValueError(f"No se encuentra en el esqueleto: {hueco}")
    enlace_json = _a_json(enlace or {"mapa": None, "marcadores": {}})
    content = content.replace(_HUECO_ENLACE, "const enlaceMapa = " + enlace_json + ";", 1)
    tabla_json = _a_json([i.__dict__ for i in detecciones])
    content = content.replace(_HUECO_DETECCIONES, "const detecciones = " + tabla_json + ";", 1)
    RUTA_SALIDA.write_text(content, encoding='utf-8')
