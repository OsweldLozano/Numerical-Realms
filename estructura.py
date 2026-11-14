"""
Archivo central de estructura del juego (estructura.json): lectura, validación y guardado.

FORMATO
-------
{
  "mapa": {                                  # el mapa general
    "fondo":  "assets/fondos/mapa.jpg",      # opcional: imagen de fondo
    "musica": "assets/musica/musica1.wav",   # opcional: música (se repite en bucle)
    "subMapas": [                            # un botón del mapa general por cada elemento
      {
        "nombre":   "Interpolacion",         # nombre del submapa (opcional; si falta: "Mapa 1", ...)
        "posicion": [0.6055, 0.4486],        # opcional: [x, y] entre 0 y 1 del botón en el mapa general
        "estado":   "disponible",            # opcional: "bloqueado" | "disponible" | "completado"
        "fondo":    "assets/fondos/subMapa1.jpg",   # opcional: si falta, usa el fondo del mapa
        "musica":   "assets/musica/musica2.wav",    # opcional: si falta, sigue la música del mapa
        "niveles": [                         # un botón por cada nivel dentro del submapa
          {
            "nombre":   "Interpolacion Lineal",     # obligatorio; enlaza con el "titulo" del nivel
            "posicion": [0.30, 0.50],               # opcional: botón dentro del submapa
            "estado":   "disponible"                # opcional (por defecto "disponible")
          }
        ]
      },
      {}                                     # un {} vacío es un submapa pendiente (sale con candado)
    ]
  }
}

REGLAS
------
* Las rutas pueden usar / o \\ y son relativas a la carpeta donde está este archivo
  (también se aceptan rutas absolutas). Si un archivo no existe se avisa y se ignora.
* "posicion" son fracciones del ancho y del alto de la ventana (0 = izquierda/arriba,
  1 = derecha/abajo). Si falta, el botón se reparte automáticamente. Si varios botones
  del mismo mapa tienen exactamente la misma posición, el primero se queda donde está y
  los demás se reparten solos. En el juego, F2 + S fija las posiciones en este archivo.
* "estado" es el estado inicial. Los niveles que el jugador completa se guardan aparte
  (progreso.json) y pasan a verse como "completado". Un submapa se ve completado cuando
  todos sus niveles lo están. Un nivel sin contenido (ver abajo) se ve bloqueado.
* El CONTENIDO de cada nivel no va aquí. Sale de una PLANTILLA (carpeta plantillas/, genera
  un problema nuevo cada vez; ver constructor_niveles.py) o de un nivel fijo del JSON de
  niveles (niveles.json). Cada nivel de la estructura toma el contenido cuyo "nivel" (o, si
  no tiene, su "titulo") tiene el mismo nombre, sin distinguir mayúsculas, acentos ni
  espacios extra: "Interpolacion Lineal" enlaza con "Interpolación Lineal". Si hay una
  plantilla y un nivel fijo con el mismo nombre, se usa la plantilla.
"""
import json
import os
import re
import unicodedata

ESTADOS = ("bloqueado", "disponible", "completado")


# ------------------------------------------------------------------ estructuras
class Nivel:
    def __init__(self, nombre, posicion, estado, raw, clave):
        self.nombre = nombre
        self.posicion = posicion      # [x, y] o None
        self.estado = estado          # estado inicial
        self.raw = raw                # el diccionario original del JSON (para guardar)
        self.clave = clave            # "Submapa/Nivel": identifica al nivel en el progreso
        self.contenido = None         # definición del nivel (se asigna en vincular_contenido)


class SubMapa:
    def __init__(self, indice, nombre, posicion, estado, fondo, musica, niveles, raw):
        self.indice = indice
        self.nombre = nombre
        self.posicion = posicion
        self.estado = estado
        self.fondo = fondo            # ruta ya resuelta, o None
        self.musica = musica
        self.niveles = niveles
        self.raw = raw


class Estructura:
    def __init__(self, ruta, datos):
        self.ruta = ruta
        self.base = os.path.dirname(ruta)
        self.datos = datos
        self.fondo = None
        self.musica = None
        self.submapas = []
        self.avisos = []              # cosas que no impiden jugar pero conviene revisar


# ------------------------------------------------------------------- utilidades
def normalizar(texto):
    """Minúsculas, sin acentos y sin espacios de más: para comparar nombres."""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


def resolver_ruta(base, texto):
    """Ruta relativa a `base`, aceptando \\ o / como separador."""
    texto = texto.strip().replace("\\", "/")
    return os.path.normpath(os.path.join(base, texto))


def _err(ruta, msg):
    raise ValueError(f"{ruta}: {msg}")


def _es_numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _leer_estado(d, ruta):
    v = d.get("estado", "disponible")
    if not isinstance(v, str) or v.strip().lower() not in ESTADOS:
        _err(f"{ruta}.estado", f'debe ser "bloqueado", "disponible" o "completado" (se recibió {v!r})')
    return v.strip().lower()


def _leer_posicion(d, ruta):
    p = d.get("posicion")
    if p is None:
        return None
    ok = (isinstance(p, list) and len(p) == 2 and all(_es_numero(v) for v in p)
          and all(0 <= v <= 1 for v in p))
    if not ok:
        _err(f"{ruta}.posicion", "debe ser [x, y] con dos números entre 0 y 1 "
                                  f"(fracción del ancho y del alto de la ventana); se recibió {p!r}")
    return [float(p[0]), float(p[1])]


def _leer_archivo(d, clave, ruta, est):
    """Ruta de un archivo (fondo o música) ya resuelta. Si no existe, avisa y devuelve None."""
    v = d.get(clave)
    if v is None:
        return None
    if not isinstance(v, str) or not v.strip():
        _err(f"{ruta}.{clave}", "debe ser un texto con la ruta del archivo")
    p = resolver_ruta(est.base, v)
    if not os.path.isfile(p):
        est.avisos.append(f"{ruta}.{clave}: no encuentro {v!r} (busqué en {p}); se ignora")
        return None
    return p


def posiciones_de(items):
    """Posiciones de los botones de un mapa, listas para MapaNiveles. Si varios comparten
    exactamente la misma posición, el primero la conserva y los demás quedan en None
    (se reparten automáticamente)."""
    vistas, res = set(), []
    for it in items:
        p = it.posicion
        if p is not None:
            k = (round(p[0], 4), round(p[1], 4))
            if k in vistas:
                p = None
            else:
                vistas.add(k)
        res.append(p)
    return res


def _avisar_repetidas(items, etiqueta, est):
    repetidos = [it.nombre for it, p in zip(items, posiciones_de(items))
                 if p is None and it.posicion is not None]
    if repetidos:
        est.avisos.append(
            f"{etiqueta}: {len(repetidos)} botón(es) tienen la misma posición que otro "
            f"({', '.join(repetidos)}); se reparten automáticamente. "
            "Usa F2 y S en el juego para fijar sus posiciones.")


# ------------------------------------------------------------------------ carga
def cargar_estructura(ruta_json):
    """Lee y valida estructura.json. Lanza FileNotFoundError, json.JSONDecodeError o
    ValueError (con la ruta exacta del campo problemático)."""
    ruta_json = os.path.abspath(ruta_json)
    with open(ruta_json, encoding="utf-8") as f:
        datos = json.load(f)
    if not isinstance(datos, dict) or not isinstance(datos.get("mapa"), dict):
        _err("(raíz)", 'falta el objeto "mapa"')
    est = Estructura(ruta_json, datos)
    mapa = datos["mapa"]
    est.fondo = _leer_archivo(mapa, "fondo", "mapa", est)
    est.musica = _leer_archivo(mapa, "musica", "mapa", est)

    subs = mapa.get("subMapas")
    if not (isinstance(subs, list) and subs):
        _err("mapa.subMapas", "debe ser una lista con al menos un submapa (puede usar {} como marcador)")

    nombres_sub = set()
    for k, s in enumerate(subs):
        rs = f"mapa.subMapas[{k}]"
        if not isinstance(s, dict):
            _err(rs, "debe ser un objeto { ... } (puede estar vacío)")
        nombre = s.get("nombre")
        if nombre is None:
            nombre = f"Mapa {k + 1}"
        elif not isinstance(nombre, str) or not nombre.strip():
            _err(f"{rs}.nombre", "debe ser un texto")
        nombre = nombre.strip()
        if normalizar(nombre) in nombres_sub:
            _err(f"{rs}.nombre", f"el nombre {nombre!r} está repetido; cada submapa necesita uno distinto")
        nombres_sub.add(normalizar(nombre))

        niveles_raw = s.get("niveles", [])
        if not isinstance(niveles_raw, list):
            _err(f"{rs}.niveles", "debe ser una lista de niveles")
        niveles, vistos = [], set()
        for j, n in enumerate(niveles_raw):
            rn = f"{rs}.niveles[{j}]"
            if not isinstance(n, dict):
                _err(rn, "debe ser un objeto { ... }")
            nom = n.get("nombre")
            if not isinstance(nom, str) or not nom.strip():
                _err(f"{rn}.nombre", 'falta el "nombre" del nivel (texto)')
            nom = nom.strip()
            if normalizar(nom) in vistos:
                _err(f"{rn}.nombre", f"el nombre {nom!r} está repetido dentro de este submapa")
            vistos.add(normalizar(nom))
            niveles.append(Nivel(nom, _leer_posicion(n, rn), _leer_estado(n, rn), n, f"{nombre}/{nom}"))

        sub = SubMapa(k, nombre, _leer_posicion(s, rs), _leer_estado(s, rs),
                      _leer_archivo(s, "fondo", rs, est), _leer_archivo(s, "musica", rs, est),
                      niveles, s)
        est.submapas.append(sub)
        _avisar_repetidas(niveles, f"Submapa {nombre!r}", est)

    _avisar_repetidas(est.submapas, "Mapa general", est)
    return est


def vincular_contenido(est, pool):
    """Asigna a cada nivel su contenido buscando por nombre en `pool` (plantillas y niveles
    fijos ya validados). El nombre es "nivel" si existe, si no "titulo"; ante nombres
    repetidos gana el primero del pool. Agrega a est.avisos lo que no coincida."""
    indice = {}
    for n in pool:
        indice.setdefault(normalizar(_nombre_enlace(n)), n)
    usados, sin_contenido = set(), []
    for sub in est.submapas:
        for nv in sub.niveles:
            c = indice.get(normalizar(nv.nombre))
            if c is None:
                sin_contenido.append(f"{sub.nombre} / {nv.nombre}")
            else:
                nv.contenido = c
                usados.add(normalizar(nv.nombre))
    if sin_contenido:
        est.avisos.append("Niveles de la estructura sin contenido en el JSON de niveles (salen con "
                          "candado): " + "; ".join(sin_contenido))
    sobran = [_nombre_enlace(n) for n in pool if normalizar(_nombre_enlace(n)) not in usados]
    if sobran:
        est.avisos.append("Niveles del JSON de niveles que no aparecen en la estructura (no se podrán "
                          "jugar): " + "; ".join(sobran))


def _nombre_enlace(contenido):
    return contenido.get("nivel") or contenido["titulo"]


# ---------------------------------------------------------------------- guardado
def actualizar_posiciones(items, posiciones):
    """Guarda en memoria (y en el diccionario original) las posiciones de un mapa."""
    for it, p in zip(items, posiciones):
        p = [float(p[0]), float(p[1])]
        it.posicion = p
        it.raw["posicion"] = p


def guardar_estructura(est):
    """Escribe el archivo completo (sangría de 2 espacios). Lanza OSError si falla."""
    tmp = est.ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(est.datos, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, est.ruta)
