# FONTAN

**F**iltrado de redes **O**cultas y **N**o seguras con **T**razado **A**utomático en **N**avegador.

Herramienta para analizar capturas de *wardriving*. Sitúa en un mapa interactivo los puntos de acceso WiFi detectados, señala los que usan cifrado inseguro y extrae los SSID que piden los dispositivos en sus *probe requests*.

El nombre homenajea a Domingo Fontán, autor de la *Carta Geométrica de Galicia* (1834), el primer mapa científico de Galicia.

## Funcionalidades

**Capturas de WiGLE (`.wiglecsv`)**: genera un mapa con varias capas seleccionables:

- Todos los puntos detectados, con un mapa de calor.
- La detección con mayor señal (RSSI) de cada MAC.
- La detección con mayor señal de cada SSID. Las redes ocultas se agrupan por MAC.
- Los APs vulnerables (OPEN, WEP, WPA1 o TKIP), marcados en rojo.

Junto al mapa aparece una tabla enlazada con él:

- Al pulsar una fila, el mapa se centra en ese punto. Al pulsar un marcador, se selecciona su fila.
- Se puede buscar por MAC o SSID y filtrar solo las redes inseguras.
- El separador entre la tabla y el mapa se puede arrastrar para cambiar el ancho de cada parte.
- El mapa incluye herramientas para medir distancias, dibujar y ver las coordenadas del cursor.

**Bases de datos de Kismet (`.kismet`)**: muestra por pantalla los SSID solicitados en los *probe requests*, sin repetidos. Estos SSID revelan a qué redes se han conectado antes los dispositivos cercanos.

## Requisitos

- Python 3.10 o superior.
- Tkinter, necesario para el diálogo de selección de archivo.
- [folium](https://python-visualization.github.io/folium/), que se instala automáticamente.

## Instalación

```bash
git clone https://github.com/MrSegfault/fontan.git
cd fontan
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Uso

```bash
source .venv/bin/activate
fontan            # o bien: python -m fontan
```

Se abre un diálogo para elegir el archivo, y el programa actúa según su extensión:

| Extensión   | Resultado                                                    |
|-------------|--------------------------------------------------------------|
| `.wiglecsv` | Abre en el navegador el mapa y la tabla enlazada             |
| `.kismet`   | Muestra por la terminal los SSID de los *probe requests*     |

El mapa se sirve en `127.0.0.1` en un puerto libre y no se expone a la red local. Hace falta un servidor HTTP porque OpenStreetMap rechaza las teselas pedidas desde `file://`. Para cerrarlo, pulsa `Ctrl+C` en la terminal.

## Estructura

```
fontan/
├── pyproject.toml
├── README.md
└── wardriving/
    ├── __main__.py            # punto de entrada: diálogo y elección de modo
    ├── lector.py              # lectura de .wiglecsv y .kismet
    ├── filtrado.py            # filtros por RSSI, vulnerables y probes
    ├── trazador.py            # mapa folium, tabla HTML y servidor local
    ├── wardriving.skel.html   # plantilla de la tabla enlazada con el mapa
    └── archivos/              # capturas de entrada
```

Los archivos `mapa.html` y `wardriving.html` se generan en cada ejecución.

## Aviso

FONTAN solo analiza capturas pasivas ya realizadas. No se conecta a ninguna red ni interactúa con ella. Úsalo de forma responsable y con fines formativos o de auditoría autorizada. Las capturas contienen ubicaciones e identificadores de redes de terceros, así que no las publiques.

## Licencia

Distribuido bajo la licencia. Consulta [LICENSE](LICENSE).
