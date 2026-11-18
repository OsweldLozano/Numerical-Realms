import sympy as sp

from generadores import registrar
from generadores._util import entre_parentesis, num
from resolvedores import interpolacion as res

X = sp.symbols("x")
SUPER = {1: "", 2: "²", 3: "³", 4: "⁴", 5: "⁵"}


# =================================================================== utilidades
def _polinomio_entero(rng, grado, maximo, puntos):
    """Valores enteros de un polinomio aleatorio con coeficientes pequeños, evaluado en
    `puntos`. Se repite hasta que ningún valor pase de `maximo` (en valor absoluto). Con
    coeficientes y nodos enteros, todas las diferencias (y las diferencias divididas) son
    enteras, así que el jugador no arrastra decimales en las tablas."""
    for intento in range(10000):
        if intento and intento % 300 == 0 and grado > 1:
            grado -= 1                            # con nodos grandes, un grado menor cabe mejor
        coefs = [rng.randint(-2, 2) for _ in range(grado)] + [rng.choice([-1, 1])]
        coefs[0] = rng.randint(-6, 9)
        ys = [sum(c * p ** k for k, c in enumerate(coefs)) for p in puntos]
        if max(abs(y) for y in ys) <= maximo and len(set(ys)) > 1:
            return ys
    raise RuntimeError("no se pudo generar una tabla con valores pequeños")


def _por_orden(delta, n):
    """El resolvedor guarda las diferencias en una sola lista (primero las de orden 1, luego
    las de orden 2...). Aquí se separan: [[orden 1], [orden 2], ...]."""
    ordenes, i = [], 0
    for k in range(1, n):
        tam = n - k
        ordenes.append(delta[i:i + tam])
        i += tam
    return ordenes


def _punto_intermedio(rng, xs):
    """Un x entre el primer y el último nodo que no sea un nodo (termina en .5)."""
    while True:
        x = rng.randint(min(xs), max(xs) - 1) + 0.5
        if x not in xs:
            return x


def _tabla(xs, ys):
    return [[x, y] for x, y in zip(xs, ys)]


# ========================================================= interpolación lineal
FUNCIONES_LINEAL = [
    # (expresión, texto, mínimo de a, máximo de b)
    (sp.log(X), "ln(x)", 1, 9),
    (sp.sqrt(X), "raíz(x)", 0, 16),
    (sp.exp(X), "eˣ", 0, 3),
    (1 / X, "1/x", 1, 8),
    (X ** 2, "x²", -4, 6),
    (X ** 3, "x³", -3, 4),
]


def generar_problema_lineal(rng):
    expr, texto, minimo, maximo = rng.choice(FUNCIONES_LINEAL)
    a = rng.randint(minimo, maximo - 1)
    b = rng.randint(a + 1, min(a + 4, maximo))
    pasos = int((b - a) * 2)                      # x en múltiplos de 0.5 dentro de (a, b)
    x = a + rng.randint(1, pasos - 1) * 0.5 if pasos > 1 else a + 0.5
    if x == int(x):
        x = int(x)
    return {"valor": x, "a": a, "b": b, "expresion": expr, "funcion": f"f(x) = {texto}"}


@registrar("interpolacion_lineal")
def interpolacion_lineal(rng):
    p = generar_problema_lineal(rng)
    datos = res.InterpolacionLineal(p["valor"], p["a"], p["b"], p["expresion"])
    datos["funcion"] = p["funcion"]
    return datos


# ================================================================ Newton (Δ y ∇)
def generar_problema_newton(rng, hacia="adelante"):
    """Tabla con x igualmente espaciadas y un x cerca del inicio (adelante) o del final
    (atrás), para que s salga 0.25, 0.5, 0.75 o 1.5 (o negativo)."""
    n = rng.choice([4, 4, 5])
    h = rng.choice([1, 1, 2, 0.5])
    x0 = rng.randint(-2, 4)
    xs = [x0 + i * h for i in range(n)]
    xs = [int(v) if v == int(v) else v for v in xs]
    ys = _polinomio_entero(rng, rng.choice([n - 2, n - 1]), 60, range(n))
    s = rng.choice([0.25, 0.5, 0.5, 0.75, 1.5])
    x = xs[0] + s * h if hacia == "adelante" else xs[-1] - s * h
    if x == int(x):
        x = int(x)
    return {"x": x, "tabla": _tabla(xs, ys)}


def _completar_newton(datos, hacia):
    """Agrega: n, uniformidad, diferencias por orden con su etiqueta y las fórmulas de cada
    término de g(x).

    Todas las diferencias se nombran con Δ (Δᵏyj = Δᵏ⁻¹yj+1 - Δᵏ⁻¹yj). Hacia atrás se usa la
    equivalencia ∇ᵏyn = Δᵏyn-k, porque la fuente de pygame-gui (Noto Sans) no tiene el
    símbolo ∇ y se vería como un cuadro. Los coeficientes son los mismos."""
    n = len(datos["tabla"])
    ordenes = []
    for k, difs in enumerate(_por_orden(datos["delta"], n), start=1):
        valores = [{**d, "etiqueta": f"Δ{SUPER[k]}y{j}"} for j, d in enumerate(difs)]
        ordenes.append({"k": k, "simbolo": f"Δ{SUPER[k]}y", "valores": valores})

    for i, op in enumerate(datos["g_x"]["operacion"]):
        if hacia == "adelante":
            op["simbolo"] = "y0" if i == 0 else f"Δ{SUPER[i]}y0"
            factores = "".join(f"(s - {j})" for j in range(1, i))
        else:
            op["simbolo"] = f"y{n - 1}" if i == 0 else f"Δ{SUPER[i]}y{n - 1 - i}"
            factores = "".join(f"(s + {j})" for j in range(1, i))
        if i == 0:
            op["formula"] = "1"
        elif i == 1:
            op["formula"] = "s"
        else:
            op["formula"] = f"s{factores} / {i}!"

    datos["n"] = n
    datos["ordenes"] = ordenes
    datos["uniforme"] = len({round(h["hi"], 9) for h in datos["h"]}) == 1
    return datos


@registrar("newton_adelante")
def newton_adelante(rng):
    p = generar_problema_newton(rng, "adelante")
    return _completar_newton(res.NewtonHaciaAdelante(p["x"], p["tabla"]), "adelante")


@registrar("newton_atras")
def newton_atras(rng):
    p = generar_problema_newton(rng, "atras")
    return _completar_newton(res.NewtonHaciaAtras(p["x"], p["tabla"]), "atras")


# ==================================================== Newton diferencias divididas
def generar_problema_divididas(rng):
    """Nodos enteros NO igualmente espaciados. Los valores salen de un polinomio con
    coeficientes enteros, así que todas las diferencias divididas son enteras."""
    n = rng.choice([4, 4, 5])
    while True:
        xs = sorted(rng.sample(range(-2, 9), n))
        pasos = {b - a for a, b in zip(xs, xs[1:])}
        if len(pasos) > 1:                        # que no sea uniforme
            break
    ys = _polinomio_entero(rng, rng.choice([n - 2, n - 1]), 90, xs)
    return {"x": _punto_intermedio(rng, xs), "tabla": _tabla(xs, ys)}


@registrar("newton_diferencias_divididas")
def newton_diferencias_divididas(rng):
    p = generar_problema_divididas(rng)
    datos = res.NewtonconDiferenciasDivididas(p["x"], p["tabla"])
    n = len(datos["tabla"])
    xs = [fila[0] for fila in datos["tabla"]]
    x = datos["x"]

    ordenes = []
    for k, difs in enumerate(_por_orden(datos["delta"], n), start=1):
        valores = []
        for j, d in enumerate(difs):
            nodos = ",".join(f"x{i}" for i in range(j, j + k + 1))
            valores.append({**d, "etiqueta": f"f[{nodos}]"})
        ordenes.append({"k": k, "valores": valores})

    for i, op in enumerate(datos["g_x"]["operacion"]):
        op["simbolo"] = "y0" if i == 0 else "f[" + ",".join(f"x{j}" for j in range(i + 1)) + "]"
        op["formula"] = "1" if i == 0 else "".join(
            f"({num(x)} - {entre_parentesis(xs[j])})" for j in range(i))

    datos["n"] = n
    datos["ordenes"] = ordenes
    return datos


# ===================================================================== Lagrange
def generar_problema_lagrange(rng):
    n = rng.choice([3, 3, 4])
    xs = sorted(rng.sample(range(-2, 8), n))
    ys = [rng.randint(-9, 12) for _ in range(n)]
    return {"x": _punto_intermedio(rng, xs), "tabla": _tabla(xs, ys)}


@registrar("lagrange")
def lagrange(rng):
    p = generar_problema_lagrange(rng)
    datos = res.Lagrange(p["x"], p["tabla"])
    if "error" in datos:                          # no pasa con nodos distintos, pero por si acaso
        raise ValueError(f"Lagrange no pudo resolver el problema: {datos['error']}")
    x = datos["x"]
    for i, paso in enumerate(datos["pasos"]):
        xi = paso["abajo"]["x"]
        numerador, denominador = 1, 1
        for v in paso["arriba"]["lista"]:
            numerador *= x - v
        for v in paso["abajo"]["lista"]:
            denominador *= xi - v
        paso["texto_arriba"] = "".join(f"({num(x)} - {entre_parentesis(v)})"
                                       for v in paso["arriba"]["lista"])
        paso["texto_abajo"] = "".join(f"({num(xi)} - {entre_parentesis(v)})"
                                      for v in paso["abajo"]["lista"])
        paso["numerador"] = numerador
        paso["denominador"] = denominador
        paso["L"] = numerador / denominador
    datos["n"] = len(datos["tabla"])
    return datos
