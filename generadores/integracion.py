"""
Creador de niveles del submapa Integración Numérica.

Cada función registrada:
    1. genera un problema aleatorio: una función, un intervalo [a, b] y el número de
       subintervalos n, con h = 0.25 o 0.5 para que las x sean cómodas;
    2. lo resuelve con el resolvedor de Vanessa (resolvedores/integracion.py);
    3. agrega lo que usan las plantillas: cada punto con su x, el texto de la sustitución, su
       peso en la fórmula, las sumas parciales y las tolerancias. El resolvedor no se modifica
       para eso: todo lo extra se calcula aquí a partir de lo que devuelve. Como revisión, se
       comprueba que las sumas den la misma integral que calculó el resolvedor.

TOLERANCIAS: el jugador escribe f(xi) con 4 decimales y con esos valores redondeados calcula
las sumas. El error que eso arrastra crece con los pesos (en Newton-Cotes hay pesos como 272),
así que cada casilla lleva una tolerancia calculada para su caso: "tol", "tol_suma", "tol_l".

Plantillas: plantillas/regla_trapezoidal.json, simpson_1_3.json, simpson_3_8.json,
newton_cotes_cerradas.json y newton_cotes_abiertas.json.
"""
from fractions import Fraction

from generadores import registrar
from generadores._util import num
from resolvedores import integracion as res

ERROR_F = 5e-5           # error máximo al escribir f(xi) con 4 decimales
HOLGURA = 1e-4           # margen extra por el redondeo de la propia casilla

# (expresión para sympy, texto para mostrar, texto de la sustitución, a mínimo, a máximo)
FUNCIONES = [
    ("exp(x)",        "e^x",          "e^{x}",           0, 1),
    ("sqrt(x)",       "raíz(x)",      "raíz{x}",         0, 2),
    ("log(x)",        "ln(x)",        "ln{x}",           1, 2),
    ("1/x",           "1/x",          "1/{x}",           1, 2),
    ("1/(1 + x**2)",  "1/(1 + x²)",   "1/(1 + {x}²)",    0, 1),
    ("exp(-x**2)",    "e^(-x²)",      "e^(-{x}²)",       0, 1),
    ("x*exp(x)",      "x·e^x",        "{x}·e^{x}",       0, 1),
    ("sin(x)",        "sen(x)  (en radianes)", "sen{x}", 0, 1),
    ("x**3 + 2",      "x³ + 2",       "{x}³ + 2",        0, 2),
]


def _numero(v):
    """Fraction/float del resolvedor -> int o float."""
    v = float(v)
    return int(v) if v == int(v) else v


def generar_problema(rng, n, intervalos=None):
    """Función, a, b y n. `intervalos` es cuántos subintervalos de ancho h hay entre a y b
    (en las fórmulas abiertas son n + 2)."""
    expr, texto, plantilla, a_min, a_max = rng.choice(FUNCIONES)
    h = Fraction(rng.choice(["1/4", "1/2"]))
    a = Fraction(rng.randint(a_min, a_max))
    b = a + h * (intervalos or n)
    return {"expresion": expr, "funcion": f"f(x) = {texto}", "sustitucion": plantilla,
            "a": a, "b": b, "n": n}


def _completar(datos, problema, pesos, factor, factor_texto, primero=0):
    """Arma la lista de puntos (desde el índice `primero`, para omitir los que no se usan)
    con sus pesos, y las sumas y tolerancias. Comprueba el resultado contra el resolvedor."""
    h = Fraction(datos["h"])
    a = problema["a"]
    puntos = []
    for i, (paso, w) in enumerate(zip(datos["pasos"], pesos)):
        if w == 0:
            continue                               # (fórmulas abiertas: f(a) y f(b) no se usan)
        x = a + i * h
        valor = float(paso["valor"])
        puntos.append({
            "i": i, "x": _numero(x), "valor": valor, "peso": w,
            "texto": problema["sustitucion"].format(x=f"({num(_numero(x))})"),
            "producto": w * valor,
            "tol": abs(w) * ERROR_F * 1.2 + HOLGURA,
        })
    suma = sum(p["producto"] for p in puntos)
    tol_suma = sum(abs(p["peso"]) for p in puntos) * ERROR_F * 1.2 + 3 * HOLGURA
    l = float(datos["l"])
    if abs(float(factor) * suma - l) > 1e-9 * max(1, abs(l)):
        raise ValueError(f"las sumas no coinciden con el resolvedor ({float(factor) * suma} vs {l})")
    return {
        "funcion": problema["funcion"],
        "a": _numero(a), "b": _numero(problema["b"]), "n": problema["n"],
        "h": _numero(h),
        "puntos": puntos,
        "ultimo": len(datos["pasos"]) - 1,
        "suma": suma, "tol_suma": tol_suma,
        "factor": float(factor), "factor_texto": factor_texto,
        "l": l, "tol_l": abs(float(factor)) * (tol_suma + ERROR_F) + HOLGURA,
    }


def _grupo(datos, indices):
    """Suma de f(xi) para los índices dados, con su tolerancia."""
    valores = {p["i"]: p["valor"] for p in datos["puntos"]}
    return (sum(valores[i] for i in indices),
            len(indices) * ERROR_F * 1.2 + 2 * HOLGURA)


def _resolver(funcion_resolvedor, problema):
    integral = res.integralDefinida(problema["expresion"], problema["a"], problema["b"],
                                    problema["n"])
    datos = funcion_resolvedor(integral)
    if "error" in datos:
        raise ValueError(f"el resolvedor rechazó el problema: {datos['error']}")
    return datos


# ============================================================== regla trapezoidal
@registrar("regla_trapezoidal")
def regla_trapezoidal(rng):
    p = generar_problema(rng, rng.choice([4, 5, 6]))
    n = p["n"]
    datos = _resolver(res.ReglaTrapezoidal, p)
    pesos = [1] + [2] * (n - 1) + [1]
    d = _completar(datos, p, pesos, Fraction(datos["h"]) / 2, "h/2")
    d["extremos"], d["tol_extremos"] = _grupo(d, [0, n])
    d["interiores"], d["tol_interiores"] = _grupo(d, range(1, n))
    return d


# ============================================================ Simpson 1/3 y 3/8
@registrar("simpson_1_3")
def simpson_1_3(rng):
    p = generar_problema(rng, rng.choice([4, 6]))
    n = p["n"]
    datos = _resolver(res.Regla1_3Simpson, p)
    pesos = [1] + [4 if i % 2 else 2 for i in range(1, n)] + [1]
    d = _completar(datos, p, pesos, Fraction(datos["h"]) / 3, "h/3")
    d["extremos"], d["tol_extremos"] = _grupo(d, [0, n])
    d["impares"], d["tol_impares"] = _grupo(d, range(1, n, 2))
    d["pares"], d["tol_pares"] = _grupo(d, range(2, n, 2))
    return d


@registrar("simpson_3_8")
def simpson_3_8(rng):
    # la fórmula del resolvedor es la de una sola aplicación: solo es correcta con n = 3
    p = generar_problema(rng, 3)
    datos = _resolver(res.Regla3_8Simpson, p)
    d = _completar(datos, p, [1, 3, 3, 1], Fraction(datos["h"]) * Fraction(3, 8), "3h/8")
    d["extremos"], d["tol_extremos"] = _grupo(d, [0, 3])
    d["interiores"], d["tol_interiores"] = _grupo(d, [1, 2])
    return d


# ================================================================ Newton-Cotes
def _texto_pesos(pesos):
    return ", ".join(str(w) for w in pesos)


@registrar("newton_cotes_cerradas")
def newton_cotes_cerradas(rng):
    p = generar_problema(rng, rng.choice([4, 5, 6]))
    datos = _resolver(res.NewtonCotesCerradas, p)
    constantes = res.NCC[p["n"]]
    c, pesos = constantes[0], constantes[1:]
    d = _completar(datos, p, pesos, Fraction(datos["h"]) * c, f"h·{c}")
    d["constante"] = f"{c}"
    d["pesos_texto"] = _texto_pesos(pesos)
    return d


@registrar("newton_cotes_abiertas")
def newton_cotes_abiertas(rng):
    n = rng.choice([2, 3, 4])
    p = generar_problema(rng, n, intervalos=n + 2)
    datos = _resolver(res.NewtonCotesAbiertas, p)
    constantes = res.NCA[n]
    c, pesos = constantes[0], constantes[1:]
    d = _completar(datos, p, pesos, Fraction(datos["h"]) * c, f"h·{c}")
    d["constante"] = f"{c}"
    d["pesos_texto"] = _texto_pesos([w for w in pesos if w != 0])
    d["intervalos"] = n + 2
    return d
