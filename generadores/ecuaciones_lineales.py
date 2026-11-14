"""
Generadores del submapa Ecuaciones Lineales.

EJEMPLO: sustituye generar_problema_* y resolver_* por tu generador y tu resolvedor.
Se calcula con Fraction para que no haya errores de redondeo; el constructor los
convierte a números normales.
"""
from fractions import Fraction

from generadores import registrar
from generadores._util import entre_parentesis, num

NOMBRES = ("x", "y", "z")


def _nombres(tam):
    return list(NOMBRES[:tam]) if tam <= 3 else [f"x{i + 1}" for i in range(tam)]


def _decimal_finito(f, max_dec=4):
    """True si la fracción se escribe exacta con hasta `max_dec` decimales (0.5, 2.25...)."""
    return (f * 10 ** max_dec).denominator == 1


def texto_ecuacion(coefs, b, variables):
    partes = []
    for a, v in zip(coefs, variables):
        if a == 0:
            continue
        mag = "" if abs(a) == 1 else str(abs(a))
        signo = "-" if a < 0 else "+"
        partes.append((signo, f"{mag}{v}"))
    if not partes:
        return f"0 = {b}"
    s0, t0 = partes[0]
    texto = ("-" if s0 == "-" else "") + t0
    for s, t in partes[1:]:
        texto += f" {s} {t}"
    return f"{texto} = {b}"


# ------------------------------------------------------------ eliminación gaussiana
def generar_problema_gauss(rng, tam):
    """Sistema tam x tam con solución entera."""
    sol = [rng.randint(-5, 5) for _ in range(tam)]
    A = [[rng.randint(-5, 5) for _ in range(tam)] for _ in range(tam)]
    b = [sum(a * x for a, x in zip(fila, sol)) for fila in A]
    return {"A": A, "b": b, "solucion_real": sol}


def resolver_gauss(A, b):
    """Eliminación hacia adelante (sin pivoteo) + sustitución hacia atrás.
    Devuelve None si algún pivote es cero (el generador entonces pide otro problema)."""
    tam = len(A)
    M = [[Fraction(v) for v in fila] + [Fraction(bi)] for fila, bi in zip(A, b)]
    etapas = []
    for k in range(tam - 1):
        if M[k][k] == 0:
            return None
        ops = []
        for i in range(k + 1, tam):
            factor = M[i][k] / M[k][k]
            if factor != 0:
                M[i] = [a - factor * p for a, p in zip(M[i], M[k])]
                signo = "-" if factor > 0 else "+"
                ops.append(f"R{i + 1} = R{i + 1} {signo} {entre_parentesis(abs(factor))}·R{k + 1}")
        etapas.append({
            "columna": k + 1,
            "pivote": M[k][k],
            "operaciones": "; ".join(ops) if ops else "las filas de abajo ya tienen 0",
            "matriz": [fila[:] for fila in M],
            "editables": [[i, j] for i in range(k + 1, tam) for j in range(tam + 1)],
        })
    if M[tam - 1][tam - 1] == 0:
        return None

    x = [Fraction(0)] * tam
    sustitucion = []
    for i in range(tam - 1, -1, -1):
        suma = sum(M[i][j] * x[j] for j in range(i + 1, tam))
        x[i] = (M[i][tam] - suma) / M[i][i]
        d = lambda v: entre_parentesis(v, fraccion=False)          # noqa: E731
        if i == tam - 1:
            formula = f"{d(M[i][tam])} / {d(M[i][i])}"
        else:
            terminos = " - ".join(f"{d(M[i][j])}·{d(x[j])}" for j in range(i + 1, tam))
            formula = f"({num(M[i][tam], fraccion=False)} - {terminos}) / {d(M[i][i])}"
        sustitucion.append({"indice": i, "formula": formula, "valor": x[i]})
    return {"etapas": etapas, "sustitucion": sustitucion, "solucion": x}


def _numeros_amables(sol):
    """Todos los valores intermedios con decimales finitos (máx. 4) y no muy grandes."""
    for et in sol["etapas"]:
        for fila in et["matriz"]:
            for v in fila:
                if not _decimal_finito(v) or abs(v) > 99:
                    return False
    return True


@registrar("eliminacion_gaussiana")
def eliminacion_gaussiana(rng, tam=3):
    variables = _nombres(tam)
    for intento in range(5000):
        p = generar_problema_gauss(rng, tam)
        sol = resolver_gauss(p["A"], p["b"])
        if sol is None:
            continue                       # pivote cero: otro problema
        if intento < 4000 and not _numeros_amables(sol):
            continue                       # se prefieren problemas con números cómodos
        break
    else:
        raise RuntimeError("no se pudo generar un sistema válido")

    for s in sol["sustitucion"]:
        s["variable"] = variables[s["indice"]]
    return {
        "tam": tam,
        "variables": variables,
        "ecuaciones": [texto_ecuacion(f, bi, variables) for f, bi in zip(p["A"], p["b"])],
        "A": p["A"],
        "b": p["b"],
        "Ab": [fila + [bi] for fila, bi in zip(p["A"], p["b"])],
        "etapas": sol["etapas"],
        "sustitucion": sol["sustitucion"],
        "solucion": sol["solucion"],
    }
