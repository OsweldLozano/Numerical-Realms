import sympy as sp

from generadores import registrar
from generadores._util import num
from resolvedores import edo as res

Y, T, YP = sp.symbols("y t yp")

# y' = f(y, t): (expresión para sympy, texto para mostrar, texto de la sustitución)
FUNCIONES = [
    ("t + y",      "t + y",      "{t} + {y}"),
    ("y - t",      "y - t",      "{y} - {t}"),
    ("2*t - y",    "2t - y",     "2·{t} - {y}"),
    ("t*y",        "t·y",        "{t}·{y}"),
    ("y + t**2",   "y + t²",     "{y} + {t}²"),
    ("t - 2*y",    "t - 2y",     "{t} - 2·{y}"),
    ("t**2 - y",   "t² - y",     "{t}² - {y}"),
    ("1 - y",      "1 - y",      "1 - {y}"),
    ("y*(1 + t)",  "y·(1 + t)",  "{y}·(1 + {t})"),
]

# y'' = f(y', y, t)
FUNCIONES_2 = [
    ("-y",              "-y",              "-{y}"),
    ("-yp - y",         "-y' - y",         "-{yp} - {y}"),
    ("t - y",           "t - y",           "{t} - {y}"),
    ("yp + 2*y",        "y' + 2y",         "{yp} + 2·{y}"),
    ("t - 2*yp - y",    "t - 2y' - y",     "{t} - 2·{yp} - {y}"),
    ("t*yp - y",        "t·y' - y",        "{t}·{yp} - {y}"),
]


def _n(v):
    t = num(float(v))
    return f"({t})" if t.startswith("-") else t


def _redondear(v):
    v = float(v)
    r = round(v, 10)
    return int(r) if r == int(r) else r


def generar_problema(rng, orden_superior=False):
    expr, texto, sust = rng.choice(FUNCIONES_2 if orden_superior else FUNCIONES)
    p = {"expresion": expr, "texto": texto, "sust": sust,
         "h": rng.choice([0.1, 0.1, 0.2]),
         "t0": rng.choice([0, 0, 1]),
         "y0": rng.choice([1, 1, 2, 0.5])}
    if orden_superior:
        p["yp0"] = rng.choice([0, 1, -1, 2])
        p["y0"] = rng.choice([0, 1, 1, 2])
    return p


def _f(p):
    if "yp0" in p:
        return sp.lambdify([YP, Y, T], sp.sympify(p["expresion"]))
    return sp.lambdify([Y, T], sp.sympify(p["expresion"]))


def _texto(p, y, t, yp=None):
    """Sustitución con los números puestos, p. ej. "0.1 + (1.105)"."""
    return p["sust"].format(y=_n(y), t=_n(t), yp=_n(yp) if yp is not None else "")


def _base(p, n):
    datos = {"funcion": f"y' = f(y, t) = {p['texto']}", "h": p["h"], "t0": p["t0"],
             "y0": p["y0"], "n": n, "t_final": _redondear(p["t0"] + n * p["h"])}
    return datos


# ===================================================================== Euler
@registrar("euler_adelante")
def euler_adelante(rng, n=3):
    p = generar_problema(rng)
    f = _f(p)
    datos = res.EulerHaciaAdelante(p["expresion"], p["h"], p["y0"], p["t0"], n)
    for it in datos["iteraciones"]:
        it["t0"] = _redondear(it["t0"])
        it["f"] = float(f(it["y0"], it["t0"]))
        it["texto_f"] = _texto(p, it["y0"], it["t0"])
    return {**_base(p, n), "iteraciones": datos["iteraciones"]}


@registrar("euler_modificado")
def euler_modificado(rng, n=2):
    p = generar_problema(rng)
    f = _f(p)
    predictor = p["y0"] + p["h"] * f(p["y0"], p["t0"])
    datos = res.EulerModificado(p["expresion"], p["h"], p["y0"], predictor, p["t0"], n)
    for it in datos["iteraciones"]:
        it["t0"], it["t1"] = _redondear(it["t0"]), _redondear(it["t1"])
        it["f0"] = float(f(it["y0"], it["t0"]))
        it["texto_f0"] = _texto(p, it["y0"], it["t0"])
        it["f1"] = float(f(it["y1"], it["t1"]))
        it["texto_f1"] = _texto(p, it["y1"], it["t1"])
    return {**_base(p, n), "iteraciones": datos["iteraciones"]}


@registrar("euler_atras")
def euler_atras(rng, n=2):
    p = generar_problema(rng)
    f = _f(p)
    predictor = p["y0"] + p["h"] * f(p["y0"], p["t0"])
    datos = res.EulerHaciaAtras(p["expresion"], p["y0"], predictor, p["h"], p["t0"], n)
    for it in datos["iteraciones"]:
        it["t1"] = _redondear(it["t1"])
        it["t0"] = _redondear(it["t1"] - p["h"])
        it["f0"] = float(f(it["y0"], it["t0"]))
        it["texto_f0"] = _texto(p, it["y0"], it["t0"])
        it["f1"] = float(f(it["y1"], it["t1"]))
        it["texto_f1"] = _texto(p, it["y1"], it["t1"])
    return {**_base(p, n), "iteraciones": datos["iteraciones"]}


# =============================================================== Runge-Kutta
FORMULAS_RK = {
    2: (["h·f(y, t)", "h·f(y + k1, t + h)"],
        "y + (k1 + k2) / 2"),
    3: (["h·f(y, t)", "h·f(y + k1/2, t + h/2)", "h·f(y - k1 + 2·k2, t + h)"],
        "y + (k1 + 4·k2 + k3) / 6"),
    "4_1_3": (["h·f(y, t)", "h·f(y + k1/2, t + h/2)", "h·f(y + k2/2, t + h/2)", "h·f(y + k3, t + h)"],
              "y + (k1 + 2·k2 + 2·k3 + k4) / 6"),
    "4_3_8": (["h·f(y, t)", "h·f(y + k1/3, t + h/3)", "h·f(y - k1/3 + k2, t + 2h/3)",
               "h·f(y + k1 - k2 + k3, t + h)"],
              "y + (k1 + 3·k2 + 3·k3 + k4) / 8"),
}


def _runge_kutta(rng, metodo, clave, n):
    p = generar_problema(rng)
    datos = metodo(p["expresion"], p["h"], p["y0"], p["t0"], n)
    formulas, formula_y = FORMULAS_RK[clave]
    t = p["t0"]
    for it in datos["iteraciones"]:
        it["t"] = _redondear(t)
        it["y"] = it["k1"]["y"]
        it["ks"] = [{"nombre": f"k{j}", "formula": formula, "valor": float(it[f"k{j}"]["k"]),
                     "texto": f"{num(p['h'])}·[{_texto(p, it[f'k{j}']['y'], it[f'k{j}']['t'])}]"}
                    for j, formula in enumerate(formulas, start=1)]
        it["yi"] = float(it["yi"]["yi"])
        t += p["h"]
    return {**_base(p, n), "formula_y": formula_y, "iteraciones": datos["iteraciones"]}


@registrar("runge_kutta_2")
def runge_kutta_2(rng, n=2):
    return _runge_kutta(rng, res.RungeKutta2Orden, 2, n)


@registrar("runge_kutta_3")
def runge_kutta_3(rng, n=2):
    return _runge_kutta(rng, res.RungeKutta3Orden, 3, n)


@registrar("runge_kutta_4_1_3")
def runge_kutta_4_1_3(rng, n=2):
    return _runge_kutta(rng, res.RungeKutta4Orden1_3Simpson, "4_1_3", n)


@registrar("runge_kutta_4_3_8")
def runge_kutta_4_3_8(rng, n=2):
    return _runge_kutta(rng, res.RungeKutta4Orden3_8Simpson, "4_3_8", n)


# ============================================================ orden superior
@registrar("runge_kutta_orden_superior")
def runge_kutta_orden_superior(rng, n=2):
    p = generar_problema(rng, orden_superior=True)
    datos = res.RungeKuttaOrdenSuperior(p["expresion"], p["h"], p["y0"], p["yp0"], p["t0"], n)
    for it in datos["iteraciones"]:
        m1, m2 = it["m1"], it["m2"]
        m1["qn"], m2["qn"] = _redondear(m1["qn"]), _redondear(m2["qn"])
        it["texto_m1"] = f"{num(p['h'])}·[{_texto(p, m1['Un'], m1['qn'], m1['Vn'])}]"
        it["texto_m2"] = f"{num(p['h'])}·[{_texto(p, m2['Un'], m2['qn'], m2['Vn'])}]"
    return {"funcion": f"y'' = f(y', y, t) = {p['texto']}", "h": p["h"], "t0": p["t0"],
            "y0": p["y0"], "yp0": p["yp0"], "n": n,
            "t_final": _redondear(p["t0"] + n * p["h"]),
            "iteraciones": datos["iteraciones"]}
