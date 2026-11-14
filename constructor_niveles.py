"""
Constructor de niveles: PLANTILLA (JSON base del nivel) + DATOS (generador y resolvedor)
-> NIVEL listo para jugar (el mismo formato que lee nivel_generico.py).

    plantillas/biseccion.json  ──┐
                                 ├──> constructor_niveles.py ──> nivel (dict) ──> nivel_generico
    generadores/...py  ──> datos ┘

Cada vez que el jugador abre un nivel se genera un problema nuevo, se resuelve y se
arma el nivel con los valores de esa solución.


QUÉ VA EN CADA LUGAR
--------------------
* La PLANTILLA dice cómo se ve el nivel: instrucción, pasos, qué se escribe en cada
  casilla. No lleva números del problema, solo referencias a los datos ({x0}, "m"...).
* El GENERADOR (una función en la carpeta generadores/) crea un problema aleatorio, lo
  resuelve y devuelve un diccionario con TODO lo que la plantilla necesita: los datos del
  problema y los valores intermedios del proceso de solución. Ver generadores/__init__.py.


FORMATO DE LA PLANTILLA
-----------------------
{
  "titulo":      "Bisección",               # obligatorio; texto de la píldora (admite {...})
  "nivel":       "Bisectriz",               # opcional: nombre del nivel en estructura.json con el
                                            #   que se enlaza (si falta, se usa "titulo")
  "generador":   "biseccion",               # obligatorio: nombre registrado en generadores/
  "parametros":  {"iteraciones": 4},        # opcional: se pasan al generador
  "tiempo":      600,                       # opcional, segundos (def. 600)
  "decimales":   4,                         # opcional: cifras con que se MUESTRAN los números (def. 4)
  "tolerancia":  1e-6,                      # opcional: tolerancia por defecto de las casillas
  "instruccion": "Aproxime la raíz de {funcion} en [{a}, {b}]...",
  "intro":       ["{funcion}", ...],        # opcional
  "pasos": [ ...pasos... ]
}

Textos con datos:  "Datos: x0={x0}  y0={y0}"
    Lo que va entre llaves es una EXPRESIÓN sobre los datos: {x0}, {y1 - y0}, {it.c},
    {A[0][1]}, {abs(error)}. Para fijar el formato: {m:.2f}. Para escribir una llave
    literal: {{ o }}.

Un paso:
    {"titulo": "Paso {paso}. Calcule la pendiente:",      # {paso} = número del paso, automático
     "filas": [ ["m =", {"in": "m"}],  ... ]}

Tokens de una fila:
    "texto {dato}"                    etiqueta fija (con datos)
    5                                 etiqueta fija
    {"in": "m"}                       casilla; la respuesta es la expresión "m" evaluada.
                                      Opcional: "decimales" (redondea la respuesta y acepta
                                      cualquier valor que redondee igual), "tol", "ancho", "limite".
                                      Si no indicas "ancho", se ajusta a la longitud del número.
    {"in": 7}                         casilla con respuesta fija (no depende de los datos)
    {"matriz": "Ab", "casillas": "todas"}
                                      matriz tomada de los datos. "casillas" dice qué celdas se
                                      llenan: "todas", "ninguna", una lista [[fila, col], ...]
                                      (desde 0) o una expresión que dé esa lista ("et.editables").
                                      Admite "decimales" y "tol" para las casillas.
    {"matriz": [[1, {"in": "a"}], ["{b}", 4]]}
                                      matriz escrita a mano (celdas: texto, número o casilla)

REPETIR (número variable de pasos o filas: iteraciones, etapas de eliminación...)
    {"repetir": "iteraciones", "como": "it", "max": 6,
     "paso": {"titulo": "Iteración {num}: ...", "filas": [["c =", {"in": "it.c"}]]}}

    Recorre la lista de los datos "iteraciones" (o range(n) si la expresión da un entero)
    y crea un paso por elemento. Dentro están disponibles:
        it     el elemento ("como"; por defecto "elem")     num    1, 2, 3...
        idx    0, 1, 2...                                   total  cuántos elementos hay
    "max" (opcional) limita cuántos se usan. Lo mismo sirve dentro de "filas" con "fila":
        {"repetir": "puntos", "como": "p", "fila": ["x{num} =", {"in": "p.x"}]}
    y dentro de "intro" con "texto":
        {"repetir": "ecuaciones", "como": "ec", "texto": "{ec}"}

CONDICIONES:  cualquier paso, fila, texto o "repetir" puede llevar "si": "expresión";
    se omite cuando la expresión es falsa. Ej.: {"si": "convergio", "paso": {...}}

EXPRESIONES: números, + - * / // % **, comparaciones, and/or/not, "x if c else y",
    acceso a datos (it.c o it["c"], A[0][1]) y las funciones abs, round, min, max, len,
    sum, sqrt, exp, log, sin, cos, tan (y las constantes pi, e). Nada más se ejecuta.


USO DESDE LA TERMINAL
---------------------
    python constructor_niveles.py                              # prueba todas las plantillas
    python constructor_niveles.py plantillas/biseccion.json    # muestra un nivel generado (JSON)
        --semilla 7       mismo problema siempre (para depurar)
        --datos           muestra también los datos que devolvió el generador
        --probar 500      genera 500 problemas para encontrar casos que fallen
        --jugar           abre el nivel generado en una ventana
    python constructor_niveles.py --exportar niveles.json       # un nivel fijo por plantilla

USO DESDE PYTHON
----------------
    plantilla = cargar_plantilla("plantillas/biseccion.json")
    nivel = generar_nivel(plantilla)              # problema nuevo, resuelto y armado
    nivel = construir_nivel(plantilla, datos)     # o con datos que ya tengas
"""
import argparse
import ast
import glob
import json
import math
import operator
import os
import random
import re
import sys
import traceback
from fractions import Fraction

import generadores
from nivel_generico import validar_nivel

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_PLANTILLAS = os.path.join(BASE, "plantillas")
DECIMALES_DEFECTO = 4
TOLERANCIA_DEFECTO = 1e-6
PRUEBAS_AL_CARGAR = 5           # problemas que se generan al iniciar para detectar errores


class ErrorPlantilla(ValueError):
    """Error en una plantilla o en los datos que recibe. El mensaje dice dónde."""


def _err(ruta, msg):
    raise ErrorPlantilla(f"{ruta}: {msg}")


def _es_numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ===================================================================== datos
def normalizar_datos(v):
    """Convierte lo que devuelva el generador a tipos simples de Python: numpy (escalares y
    arreglos), Fraction y tuplas pasan a int/float/list. Así el generador puede usar numpy."""
    if hasattr(v, "tolist") and not isinstance(v, (str, bytes)):     # numpy
        v = v.tolist()
    if isinstance(v, dict):
        return {str(k): normalizar_datos(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [normalizar_datos(x) for x in v]
    if isinstance(v, Fraction):
        return v.numerator if v.denominator == 1 else float(v)
    if isinstance(v, bool) or v is None or isinstance(v, (int, str)):
        return v
    if isinstance(v, float):
        return v
    try:
        return float(v)                                              # otros números
    except (TypeError, ValueError):
        return str(v)


# =============================================================== expresiones
_BINARIOS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
             ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
             ast.Mod: operator.mod, ast.Pow: operator.pow}
_UNARIOS = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}
_COMPARA = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
            ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}
FUNCIONES = {"abs": abs, "round": round, "min": min, "max": max, "len": len, "sum": sum,
             "sqrt": math.sqrt, "exp": math.exp, "log": math.log,
             "sin": math.sin, "cos": math.cos, "tan": math.tan}
CONSTANTES = {"pi": math.pi, "e": math.e, "True": True, "False": False}
_cache_ast = {}


def evaluar(expr, ctx, ruta):
    """Evalúa una expresión de la plantilla con los datos de `ctx`, sin ejecutar código."""
    if not isinstance(expr, str):
        return expr
    arbol = _cache_ast.get(expr)
    if arbol is None:
        try:
            arbol = ast.parse(expr.strip(), mode="eval").body
        except SyntaxError:
            _err(ruta, f"expresión mal escrita: {expr!r}")
        _cache_ast[expr] = arbol
    try:
        return _ev(arbol, ctx, ruta, expr)
    except ErrorPlantilla:
        raise
    except Exception as e:                      # división entre cero, índice fuera de rango...
        _err(ruta, f"al evaluar {expr!r}: {type(e).__name__}: {e}")


def _ev(n, ctx, ruta, expr):
    ev = lambda x: _ev(x, ctx, ruta, expr)      # noqa: E731
    if isinstance(n, ast.Constant):
        return n.value
    if isinstance(n, ast.Name):
        if n.id in ctx:
            return ctx[n.id]
        if n.id in CONSTANTES:
            return CONSTANTES[n.id]
        disp = ", ".join(sorted(k for k in ctx if not k.startswith("_")))
        _err(ruta, f"en {expr!r} no existe el dato {n.id!r}. Datos disponibles: {disp}")
    if isinstance(n, ast.Attribute):
        base = ev(n.value)
        if isinstance(base, dict) and n.attr in base:
            return base[n.attr]
        claves = ", ".join(base) if isinstance(base, dict) else type(base).__name__
        _err(ruta, f"en {expr!r} no existe '.{n.attr}' (hay: {claves})")
    if isinstance(n, ast.Subscript):
        base, i = ev(n.value), ev(n.slice)
        try:
            return base[i]
        except (KeyError, IndexError, TypeError) as e:
            _err(ruta, f"en {expr!r} no se puede tomar [{i!r}]: {e}")
    if isinstance(n, ast.BinOp) and type(n.op) in _BINARIOS:
        return _BINARIOS[type(n.op)](ev(n.left), ev(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _UNARIOS:
        return _UNARIOS[type(n.op)](ev(n.operand))
    if isinstance(n, ast.BoolOp):
        if isinstance(n.op, ast.And):
            return all(ev(v) for v in n.values)
        return any(ev(v) for v in n.values)
    if isinstance(n, ast.Compare):
        izq = ev(n.left)
        for op, der in zip(n.ops, n.comparators):
            if type(op) not in _COMPARA:
                break
            d = ev(der)
            if not _COMPARA[type(op)](izq, d):
                return False
            izq = d
        else:
            return True
    if isinstance(n, ast.IfExp):
        return ev(n.body) if ev(n.test) else ev(n.orelse)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FUNCIONES \
            and not n.keywords:
        return FUNCIONES[n.func.id](*[ev(a) for a in n.args])
    if isinstance(n, (ast.List, ast.Tuple)):
        return [ev(x) for x in n.elts]
    _err(ruta, f"en {expr!r} hay algo que no se permite en una expresión "
               f"({type(n).__name__}); ver el formato en constructor_niveles.py")


# ================================================================== formato
def formatear(v, decimales):
    """Número -> texto corto: 3, 2.5, 0.3333 (sin ceros de más)."""
    if isinstance(v, bool):
        return "Sí" if v else "No"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return str(v)
        r = round(v, decimales)
        if r == int(r):
            return str(int(r))
        return f"{r:.{decimales}f}".rstrip("0").rstrip(".")
    if isinstance(v, list):
        return "[" + ", ".join(formatear(x, decimales) for x in v) + "]"
    return str(v)


_LLAVES = re.compile(r"\{\{|\}\}|\{([^{}]+)\}")
_ESPEC = re.compile(r"^[<>^=+\- #0-9,._]*[bdeEfFgGn%]?$")


def rellenar(texto, ctx, ruta, conf):
    """Sustituye {expresión} y {expresión:formato} dentro de un texto."""
    if not isinstance(texto, str):
        _err(ruta, f"se esperaba un texto (se recibió {texto!r})")

    def cambio(m):
        if m.group(0) == "{{":
            return "{"
        if m.group(0) == "}}":
            return "}"
        cuerpo, espec = m.group(1), None
        if ":" in cuerpo:
            e, s = cuerpo.rsplit(":", 1)
            if _ESPEC.match(s.strip()):
                cuerpo, espec = e, s.strip()
        v = evaluar(cuerpo, ctx, ruta)
        if espec:
            try:
                return format(v, espec)
            except (ValueError, TypeError) as e:
                _err(ruta, f"formato {espec!r} no válido para {v!r}: {e}")
        return formatear(v, conf["decimales"])
    return _LLAVES.sub(cambio, texto)


# =================================================================== tokens
def _casilla(valor, opciones, ruta, conf):
    """Casilla para el nivel final a partir del valor correcto ya calculado."""
    valor = normalizar_datos(valor)
    if isinstance(valor, str):
        out = {"in": valor}
        texto = valor
    elif _es_numero(valor):
        if isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor)):
            _err(ruta, f"la respuesta de la casilla no es un número válido ({valor})")
        dec = opciones.get("decimales")
        if dec is not None:
            valor = round(valor, dec)
            tol = opciones.get("tol", 0.5 * 10 ** -dec + 1e-12)
        else:
            tol = opciones.get("tol", conf["tolerancia"])
        if isinstance(valor, float) and valor == int(valor):
            valor = int(valor)
        out = {"in": valor, "tol": tol}
        texto = formatear(valor, dec if dec is not None else conf["decimales"])
    else:
        _err(ruta, f"la respuesta de una casilla debe ser número o texto (se obtuvo {valor!r})")
    n = len(texto)
    out["limite"] = opciones.get("limite", max(8, n + 3))
    if "ancho" in opciones:
        out["ancho"] = opciones["ancho"]
    elif n > 4:                                  # que quepa el número (unidades de nivel_generico)
        out["ancho"] = int(8.5 * n + 16)
    return out


def _token(t, ctx, ruta, conf):
    if isinstance(t, str):
        return rellenar(t, ctx, ruta, conf)
    if _es_numero(t):
        return t
    if isinstance(t, dict) and "matriz" in t:
        return {"matriz": _matriz(t, ctx, ruta, conf)}
    if isinstance(t, dict) and "in" in t:
        return _casilla(evaluar(t["in"], ctx, ruta), t, ruta, conf)
    _err(ruta, 'un token debe ser texto, número, {"in": ...} o {"matriz": ...}')


def _matriz(t, ctx, ruta, conf):
    m = t["matriz"]
    if isinstance(m, list) and all(isinstance(f, list) for f in m) and not isinstance(m, str) \
            and "casillas" not in t:
        # escrita a mano: cada celda es un token
        return [[_token(c, ctx, f"{ruta}.matriz[{i}][{j}]", conf) for j, c in enumerate(f)]
                for i, f in enumerate(m)]
    valores = normalizar_datos(evaluar(m, ctx, ruta))
    if not (isinstance(valores, list) and valores and all(isinstance(f, list) and f for f in valores)):
        _err(ruta, f"{m!r} debe dar una matriz (lista de listas); se obtuvo {valores!r}")
    cas = t.get("casillas", "todas")
    if cas == "todas":
        editable = lambda i, j: True                              # noqa: E731
    elif cas == "ninguna":
        editable = lambda i, j: False                             # noqa: E731
    else:
        lista = evaluar(cas, ctx, ruta) if isinstance(cas, str) else cas
        try:
            pares = {(int(p[0]), int(p[1])) for p in lista}
        except (TypeError, ValueError, IndexError):
            _err(ruta, f'"casillas" debe ser "todas", "ninguna" o una lista [[fila, col], ...] '
                       f"(se obtuvo {lista!r})")
        editable = lambda i, j: (i, j) in pares                   # noqa: E731
    dec = t.get("decimales", conf["decimales"])
    res = []
    for i, fila in enumerate(valores):
        r = []
        for j, v in enumerate(fila):
            if editable(i, j):
                r.append(_casilla(v, t, f"{ruta}[{i}][{j}]", conf))
            else:
                r.append(v if isinstance(v, int) and not isinstance(v, bool) else formatear(v, dec))
        res.append(r)
    return res


# ======================================================= repetir y condiciones
def _expandir(lista, ctx, ruta, clave):
    """Recorre pasos, filas o textos de intro resolviendo "repetir" y "si".
    Devuelve [(elemento, contexto, ruta), ...]."""
    if not isinstance(lista, list):
        _err(ruta, "debe ser una lista")
    res = []
    for k, el in enumerate(lista):
        r = f"{ruta}[{k}]"
        if isinstance(el, dict) and "repetir" in el:
            if clave not in el:
                _err(r, f'"repetir" necesita la clave "{clave}" con lo que se repite')
            if "si" in el and not evaluar(el["si"], ctx, f"{r}.si"):
                continue
            seq = evaluar(el["repetir"], ctx, f"{r}.repetir")
            if _es_numero(seq):
                seq = list(range(int(seq)))
            if not isinstance(seq, list):
                _err(f"{r}.repetir", f"{el['repetir']!r} debe ser una lista o un entero "
                                     f"(se obtuvo {type(seq).__name__})")
            if "max" in el:
                seq = seq[:int(el["max"])]
            como = el.get("como", "elem")
            for idx, item in enumerate(seq):
                sub = dict(ctx)
                sub.update({como: item, "idx": idx, "num": idx + 1, "total": len(seq)})
                res.append((el[clave], sub, f"{r}[{como}={idx}]"))
            continue
        if isinstance(el, dict) and "si" in el and clave in el:
            if evaluar(el["si"], ctx, f"{r}.si"):
                res.append((el[clave], ctx, r))
            continue
        res.append((el, ctx, r))
    return res


# ================================================================ construir
def construir_nivel(plantilla, datos, ruta="plantilla"):
    """Arma el nivel (formato de nivel_generico) con la plantilla y los datos del resolvedor."""
    if not isinstance(datos, dict):
        _err(ruta, f"el generador debe devolver un diccionario (devolvió {type(datos).__name__})")
    conf = {"decimales": int(plantilla.get("decimales", DECIMALES_DEFECTO)),
            "tolerancia": float(plantilla.get("tolerancia", TOLERANCIA_DEFECTO))}
    ctx = normalizar_datos(datos)

    nivel = {
        "titulo": rellenar(plantilla["titulo"], ctx, f"{ruta}.titulo", conf),
        "instruccion": rellenar(plantilla["instruccion"], ctx, f"{ruta}.instruccion", conf),
        "tiempo": plantilla.get("tiempo", 600),
    }
    if "intro" in plantilla:
        nivel["intro"] = [rellenar(t, c, r, conf)
                          for t, c, r in _expandir(plantilla["intro"], ctx, f"{ruta}.intro", "texto")]
    pasos = []
    for paso, c, r in _expandir(plantilla["pasos"], ctx, f"{ruta}.pasos", "paso"):
        if not isinstance(paso, dict):
            _err(r, "cada paso debe ser un objeto {\"titulo\": ..., \"filas\": [...]}")
        c = dict(c, paso=len(pasos) + 1)
        filas = []
        for fila, c2, r2 in _expandir(paso.get("filas"), c, f"{r}.filas", "fila"):
            if not isinstance(fila, list):
                _err(r2, "cada fila debe ser una lista de tokens")
            filas.append([_token(t, c2, f"{r2}[{j}]", conf) for j, t in enumerate(fila)])
        if not filas:
            continue                             # todas sus filas quedaron omitidas por "si"
        pasos.append({"titulo": rellenar(paso.get("titulo", ""), c, f"{r}.titulo", conf),
                      "filas": filas})
    nivel["pasos"] = pasos
    validar_nivel(nivel, f"nivel construido con {ruta}")
    return nivel


def es_plantilla(contenido):
    return isinstance(contenido, dict) and "generador" in contenido


def generar_datos(plantilla, semilla=None):
    """Llama al generador de la plantilla: problema aleatorio + solución."""
    rng = random.Random(semilla)
    gen = generadores.obtener(plantilla["generador"])
    datos = gen(rng, **plantilla.get("parametros", {}))
    if not isinstance(datos, dict):
        raise ErrorPlantilla(f"el generador {plantilla['generador']!r} debe devolver un "
                             f"diccionario (devolvió {type(datos).__name__})")
    return normalizar_datos(datos)


def generar_nivel(plantilla, semilla=None):
    """Problema nuevo -> resuelto -> nivel listo para nivel_generico."""
    return construir_nivel(plantilla, generar_datos(plantilla, semilla),
                           plantilla.get("_archivo", "plantilla"))


# ===================================================================== carga
def validar_plantilla(p, ruta):
    if not isinstance(p, dict):
        _err(ruta, "la plantilla debe ser un objeto { ... }")
    for k in ("titulo", "instruccion", "generador"):
        if not isinstance(p.get(k), str) or not p[k].strip():
            _err(ruta, f'falta "{k}" (texto)')
    if p["generador"] not in generadores.nombres():
        _err(f"{ruta}.generador", f"no hay un generador registrado como {p['generador']!r}. "
                                  f"Registrados: {', '.join(generadores.nombres()) or '(ninguno)'}")
    if "nivel" in p and (not isinstance(p["nivel"], str) or not p["nivel"].strip()):
        _err(f"{ruta}.nivel", "debe ser el nombre del nivel en estructura.json")
    if not isinstance(p.get("parametros", {}), dict):
        _err(f"{ruta}.parametros", "debe ser un objeto { ... }")
    if not (isinstance(p.get("pasos"), list) and p["pasos"]):
        _err(f"{ruta}.pasos", "debe ser una lista con al menos un paso")
    for k in ("decimales",):
        if k in p and not (isinstance(p[k], int) and 0 <= p[k] <= 10):
            _err(f"{ruta}.{k}", "debe ser un entero entre 0 y 10")


def cargar_plantilla(ruta):
    with open(ruta, encoding="utf-8") as f:
        p = json.load(f)
    nombre = os.path.basename(ruta)
    validar_plantilla(p, nombre)
    p["_archivo"] = nombre
    return p


def cargar_plantillas(carpeta=CARPETA_PLANTILLAS, pruebas=PRUEBAS_AL_CARGAR):
    """Carga todas las plantillas de la carpeta y genera algunos problemas de prueba con cada
    una. Las que fallan se dejan fuera (con aviso), así el juego arranca aunque una esté mal.
    Devuelve (plantillas, avisos)."""
    plantillas, avisos = [], []
    for ruta in sorted(glob.glob(os.path.join(carpeta, "*.json"))):
        nombre = os.path.basename(ruta)
        try:
            p = cargar_plantilla(ruta)
            for s in range(pruebas):
                generar_nivel(p, semilla=s)
        except json.JSONDecodeError as e:
            avisos.append(f"{nombre}: JSON mal formado ({e}); se ignora")
        except Exception as e:
            avisos.append(f"{nombre}: {e}; se ignora")
        else:
            plantillas.append(p)
    return plantillas, avisos


def nombre_enlace(contenido):
    """Nombre con que un nivel (plantilla o estático) se enlaza con estructura.json."""
    return contenido.get("nivel") or contenido["titulo"]


# ================================================================ terminal
def _probar(p, n, desde=0):
    fallos = 0
    for s in range(desde, desde + n):
        try:
            generar_nivel(p, semilla=s)
        except Exception as e:
            fallos += 1
            if fallos <= 3:
                print(f"   semilla {s}: {e}")
    estado = "OK" if not fallos else f"{fallos} FALLOS"
    print(f"  {p['_archivo']:<34} {n} problemas  {estado}")
    return fallos


def main():
    ap = argparse.ArgumentParser(description="Genera niveles a partir de plantillas.")
    ap.add_argument("plantilla", nargs="?", help="archivo de plantilla (si falta: todas)")
    ap.add_argument("--semilla", type=int, help="semilla para repetir el mismo problema")
    ap.add_argument("--datos", action="store_true", help="mostrar los datos del generador")
    ap.add_argument("--probar", type=int, metavar="N", help="generar N problemas buscando fallos")
    ap.add_argument("--jugar", action="store_true", help="abrir el nivel generado")
    ap.add_argument("--exportar", metavar="ARCHIVO", help="guardar un nivel por plantilla en ARCHIVO")
    a = ap.parse_args()

    try:
        if a.plantilla:
            plantillas = [cargar_plantilla(a.plantilla)]
        else:
            plantillas = []
            for ruta in sorted(glob.glob(os.path.join(CARPETA_PLANTILLAS, "*.json"))):
                plantillas.append(cargar_plantilla(ruta))
    except (OSError, ValueError) as e:
        sys.exit(f"Error: {e}")

    if a.exportar:
        niveles = []
        for p in plantillas:
            try:
                niveles.append(generar_nivel(p, a.semilla))
            except Exception as e:
                print(f"{p['_archivo']}: {e}")
        with open(a.exportar, "w", encoding="utf-8") as f:
            json.dump({"niveles": niveles}, f, indent=2, ensure_ascii=False)
        print(f"{len(niveles)} niveles guardados en {a.exportar}")
        return

    if not a.plantilla or a.probar:
        print("Probando plantillas:")
        fallos = sum(_probar(p, a.probar or 100) for p in plantillas)
        sys.exit(1 if fallos else 0)

    p = plantillas[0]
    semilla = a.semilla if a.semilla is not None else random.randrange(10 ** 6)
    try:
        datos = generar_datos(p, semilla)
        nivel = construir_nivel(p, datos, p["_archivo"])
    except Exception:
        traceback.print_exc()
        sys.exit(f"\nFalló con --semilla {semilla}")
    if a.datos:
        print("DATOS DEL GENERADOR:")
        print(json.dumps(datos, indent=2, ensure_ascii=False))
        print("\nNIVEL:")
    print(json.dumps(nivel, indent=2, ensure_ascii=False))
    print(f"(semilla {semilla})", file=sys.stderr)
    if a.jugar:
        import ventana
        import nivel_generico
        ventana.PANTALLA_COMPLETA = False
        ventana.CERRAR_AL_PERDER_FOCO = False      # para poder ver la terminal mientras pruebas
        nivel_generico.Juego([nivel]).run()


if __name__ == "__main__":
    main()
