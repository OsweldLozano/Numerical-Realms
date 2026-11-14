"""
Generadores de problemas: aquí se conecta tu GENERADOR y tu RESOLVEDOR con las plantillas.

Cada método numérico tiene una función registrada con un nombre. La plantilla la elige con
"generador": "<nombre>". La función:

    from generadores import registrar

    @registrar("biseccion")
    def biseccion(rng, iteraciones=4):        # rng: random.Random; los demás vienen de
        problema = generar_problema(rng)      #      "parametros" en la plantilla
        solucion = resolver(problema, iteraciones)
        return {...}                          # diccionario con TODO lo que usa la plantilla

REGLAS DEL DICCIONARIO QUE SE DEVUELVE
    * Claves de texto; valores: números, textos, listas, matrices (listas de listas) o
      diccionarios anidados. Se aceptan también arreglos y números de numpy y Fraction.
    * Debe incluir los datos del problema Y los valores intermedios del proceso de solución
      (lo que el jugador va a escribir en cada casilla). Lo que se repite un número variable
      de veces (iteraciones, etapas) va en una LISTA de diccionarios, una entrada por vuelta.
    * Usa siempre `rng` para el azar (rng.randint, rng.uniform, rng.choice...). Así la misma
      semilla da el mismo problema y se pueden reproducir los errores. Si tu generador usa
      numpy, crea su generador así:  np.random.default_rng(rng.randrange(2**32))
    * Si un problema sale "feo" (división entre cero, no converge...), genera otro dentro de
      la función: el juego espera siempre un problema válido.

Agregar un método nuevo: crea un .py en esta carpeta con funciones @registrar(...). Se
carga solo; no hay que tocar este archivo.
"""
import importlib
import pkgutil

_REGISTRO = {}


def registrar(nombre):
    """Decorador: registra la función como generador con ese nombre."""
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
