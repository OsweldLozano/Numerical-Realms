#Librerias
import sympy as sp
from fractions import Fraction
import numpy as np
import os
import shutil
from pathlib import Path
from enum import Enum



"""  Metodos  """

def ReglaTrapezoidal(integral):
    expresion, a, b, n = integral.funcion, integral.a, integral.b, integral.n
    h = (b - a)/n 

    pasos, lista = intervalos(expresion, n, a, h)

    l = (h/2)*(lista[0] + 2*sum(lista[1:-1]) + lista[-1]) 

    datos = {
        "integral": integral,
        "l": l,
        "h": h,
        "pasos": pasos.copy()
    }
    return datos

def Regla1_3Simpson(integral):
    expresion, a, b, n = integral.funcion, integral.a, integral.b, integral.n

    if(n % 2): return {"integral": integral, "error": "intervalos impares"}

    h = (b - a)/n 

    pasos, lista = intervalos(expresion, n, a, h)

    l = (h/3)*(lista[0] + 4*sum(lista[1:-1:2]) + 2*sum(lista[2:-1:2]) + lista[-1]) 

    datos = {
        "integral": integral,
        "l": l,
        "h": h,
        "pasos": pasos.copy()
    }
    return datos

def Regla3_8Simpson(integral):
    expresion, a, b, n = integral.funcion, integral.a, integral.b, integral.n

    if(not(n % 2)): return {"integral": integral, "error": "intervalos pares"}

    h = (b - a)/n 

    pasos, lista = intervalos(expresion, n, a, h)

    l = (h)*(3/8)*(lista[0] + 3*sum(lista[1:-1]) + lista[-1]) 

    datos = {
        "integral": integral,
        "l": l,
        "h": h,
        "pasos": pasos.copy()
    }
    return datos

def NewtonCotesCerradas(integral):
    expresion, a, b, n = integral.funcion, integral.a, integral.b, integral.n
    global NCC
    
    if((n < 1) or (n > 10)): return {"integral": integral, "error": "Fuera de tabla"}

    h = (b - a)/n 

    pasos, lista = intervalos(expresion, n, a, h)

    constantes = NCC[n]
    l = (h)*(constantes[0])*(sum(c * v for c, v in zip(constantes[1:], lista))) 

    datos = {
        "integral": integral,
        "l": l,
        "h": h,
        "pasos": pasos.copy()
    }
    return datos

def NewtonCotesAbiertas(integral):
    expresion, a, b, n = integral.funcion, integral.a, integral.b, integral.n

    if((n < 1) or (n > 6)): return {"integral": integral, "error": "Fuera de tabla"}

    h = (b - a)/(n + 2) 

    pasos, lista = intervalos(expresion, n+2, a, h)

    constantes = NCA[n]
    l = (h)*(constantes[0])*(sum(c * v for c, v in zip(constantes[1:], lista))) 

    datos = {
        "integral": integral,
        "l": l,
        "h": h,
        "pasos": pasos.copy()
    }
    return datos



""" Complementos """

# Integral definida
class integralDefinida:
    def __init__(self):
        print("Integral definida")
        self.funcion = sp.sympify(input("Funcion: "))
        self.a = Fraction(input("Valor inicial(a): "))
        self.b = Fraction(input("Valor final(b): "))
        self.n = int(input("Numero de intervalos(n): "))

# Constantes para las fórmulas Cerradas de Newton – Cotes
NCC = {
    1: [Fraction("1/2"), 1, 1],
    2: [Fraction("1/3"), 1, 4, 1],
    3: [Fraction("3/8"), 1, 3, 3, 1],
    4: [Fraction("2/45"), 7, 32, 12, 32, 7],
    5: [Fraction("5/288"), 19, 75, 50, 50, 75, 19],
    6: [Fraction("1/140"), 41, 216, 27, 272, 27, 216, 41],
    7: [Fraction("7/17280"), 751, 3577, 1323, 2989, 2989, 1323, 3577, 751],
    8: [Fraction("14/14175"), 989, 5888, -928, 10946, -4540, 10946, -928, 5888, 989],
    9: [Fraction("9/89600"), 2857, 15741, 1080, 19344, 5788, 5788, 19344, 1080, 15741, 2857],
    10: [Fraction("5/299376"), 16067, 106300, -48525, 272400, -260550, 427368, -260550, 272400, -48525, 106300, 16067]
}

# Constantes para las fórmulas Abiertas de Newton – Cotes
NCA = {
    1: [Fraction("3/2"), 0, 1, 1, 0],
    2: [Fraction("4/3"), 0, 2, -1, 2, 0],
    3: [Fraction("5/24"), 0, 11, 1, 1, 11, 0],
    4: [Fraction("6/20"), 0, 11, -14, 26, -14, 11, 0],
    5: [Fraction("7/1440"), 0, 611, -453, 562, 562, -453, 611, 0],
    6: [Fraction("8/945"), 0, 460, -954, 2196, -2459, 2196, -954, 460, 0]
}

# Solver de cada uno de los intervalos
def intervalos(expresion, n, a, h):
    x = sp.symbols('x')
    funcion = sp.lambdify(x, expresion)
    
    lista = [] 
    pasos = []
    for i in range(n+1):
        paso = {}
    
        valor = a + i*h
        resultado = funcion(valor)
    
        lista.append(resultado)
        paso = {
            "x": (str(i) + "/" + str(n)),
            "texto": str(expresion.subs(x, sp.UnevaluatedExpr(valor))),
            "valor": resultado
        }
        pasos.append(paso.copy())
    return pasos, lista

