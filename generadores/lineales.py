from fractions import Fraction

from generadores import registrar
from generadores._util import entre_parentesis, num
from resolvedores import lineales as res

N = 3
VARIABLES = [f"x{i + 1}" for i in range(N)]


# ================================================================ utilidades
def _f(v):
    """Fraction/float -> número de Python (int si es entero)."""
    v = Fraction(v).limit_denominator(10 ** 9) if not isinstance(v, Fraction) else v
    return v.numerator if v.denominator == 1 else float(v)


def _decimal_finito(v, max_dec=4):
    return (Fraction(v) * 10 ** max_dec).denominator == 1


def _matriz(m):
    return [[_f(v) for v in fila] for fila in m]


def _p(v):
    """Número para una fórmula: decimales y paréntesis si es negativo."""
    return entre_parentesis(_f(v), fraccion=False) if isinstance(v, Fraction) else entre_parentesis(v)


def texto_ecuacion(coefs, b):
    partes = []
    for a, v in zip(coefs, VARIABLES):
        if a == 0:
            continue
        mag = "" if abs(a) == 1 else str(abs(a))
        partes.append(("-" if a < 0 else "+", f"{mag}{v}"))
    texto = ("-" if partes[0][0] == "-" else "") + partes[0][1]
    for s, t in partes[1:]:
        texto += f" {s} {t}"
    return f"{texto} = {b}"


def sistema_aleatorio(rng, dominante=False):
    sol = [rng.randint(-5, 5) for _ in range(N)]
    if dominante:
        A = [[rng.randint(-3, 3) for _ in range(N)] for _ in range(N)]
        for i in range(N):
            A[i][i] = sum(abs(A[i][j]) for j in range(N) if j != i) + rng.randint(1, 3)
    else:
        A = [[rng.randint(-5, 5) for _ in range(N)] for _ in range(N)]
    b = [sum(a * x for a, x in zip(fila, sol)) for fila in A]
    return [fila + [bi] for fila, bi in zip(A, b)]


def _base(Ab):
    return {"Ab": [list(f) for f in Ab],
            "ecuaciones": [texto_ecuacion(f[:N], f[N]) for f in Ab],
            "variables": VARIABLES}


def _generar_directo(rng, metodo, amable, intentos=6000):
    """Sistema que el método resuelve sin división entre cero y con números cómodos (si en
    muchos intentos no aparece uno cómodo, se acepta el primero que se pueda resolver)."""
    respaldo = None
    for intento in range(intentos):
        Ab = sistema_aleatorio(rng)
        d = metodo([[Fraction(v) for v in f] for f in Ab])
        if "error" in d:
            continue
        mats = [it["matriz"] for it in d["iteraciones"]]
        if amable(mats):
            return Ab, d
        respaldo = respaldo or (Ab, d)
    if respaldo:
        return respaldo
    raise RuntimeError("no se pudo generar un sistema")


def _amable_decimales(mats):
    return all(_decimal_finito(v) and abs(v) <= 99 for m in mats for f in m for v in f)


def _amable_enteros(mats):
    return all(Fraction(v).denominator == 1 and abs(v) <= 999 for m in mats for f in m for v in f)


def _operaciones(prev, k, filas, normalizar=True):
    """Texto de las operaciones de renglón de la etapa k (desde 0)."""
    ops = []
    pivote = prev[k][k]
    if normalizar and pivote != 1:
        ops.append(f"R{k + 1} = R{k + 1} / {_p(pivote)}")
    for i in filas:
        factor = prev[i][k] if normalizar else None
        if factor:
            ops.append(f"R{i + 1} = R{i + 1} - {_p(factor)}·R{k + 1}")
    return "; ".join(ops) if ops else "no hay que hacer cambios"


# ======================================================== eliminación gaussiana
@registrar("eliminacion_gaussiana")
def eliminacion_gaussiana(rng):
    Ab, d = _generar_directo(rng, res.EliminacionGaussiana, _amable_decimales)
    prev = [[Fraction(v) for v in f] for f in Ab]
    etapas = []
    for k, it in enumerate(d["iteraciones"]):
        m = [[Fraction(v) for v in f] for f in it["matriz"]]
        etapas.append({"k": k + 1, "pivote": _f(prev[k][k]),
                       "operaciones": _operaciones(prev, k, range(k + 1, N)),
                       "matriz": _matriz(m),
                       "editables": [[i, j] for i in range(k, N) for j in range(k, N + 1)]})
        prev = m
    # sustitución hacia atrás (la diagonal ya es 1)
    x = [Fraction(v) for v in d["incognitas"]]
    sustitucion = []
    for i in range(N - 1, -1, -1):
        terminos = [f"{_p(prev[i][j])}·{_p(x[j])}" for j in range(i + 1, N) if prev[i][j] != 0]
        formula = f"{num(_f(prev[i][N]))}" + "".join(f" - {t}" for t in terminos)
        sustitucion.append({"variable": VARIABLES[i], "formula": formula, "valor": _f(x[i])})
    return {**_base(Ab), "etapas": etapas, "sustitucion": sustitucion,
            "solucion": [_f(v) for v in x]}


# ================================================================ Gauss-Jordan
@registrar("gauss_jordan")
def gauss_jordan(rng):
    Ab, d = _generar_directo(rng, res.GaussJordan, _amable_decimales)
    prev = [[Fraction(v) for v in f] for f in Ab]
    etapas = []
    for k, it in enumerate(d["iteraciones"]):
        m = [[Fraction(v) for v in f] for f in it["matriz"]]
        etapas.append({"k": k + 1, "pivote": _f(prev[k][k]),
                       "operaciones": _operaciones(prev, k, [i for i in range(N) if i != k]),
                       "matriz": _matriz(m),
                       "editables": [[i, j] for i in range(N) for j in range(k, N + 1)]})
        prev = m
    solucion = [{"variable": v, "valor": _f(x)} for v, x in zip(VARIABLES, d["incognitas"])]
    return {**_base(Ab), "etapas": etapas, "solucion": solucion}


# ==================================================================== Montante
@registrar("montante")
def montante(rng):
    Ab, d = _generar_directo(rng, res.Montante, _amable_enteros)
    prev = [[Fraction(v) for v in f] for f in Ab]
    pivote_anterior = Fraction(1)
    etapas = []
    for k, it in enumerate(d["iteraciones"]):
        m = [[Fraction(v) for v in f] for f in it["matriz"]]
        etapas.append({"k": k + 1, "pivote": _f(prev[k][k]), "pivote_anterior": _f(pivote_anterior),
                       "matriz": _matriz(m),
                       "editables": [[i, j] for i in range(N) for j in range(N + 1) if i != k and j != k]})
        pivote_anterior = prev[k][k]
        prev = m
    det = prev[0][0]
    solucion = [{"variable": VARIABLES[i], "b": _f(prev[i][N]), "valor": _f(d["incognitas"][i])}
                for i in range(N)]
    return {**_base(Ab), "etapas": etapas, "determinante": _f(det), "solucion": solucion}


# ====================================================== Gauss-Seidel y Jacobi
def _despejes(Ab):
    """x1 = (b1 - a12·x2 - a13·x3) / a11, con los coeficientes del sistema."""
    textos = []
    for i in range(N):
        terminos = "".join(f" - {_p(Ab[i][j])}·{VARIABLES[j]}" for j in range(N) if j != i and Ab[i][j] != 0)
        textos.append(f"{VARIABLES[i]} = ({Ab[i][N]}{terminos}) / {Ab[i][i]}")
    return textos


def _sustitucion(Ab, i, valores, por_nombre=()):
    """Despeje de xi con los valores puestos: (7 - (-1)·(0.5) - 1·(2)) / 4.
    Las variables en `por_nombre` se escriben con su nombre (x1) y no con su valor: en
    Gauss-Seidel son las que el jugador acaba de calcular en la misma iteración, y mostrar su
    número sería darle la respuesta de la fila anterior."""
    terminos = "".join(f" - {_p(Ab[i][j])}·" + (VARIABLES[j] if j in por_nombre else f"({num(float(valores[j]))})")
                       for j in range(N) if j != i and Ab[i][j] != 0)
    return f"({Ab[i][N]}{terminos}) / {Ab[i][i]}"


def _iterativo(rng, metodo, inicial, seidel):
    for _ in range(500):
        Ab = sistema_aleatorio(rng, dominante=True)
        d = metodo(Ab)
        if d and 3 <= len(d["iteraciones"]) < 10:          # que haya convergido antes del máximo
            break
    else:
        raise RuntimeError("no se pudo generar un sistema que converja")
    anterior = list(inicial)
    iteraciones = []
    for it in d["iteraciones"]:
        actual = list(anterior)
        filas = []
        for i in range(N):
            usados = actual if seidel else anterior          # Seidel usa los valores ya nuevos
            nuevos = range(i) if seidel else ()              # ...que se muestran por nombre
            filas.append({"variable": VARIABLES[i], "texto": _sustitucion(Ab, i, usados, nuevos),
                          "valor": float(it["valores"][i])})
            actual[i] = it["valores"][i]
        iteraciones.append({"filas": filas, "error": float(max(it["errores"])),
                            "valores": [float(v) for v in it["valores"]]})
        anterior = [float(v) for v in it["valores"]]
    return {**_base(Ab), "despejes": _despejes(Ab), "inicial": "(" + ", ".join(str(v) for v in inicial) + ")",
            "iteraciones": iteraciones, "solucion": [float(v) for v in d["incognitas"]]}


@registrar("gauss_seidel")
def gauss_seidel(rng):
    return _iterativo(rng, res.GaussSeidel, [0] * N, seidel=True)


@registrar("jacobi")
def jacobi(rng):
    return _iterativo(rng, res.Jacobi, [1] * N, seidel=False)
