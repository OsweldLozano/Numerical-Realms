"""
Generadores del submapa Ecuaciones No Lineales.

EJEMPLO: sustituye generar_problema_* y resolver_* por tu generador y tu resolvedor.
"""
import math

from generadores import registrar

SUPERINDICE = {2: "²", 3: "³"}


# --------------------------------------------------------------------- bisección
def generar_problema_biseccion(rng):
    """f(x) = x^p - k, con k que no es potencia exacta. Intervalo [a, a+1] con la raíz."""
    p = rng.choice([2, 2, 3])
    while True:
        k = rng.randint(3, 60 if p == 2 else 120)
        raiz = k ** (1 / p)
        if abs(raiz - round(raiz)) > 1e-9:
            break
    a = math.floor(raiz)
    return {"p": p, "k": k, "a": a, "b": a + 1,
            "funcion": f"f(x) = x{SUPERINDICE[p]} - {k}"}


def resolver_biseccion(p, k, a, b, iteraciones):
    f = lambda x: x ** p - k                     # noqa: E731
    pasos = []
    for _ in range(iteraciones):
        c = (a + b) / 2
        fa, fc = f(a), f(c)
        if fa * fc < 0:
            a_nuevo, b_nuevo, lado = a, c, "izquierda"
        else:
            a_nuevo, b_nuevo, lado = c, b, "derecha"
        pasos.append({"a": a, "b": b, "c": c, "fa": fa, "fc": fc,
                      "signo": "negativo" if fa * fc < 0 else "positivo",
                      "a_nuevo": a_nuevo, "b_nuevo": b_nuevo, "lado": lado})
        a, b = a_nuevo, b_nuevo
    return {"iteraciones": pasos,
            "raiz": pasos[-1]["c"],
            "error": (pasos[-1]["b"] - pasos[-1]["a"]) / 2}


@registrar("biseccion")
def biseccion(rng, iteraciones=4):
    problema = generar_problema_biseccion(rng)
    solucion = resolver_biseccion(problema["p"], problema["k"], problema["a"],
                                  problema["b"], iteraciones)
    return {**problema, **solucion}
