from fractions import Fraction


def num(v, decimales=4, fraccion=True):
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
    t = num(v, decimales, fraccion)
    return f"({t})" if t.startswith("-") or "/" in t else t
