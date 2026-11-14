"""
Generadores del submapa Interpolación.

EJEMPLO: sustituye generar_problema_* y resolver_* por tu generador y tu resolvedor.
Lo único que importa al juego es el diccionario que devuelve la función registrada.
"""
from generadores import registrar


# ------------------------------------------------------------ interpolación lineal
def generar_problema_lineal(rng):
    """Dos puntos con x enteras y un x intermedio entero."""
    x0 = rng.randint(-3, 6)
    x1 = x0 + rng.randint(2, 6)
    y0, y1 = rng.randint(-8, 12), rng.randint(-8, 12)
    while y1 == y0:
        y1 = rng.randint(-8, 12)
    x = rng.randint(x0 + 1, x1 - 1)
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "x": x}


def resolver_lineal(p):
    """g(x) = y0 + (y1 - y0)/(x1 - x0) · (x - x0), guardando cada valor intermedio."""
    dy = p["y1"] - p["y0"]
    dx = p["x1"] - p["x0"]
    m = dy / dx
    dx_punto = p["x"] - p["x0"]
    producto = m * dx_punto
    return {"dy": dy, "dx": dx, "m": m, "dx_punto": dx_punto,
            "producto": producto, "resultado": p["y0"] + producto}


@registrar("interpolacion_lineal")
def interpolacion_lineal(rng):
    problema = generar_problema_lineal(rng)
    solucion = resolver_lineal(problema)
    return {**problema, **solucion}
