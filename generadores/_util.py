"""Utilidades compartidas por los generadores (no se registra como generador)."""
from fractions import Fraction


def num(v, decimales=4, fraccion=True):
    """Número -> texto corto para armar fórmulas dentro del generador: 3, -2.5, 7/3.
    Con fraccion=False, una Fraction que se escribe exacta en decimales sale en decimal
    (11/4 -> 2.75), para que coincida con lo que el juego muestra en las matrices."""
    if isinstance(v, Fraction):
        if v.denominator == 1:
            return str(v.numerator)
        exacta = (v * 10 ** decimales).denominator == 1
        if v.denominator <= 12 and (fraccion or not exacta):
            return f"{v.numerator}/{v.denominator}"
        v = float(v)
    if isinstance(v, float):
        r = round(v, decimales)
        if r == int(r):
            return str(int(r))
        return f"{r:.{decimales}f}".rstrip("0").rstrip(".")
    return str(v)


def entre_parentesis(v, decimales=4, fraccion=True):
    """Como num(), pero con paréntesis si es negativo o fracción: (-3), (1/2)."""
    t = num(v, decimales, fraccion)
    return f"({t})" if t.startswith("-") or "/" in t else t
