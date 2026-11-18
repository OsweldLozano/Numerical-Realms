import importlib
import pkgutil

_REGISTRO = {}


def registrar(nombre):
    def deco(funcion):
        if nombre in _REGISTRO and _REGISTRO[nombre] is not funcion:
            raise ValueError(f"ya hay un generador llamado {nombre!r} "
                             f"({_REGISTRO[nombre].__module__})")
        _REGISTRO[nombre] = funcion
        return funcion
    return deco


def obtener(nombre):
    try:
        return _REGISTRO[nombre]
    except KeyError:
        raise ValueError(f"no hay un generador registrado como {nombre!r}. "
                         f"Registrados: {', '.join(nombres()) or '(ninguno)'}") from None


def nombres():
    return sorted(_REGISTRO)


# importa todos los módulos de esta carpeta para que sus @registrar se ejecuten
for _m in pkgutil.iter_modules(__path__):
    if not _m.name.startswith("_"):
        importlib.import_module(f"{__name__}.{_m.name}")
