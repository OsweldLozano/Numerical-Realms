"""
Creador de niveles del submapa Ecuaciones No Lineales.

Cada función registrada:
    1. genera una función aleatoria (f(x), o g(x) en punto fijo) de familias con una raíz que
       no es entera, para que el método tenga trabajo;
    2. la resuelve con el resolvedor de Vanessa (resolvedores/no_lineales.py), que elige solo
       el intervalo (tabulación) o usa sus puntos iniciales fijos (Newton x0 = 1, secante
       x0 = 0 y x1 = 1, punto fijo x0 = 0);
    3. revisa que el método haya llegado cerca de una raíz (si no, genera otra función) y
       agrega lo que usan las plantillas: el texto de cada sustitución, f(x) en cada punto, el
       nuevo intervalo y las tolerancias.

TOLERANCIAS: en cada iteración se muestran los valores anteriores con 4 decimales y el jugador
evalúa con esos números redondeados. Al evaluar f, el error que eso produce es |f'(x)|·0.00005,
así que cada evaluación lleva su tolerancia calculada con la derivada ("tol_f..."). Las
aproximaciones (c, x) llevan una tolerancia fija en la plantilla.

Plantillas: plantillas/grafica.json, biseccion.json, falsa_posicion.json,
newton_raphson.json, punto_fijo.json y secante.json.
"""
import math

import sympy as sp

from generadores import registrar
from generadores._util import num
from resolvedores import no_lineales as res

X = sp.Symbol("x")
ERROR_X = 5e-5           # error de un número mostrado con 4 decimales


# ================================================================= funciones
def _no_es_potencia(k, p):
    r = round(k ** (1 / p))
    return r ** p != k


def funcion_f(rng):
    """f(x) con raíz no entera. Sirve para gráfica, bisección, falsa posición, Newton y secante."""
    while True:
        f = _funcion_f(rng)
        ev = _evaluador(f)
        if all(abs(ev(i)) > 1e-12 for i in range(-10, 101) if not (f.has(sp.exp) and i > 30)):
            return f                                  # ninguna raíz entera


def _funcion_f(rng):
    tipo = rng.choice(["cubica", "cubica_lineal", "cuadratica", "exponencial", "coseno", "exp_menos"])
    if tipo == "cubica":
        k = rng.choice([k for k in range(2, 41) if _no_es_potencia(k, 3)])
        return X ** 3 - k
    if tipo == "cubica_lineal":
        return X ** 3 + rng.choice([-2, -1, 1, 2, 3]) * X - rng.randint(2, 15)
    if tipo == "cuadratica":
        k = rng.choice([k for k in range(2, 31) if _no_es_potencia(k, 2)])
        return X ** 2 - k
    if tipo == "exponencial":
        return sp.exp(X) - rng.randint(2, 15)
    if tipo == "coseno":
        return X - rng.choice([1, 2]) * sp.cos(X)
    return sp.exp(-X) - X


def funcion_g(rng):
    """g(x) para punto fijo (x = g(x)), que converge desde x0 = 0."""
    tipo = rng.choice(["coseno", "exp", "raiz", "cuadratica", "fraccion"])
    if tipo == "coseno":
        return sp.cos(X)
    if tipo == "exp":
        return sp.exp(-X)
    if tipo == "raiz":
        return sp.sqrt(X + rng.randint(1, 12))
    if tipo == "cuadratica":
        k, m = rng.choice([(1, 3), (1, 4), (2, 5), (1, 5), (2, 6), (3, 7)])
        return (X ** 2 + k) / m
    return 1 / (X + rng.randint(1, 3))


# ============================================================ textos y números
def bonito(expr):
    """Expresión de sympy -> texto legible: 3·x² - 2, e^(-x), raíz(x + 2)."""
    t = str(expr)
    for a, b in (("**2", "²"), ("**3", "³"), ("exp(", "e^("), ("sqrt(", "raíz("), ("*", "·")):
        t = t.replace(a, b)
    return t


def sustituir(expr, v):
    """Texto de la expresión con x reemplazada por el número (4 decimales; paréntesis si es
    negativo o si va elevado o multiplicado)."""
    t = num(float(v))
    if t.startswith("-"):
        t = f"({t})"
    texto = bonito(expr)
    # x elevada o multiplicada por un número: siempre entre paréntesis para que se lea bien
    texto = texto.replace("·x", f"·({t})" if not t.startswith("(") else f"·{t}")
    texto = texto.replace("x²", f"({t})²" if not t.startswith("(") else f"{t}²")
    texto = texto.replace("x³", f"({t})³" if not t.startswith("(") else f"{t}³")
    return texto.replace("x", t)


def _evaluador(expr):
    return sp.lambdify(X, expr, "math")


def _tol(derivada, v):
    """Tolerancia al evaluar con v redondeado a 4 decimales."""
    return abs(derivada(v)) * ERROR_X * 1.5 + 1e-4


def _float(v):
    v = float(v)
    return int(v) if v == int(v) else v


def _intentar(rng, crear, revisar, intentos=500):
    """Genera funciones hasta que el resultado pase la revisión."""
    for _ in range(intentos):
        expr = crear(rng)
        try:
            datos = revisar(expr)
        except (ValueError, ZeroDivisionError, OverflowError, TypeError):
            continue
        if datos is not None:
            return expr, datos
    raise RuntimeError("no se pudo generar una función que el método resuelva")


# ==================================================================== gráfica
@registrar("grafica")
def grafica(rng):
    def revisar(f):
        d = res.Grafico(f)
        return d if d else None
    f, d = _intentar(rng, funcion_f, revisar)
    ev = _evaluador(f)
    puntos = [{"x": p["x"], "fx": float(ev(p["x"])), "texto": sustituir(f, p["x"])} for p in d["puntos"]]
    return {"funcion": f"f(x) = {bonito(f)}", "puntos": puntos,
            "a": d["raiz"]["a"], "b": d["raiz"]["b"]}


# ============================================================ bisección y falsa posición
def _intervalo_nuevo(fa, fx, a, b, x):
    return (a, x) if fa * fx < 0 else (x, b)


@registrar("biseccion")
def biseccion(rng):
    def revisar(f):
        d = res.Bisectriz(f)
        if not d or abs(d["iteraciones"][-1]["x"] - d["raiz"]["a"]) < 1e-9:
            return None
        return d
    f, d = _intentar(rng, funcion_f, revisar)
    ev, dev = _evaluador(f), _evaluador(sp.diff(f, X))
    its = []
    for it in d["iteraciones"]:
        a, b, c = it["a"], it["b"], it["x"]
        fa, fc = ev(a), ev(c)
        a2, b2 = _intervalo_nuevo(fa, fc, a, b, c)
        its.append({"a": _float(a), "b": _float(b), "c": c, "fc": fc,
                    "texto_fc": sustituir(f, c), "tol_fc": _tol(dev, c),
                    "a_nuevo": _float(a2), "b_nuevo": _float(b2),
                    "error": float(it["error"]["error"])})
    return {"funcion": f"f(x) = {bonito(f)}", "a": d["raiz"]["a"], "b": d["raiz"]["b"],
            "iteraciones": its, "raiz": its[-1]["c"]}


@registrar("falsa_posicion")
def falsa_posicion(rng):
    def revisar(f):
        d = res.FalsaPosicion(f)
        if not d or abs(float(_evaluador(f)(d["valor_final"]))) > 0.05:
            return None
        return d
    f, d = _intentar(rng, funcion_f, revisar)
    ev, dev = _evaluador(f), _evaluador(sp.diff(f, X))
    its = []
    for it in d["iteraciones"][1:]:                    # la 0 son los datos iniciales
        a, b, x = it["a"], it["b"], it["x"]
        fa, fb, fx = ev(a), ev(b), ev(x)
        a2, b2 = _intervalo_nuevo(fa, fx, a, b, x)
        its.append({"a": _float(a), "b": _float(b), "fa": fa, "fb": fb, "x": x, "fx": fx,
                    "texto_fa": sustituir(f, a), "texto_fb": sustituir(f, b), "texto_fx": sustituir(f, x),
                    "tol_fa": _tol(dev, a), "tol_fb": _tol(dev, b), "tol_fx": _tol(dev, x),
                    "a_nuevo": _float(a2), "b_nuevo": _float(b2),
                    "error": float(it["error"]["error"])})
    return {"funcion": f"f(x) = {bonito(f)}", "a": d["raiz"]["a"], "b": d["raiz"]["b"],
            "iteraciones": its, "raiz": float(d["valor_final"])}


# ============================================================= Newton-Raphson
@registrar("newton_raphson")
def newton_raphson(rng):
    def revisar(f):
        d = res.NewtonRaphson(f)
        if len(d["iteraciones"]) < 3 or abs(float(_evaluador(f)(d["valor_final"]))) > 1e-6:
            return None
        return d
    f, d = _intentar(rng, funcion_f, revisar)
    fp = sp.diff(f, X)
    dev, ddev = _evaluador(fp), _evaluador(sp.diff(fp, X))
    its = []
    for it in d["iteraciones"][1:]:
        x0 = it["x"]["x0"]
        its.append({"x0": x0, "fx": float(it["x"]["f(x)"]), "fpx": float(it["x"]["f'(x)"]),
                    "texto_fx": sustituir(f, x0), "texto_fpx": sustituir(fp, x0),
                    "tol_fx": _tol(dev, x0), "tol_fpx": _tol(ddev, x0),
                    "x1": float(it["x"]["xi"]), "error": float(it["error"]["error"])})
    return {"funcion": f"f(x) = {bonito(f)}", "derivada": f"f'(x) = {bonito(fp)}",
            "iteraciones": its, "raiz": float(d["valor_final"])}


# ================================================================ punto fijo
@registrar("punto_fijo")
def punto_fijo(rng):
    def revisar(g):
        d = res.PuntoFijo(g)
        ultimo = d["iteraciones"][-1]["error"]["error"]
        if len(d["iteraciones"]) < 4 or ultimo > 0.05:
            return None
        return d
    g, d = _intentar(rng, funcion_g, revisar)
    dev = _evaluador(sp.diff(g, X))
    its = []
    for it in d["iteraciones"][1:]:
        x0 = it["error"]["x0"]
        its.append({"x0": _float(x0), "x1": float(it["xi"]), "texto_g": sustituir(g, x0),
                    "tol_g": _tol(dev, x0), "error": float(it["error"]["error"])})
    return {"funcion": f"x = g(x) = {bonito(g)}", "iteraciones": its,
            "raiz": float(d["valor_final"])}


# ==================================================================== secante
@registrar("secante")
def secante(rng):
    def revisar(f):
        d = res.Secante(f)
        if len(d["iteraciones"]) < 4 or abs(float(_evaluador(f)(d["valor_final"]))) > 0.01:
            return None
        return d
    f, d = _intentar(rng, funcion_f, revisar)
    dev = _evaluador(sp.diff(f, X))
    its = []
    for k, it in enumerate(d["iteraciones"][2:], start=2):     # 0 y 1 son x0 y x1
        xa, xb = it["x"]["x0"], it["x"]["x1"]
        its.append({"i": k, "xa": _float(xa), "xb": _float(xb),
                    "fa": float(it["x"]["f(x0)"]), "fb": float(it["x"]["f(x1)"]),
                    "texto_fa": sustituir(f, xa), "texto_fb": sustituir(f, xb),
                    "tol_fa": _tol(dev, xa), "tol_fb": _tol(dev, xb),
                    "x": float(it["x"]["xi"]), "error": float(it["error"]["error"])})
    return {"funcion": f"f(x) = {bonito(f)}", "iteraciones": its,
            "raiz": float(d["valor_final"])}
