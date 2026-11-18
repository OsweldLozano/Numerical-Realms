"""
Creador de niveles del submapa Mínimos Cuadrados.

Cada función registrada:
    1. genera una tabla de puntos aleatoria: x enteras consecutivas y y = (un modelo con
       coeficientes enteros) + un poco de ruido, para que el ajuste no sea exacto;
    2. arma las ecuaciones normales con el resolvedor de Vanessa
       (resolvedores/minimos_cuadrados.py) y resuelve el sistema con su GaussJordan
       (resolvedores/lineales.py);
    3. agrega lo que usan las plantillas: las sumatorias con nombre legible (Σx², Σxy...),
       la matriz, los coeficientes y las tolerancias.

TOLERANCIAS: en los modelos polinomiales todas las sumatorias son enteras. En los modelos con
función (sen, e^x, ln...) el jugador suma valores redondeados a 4 decimales, así que cada
sumatoria lleva una tolerancia según cuánto pesa f(x) en sus términos. La de cada coeficiente
se obtiene simulando al jugador: calcula f(x) con 4 decimales, arma las sumatorias con esos
valores y resuelve el sistema redondeando a DECIMALES_SISTEMA (6) decimales en cada operación
(la plantilla le pide al jugador usar al menos 6); la tolerancia es 3 veces lo que se aleja,
más un margen. Se descartan los problemas en los que eso pasa de TOL_MAXIMA (sistemas tan
sensibles que ni con cuentas cuidadosas se llega al resultado). Por eso raíz(x) no se usa en
el modelo cuadrático con función: con x = 1...6 se parece demasiado a 1, x y x².

Plantillas: plantillas/linea_recta.json, cuadratica.json, cubica.json,
lineal_con_funcion.json y cuadratica_con_funcion.json.
"""
from fractions import Fraction

import numpy as np
import sympy as sp

from generadores import registrar
from resolvedores import lineales as res_lineales
from resolvedores import minimos_cuadrados as res

ERROR = 5e-5             # error de un número escrito con 4 decimales
TOL_MAXIMA = 0.01        # tolerancia máxima aceptable para un coeficiente
DECIMALES_SISTEMA = 6    # decimales que se suponen al resolver el sistema
Y_MAXIMA = 600           # valor máximo de |y| en la tabla

NOMBRES = {"x": "Σx", "x**2": "Σx²", "x**3": "Σx³", "x**4": "Σx⁴", "x**5": "Σx⁵", "x**6": "Σx⁶",
           "y": "Σy", "x*y": "Σxy", "(x**2)*y": "Σx²y", "(x**3)*y": "Σx³y",
           "f(x)": "Σf(x)", "x*f(x)": "Σx·f(x)", "(x**2)*f(x)": "Σx²·f(x)",
           "f(x)**2": "Σf(x)²", "y*f(x)": "Σy·f(x)"}

# f(x): (texto para sympy, texto para mostrar, función de numpy)
FUNCIONES = [
    ("sin(x)",  "sen(x)",   np.sin),
    ("cos(x)",  "cos(x)",   np.cos),
    ("exp(x)",  "e^x",      np.exp),
    ("log(x)",  "ln(x)",    np.log),
    ("sqrt(x)", "raíz(x)",  np.sqrt),
    ("1/x",     "1/x",      lambda x: 1 / x),
]


def _num(v):
    v = float(v)
    return int(v) if v == int(v) else v


def _resolver_redondeando(M, dec=DECIMALES_SISTEMA):
    """Gauss-Jordan redondeando cada resultado a `dec` decimales (como el jugador).
    Devuelve None si un pivote se vuelve 0 por el redondeo."""
    M = [[round(float(v), dec) for v in fila] for fila in M]
    n = len(M)
    for k in range(n):
        p = M[k][k]
        if p == 0:
            return None
        M[k] = [round(v / p, dec) for v in M[k]]
        for i in range(n):
            if i != k:
                f = M[i][k]
                M[i] = [round(a - f * c, dec) for a, c in zip(M[i], M[k])]
    return [fila[n] for fila in M]


def _tolerancia_suma(clave, xs, ys, fs):
    """Error al sumar términos calculados con f(x) redondeada a 4 decimales."""
    if fs is None or "f(x)" not in clave:
        return 1e-4
    peso = {"f(x)": lambda x, y, f: 1, "x*f(x)": lambda x, y, f: abs(x),
            "(x**2)*f(x)": lambda x, y, f: x * x, "f(x)**2": lambda x, y, f: 2 * abs(f),
            "y*f(x)": lambda x, y, f: abs(y)}[clave]
    return sum(peso(x, y, f) for x, y, f in zip(xs, ys, fs)) * ERROR * 1.5 + 2e-4


def _normales(xs, ys, grado, fs):
    """Ecuaciones normales calculadas aparte (columnas 1, x, ..., x^grado y f(x) si hay)."""
    cols = [np.array(xs, dtype=float) ** k for k in range(grado + 1)]
    if fs is not None:
        cols.append(np.array(fs, dtype=float))
    X = np.column_stack(cols)
    return np.column_stack([X.T @ X, X.T @ np.array(ys, dtype=float)])


def _armar(rng, metodo, modelo, xs, grado, funcion=None, ruido=2):
    """Genera y, revisa que el sistema sea cómodo y lo resuelve. Devuelve None si no sirve.
    Las revisiones rápidas (con numpy) van primero; el resolvedor (que usa sympy y es más
    lento) solo se llama con un problema que ya las pasó."""
    fs = None if funcion is None else funcion[2](np.array(xs, dtype=float))
    ys = []
    for i, x in enumerate(xs):
        y = modelo(x, None if fs is None else fs[i]) + rng.randint(-ruido, ruido)
        ys.append(int(round(y)))
    if max(abs(y) for y in ys) > Y_MAXIMA or len(set(ys)) < 3:
        return None

    # 1) revisión rápida: condición del sistema y simulación del jugador
    M = _normales(xs, ys, grado, fs)
    if np.linalg.cond(M[:, :-1]) > 1e9:
        return None
    coef = np.linalg.solve(M[:, :-1], M[:, -1])
    # lo que se aleja el jugador: sistema exacto resuelto redondeando, y sistema con f(x)
    # redondeada resuelto redondeando
    # (las sumatorias se escriben con 4 decimales; el sistema se resuelve con 6)
    simulaciones = [_resolver_redondeando(np.round(M, 4))]
    if fs is not None:
        simulaciones.append(_resolver_redondeando(np.round(_normales(xs, ys, grado, np.round(fs, 4)), 4)))
    if any(s is None for s in simulaciones):
        return None
    desvio = [max(abs(sim[i] - c) for sim in simulaciones) for i, c in enumerate(coef)]
    if max(3 * d + 5e-4 for d in desvio) > TOL_MAXIMA:
        return None

    # 2) el resolvedor de Vanessa arma el sistema; GaussJordan lo resuelve
    tabla = [[x, y] for x, y in zip(xs, ys)]
    datos = metodo(tabla) if funcion is None else metodo(tabla, funcion[0])
    M_res = np.array(datos["matriz"], dtype=float)
    if not np.allclose(M_res, M):
        raise ValueError("la matriz del resolvedor no coincide con las ecuaciones normales")
    sol = res_lineales.GaussJordan([[Fraction(v) if isinstance(v, (int, Fraction)) else Fraction(float(v))
                                     for v in fila] for fila in datos["matriz"]])
    if "error" in sol:
        return None
    coef = [float(v) for v in sol["incognitas"]]
    if not np.allclose(coef, np.linalg.solve(M[:, :-1], M[:, -1]), atol=1e-7):
        raise ValueError("Gauss-Jordan no coincide con numpy")

    sumas = [{"nombre": NOMBRES[k], "valor": _num(v),
              "tol": _tolerancia_suma(k, xs, ys, fs)} for k, v in datos["sumatoria"].items()]
    coeficientes = [{"nombre": f"a{i}", "valor": c, "tol": 3 * d + 5e-4}
                    for i, (c, d) in enumerate(zip(coef, desvio))]
    return {"puntos": tabla, "n": len(xs), "sumas": sumas,
            "matriz": [[_num(v) for v in fila] for fila in M_res.tolist()],
            "tol_matriz": max(s["tol"] for s in sumas), "coeficientes": coeficientes}


def _generar(rng, metodo, grado, n, inicio, funciones=None):
    """Elige primero la función (si el modelo lleva) y luego busca coeficientes con los que el
    sistema sea cómodo; así todas las funciones aparecen parejo."""
    for _ in range(20):
        f = rng.choice(funciones) if funciones else None
        for _ in range(80):
            x0 = rng.choice(inicio)
            xs = list(range(x0, x0 + n))
            a = [rng.randint(-3, 5)] + [rng.choice([-2, -1, 1, 2, 3]) for _ in range(grado)]
            extra = rng.choice([-3, -2, -1, 1, 2, 3, 4])
            modelo = (lambda x, fx: sum(c * x ** k for k, c in enumerate(a)) + (extra * fx if f else 0))  # noqa: E731
            d = _armar(rng, metodo, modelo, xs, grado, f)
            if d:
                if f:
                    d["funcion"] = f"f(x) = {f[1]}" + ("  (en radianes)" if f[0] in ("sin(x)", "cos(x)") else "")
                    d["f_texto"] = f[1]
                return d
    raise RuntimeError("no se pudo generar una tabla con un sistema cómodo de resolver")


@registrar("linea_recta")
def linea_recta(rng):
    return _generar(rng, res.LineaRecta, 1, 5, [0, 1, 2])


@registrar("cuadratica")
def cuadratica(rng):
    return _generar(rng, res.Cuadratica, 2, 5, [-2, -1, 0])


@registrar("cubica")
def cubica(rng):
    return _generar(rng, res.Cubica, 3, 6, [-2, -1, 0])


@registrar("lineal_con_funcion")
def lineal_con_funcion(rng):
    return _generar(rng, res.LinealFuncion, 1, 5, [1, 2], FUNCIONES)


@registrar("cuadratica_con_funcion")
def cuadratica_con_funcion(rng):
    return _generar(rng, res.CuadraticaFuncion, 2, 6, [1, 2],
                    [f for f in FUNCIONES if f[0] != "sqrt(x)"])
