"""
Resolvedor de los métodos de ecuaciones no lineales (código de Vanessa).

Las líneas marcadas con "# CORREGIDO" son los únicos cambios respecto al original:
    * NewtonRaphson, PuntoFijo, FalsaPosicion y Secante: iteraciones.append(iteracion = {...})
      da TypeError (append no acepta argumentos con nombre). Ahora es iteraciones.append({...}).
    * Bisectriz: el signo de f(c) se revisaba con "valor < 0" en lugar de "f_valor < 0", el
      intervalo se actualizaba igual sin importar si f crece o decrece, y el paro comparaba x
      con la tolerancia en lugar del error. Ahora: si f(a)·f(c) < 0 la raíz está en [a, c];
      si no, en [c, b]; y se detiene cuando el error <= tol.
    * FalsaPosicion: siempre reemplazaba a, aunque la raíz quedara del otro lado (solo era
      correcto cuando el extremo b se queda fijo). Ahora usa el signo de f(x), como bisección.
      En los casos en que b se queda fijo, los resultados son los mismos que antes.
    * NewtonRaphson y PuntoFijo: "valor_final" devolvía la penúltima aproximación.
    * Secante: en "error", "xi" y "x0" guardaban las dos aproximaciones anteriores en lugar
      de las dos con las que se calcula el error.
"""
#Librerias
import sympy as sp
from fractions import Fraction
import numpy as np


"""  Metodos  """
def Grafico(funcion):
    x = sp.Symbol('x')
    f_num = sp.lambdify(x, funcion, 'numpy')

    puntos = Tabulacion(f_num)
    if(puntos == None): return

    a, b = puntos[0], puntos[1]
    f_a, f_b = f_num(a), f_num(b)
    raiz = {"a":a,"f(a)":f_a,"b":b,"f(b)":f_b,}

    puntos = []
    for i in range(a-3,b+4):
        f_i = f_num(i)
        punto = {
            "x": i,
            "f(x)": f_i
        }
        puntos.append(punto.copy())

    datos={
        "funcion":funcion,
        "puntos":puntos,
        "raiz": raiz.copy(),
    }
    return datos

def Bisectriz(funcion):
    x = sp.Symbol('x')
    f_num = sp.lambdify(x, funcion, 'numpy')

    puntos = Tabulacion(f_num)
    if(puntos == None): return

    a, b = puntos[0], puntos[1]
    f_a, f_b = f_num(a), f_num(b)
    raiz = {"a":a,"f(a)":f_a,"b":b,"f(b)":f_b,}

    puntos = []
    for i in range(a-3,b+4):
        f_i = f_num(i)
        punto = {
            "x": i,
            "f(x)": f_i
        }
        puntos.append(punto.copy())

    valor = (a+b)/2
    tol = 0.001
    max_iter = 10
    iteraciones = []
    x_anterior = 0
    for i in range(1,max_iter):

        valor = (a+b)/2
        error = abs(valor-x_anterior)

        f_valor = f_num(valor)
        if (f_valor >= 0): comportamiento = "+"
        else: comportamiento = "-"                 # CORREGIDO: decía "elif(valor < 0)"

        iteracion={
            "a": a,
            "b": b,
            "x": valor,
            "comportamiento": comportamiento,
            "error": {"error":error, "xi":valor, "x0":x_anterior}        
        }
        iteraciones.append(iteracion.copy())

        if f_num(a)*f_valor < 0: b = valor         # CORREGIDO: la raíz está en [a, c]
        else: a = valor                             # CORREGIDO: la raíz está en [c, b]

        if(round(error, 3) <= tol):                 # CORREGIDO: decía round(valor, 3)
            break 

        x_anterior = valor

    datos={
        "funcion":funcion,
        "puntos":puntos,
        "raiz": raiz.copy(),
        "iteraciones":iteraciones.copy()
    }
    return datos

def NewtonRaphson(funcion):
    x = sp.Symbol('x')
    derivada = sp.diff(funcion, x)
    funcion_num = sp.lambdify(x, funcion, 'numpy')
    derivada_num = sp.lambdify(x, derivada, 'numpy')

    xi = 1
    tol = 0.000001
    max_iter = 10

    iteraciones = []
    iteraciones.append({                  # CORREGIDO: sin "iteracion ="
        "iteracion": 0,
        "xi": xi,
        "error": "---",
    })

    for i in range(1,max_iter):
        fx = funcion_num(xi)
        fpx = derivada_num(xi)

        if fpx == 0: break
        x_nuevo = xi - fx / fpx
        error = abs(x_nuevo - xi)

        iteracion ={
            "iteracion": i,
            "x": {"xi":x_nuevo, "x0":xi, "f(x)":fx, "f'(x)":fpx,},
            "error": {"error":error, "xi":x_nuevo, "x0":xi},
        }
        iteraciones.append(iteracion.copy())

        xi = x_nuevo                                # CORREGIDO: antes de salir, para valor_final
        if(error < tol): break

    datos={
        "funcion":funcion,
        "derivada":derivada,
        "valor_final":xi,
        "iteraciones":iteraciones.copy()
    }
    return datos

def PuntoFijo(funcion):
    x = sp.Symbol('x')
    g_num = sp.lambdify(x, funcion, 'numpy')

    xi = 0
    tol = 0.00001
    max_iter = 10

    iteraciones = []
    iteraciones.append({                  # CORREGIDO: sin "iteracion ="
        "iteracion": 0,
        "xi": xi,
        "error": "---",
    })



    for i in range(1,max_iter):
        x_nuevo = g_num(xi)
        error = abs(x_nuevo - xi)

        iteracion ={
            "iteracion": i,
            "xi": x_nuevo,
            "error": {"error":error, "xi":x_nuevo, "x0":xi},
        }
        iteraciones.append(iteracion.copy())

        xi = x_nuevo                                # CORREGIDO: antes de salir, para valor_final
        if(error < tol):
            break
    
    datos={
        "funcion":funcion,
        "valor_final":xi,
        "iteraciones":iteraciones.copy()
    }
    return datos

def FalsaPosicion(funcion):
    x = sp.Symbol('x')
    f_num = sp.lambdify(x, funcion, 'numpy')

    puntos = Tabulacion(f_num)
    if(puntos == None): return

    a, b = puntos[0], puntos[1]
    f_a, f_b = f_num(a), f_num(b)
    raiz = {"a":a,"f(a)":f_a,"b":b,"f(b)":f_b,}

    tol = 0.001
    max_iter = 10
    
    iteraciones = []
    iteraciones.append({                  # CORREGIDO: sin "iteracion ="
        "iteracion": 0,
        "b": b,
        "f(b)": f_b,
        "a": a,
        "f(a)": f_a,
        "x": "---",
        "error": "---",
    })

    x_anterior = a                                  # CORREGIDO: aproximación anterior
    for i in range(1,max_iter):
        xi = a - ((f_a * (b - a))/(f_b - f_a))
        error = abs(x_anterior - xi)                # CORREGIDO: decía abs(a - xi)

        iteracion ={
            "iteracion": i,
            "b": b,
            "f(b)": f_b,
            "a": a,
            "f(a)": f_a,
            "x": xi,
            "error": {"error":error, "xi":xi, "x0":x_anterior},   # CORREGIDO
        }
        iteraciones.append(iteracion.copy())

        if(round(error, 3) <= tol):
            break

        f_xi = f_num(xi)                            # CORREGIDO: se conserva el lado con cambio de signo
        if f_a*f_xi < 0: b, f_b = xi, f_xi
        else: a, f_a = xi, f_xi
        x_anterior = xi

    datos={
        "funcion":funcion,
        "valor_final":xi,
        "raiz": raiz.copy(),
        "iteraciones":iteraciones.copy()
    }
    return datos

def Secante(funcion):
    x = sp.Symbol('x')
    f_num = sp.lambdify(x, funcion, 'numpy')

    tol = 0.001
    max_iter = 10
    x0 = 0
    f_X0 = f_num(x0)
    xi = 1
    f_Xi = f_num(xi)

    iteraciones = []
    iteraciones.append({                  # CORREGIDO: sin "iteracion ="
        "iteracion": 0,
        "x": x0,
        "f(x)": f_X0,
        "error": "---",
    })
    iteraciones.append({                  # CORREGIDO: sin "iteracion ="
        "iteracion": 1,
        "x": xi,
        "f(x)": f_Xi,
        "error": xi - x0,
    })

    for i in range(2,max_iter):
        x_nuevo = xi - (f_Xi*(xi -x0))/(f_Xi - f_X0)
        f_x_nuevo = f_num(x_nuevo)
        error = abs(x_nuevo - xi)

        iteracion ={
            "iteracion": i,
            "x": {"xi":x_nuevo, "x0":x0, "x1":xi, "f(x1)":f_Xi, "f(x0)":f_X0,},
            "f(x)": f_x_nuevo,
            "error": {"error":error, "xi":x_nuevo, "x0":xi},   # CORREGIDO
        }
        iteraciones.append(iteracion.copy())

        if(round(error, 3) <= tol):
            xi = x_nuevo
            break

        x0, f_X0 = xi, f_Xi
        xi, f_Xi = x_nuevo, f_x_nuevo 

    datos={
        "funcion":funcion,
        "valor_final":xi,
        "iteraciones":iteraciones.copy()
    }
    return datos


""" Complementos """
def Tabulacion(f_num):
    intervalos = []
    x0 = 0
    f0 = 0
    for i in range(-10, 100):
        x1 = i
        f1 = f_num(x1)

        if f1 * f0 < 0:
            intervalos.append(x0)
            intervalos.append(x1)
            return intervalos
        elif f1 == 0:
            x2 = i+1
            f2 = f_num(x2)
            intervalos.append(x0)
            intervalos.append(x2)
            return intervalos
        
        x0 = x1
        f0 = f1

    return None