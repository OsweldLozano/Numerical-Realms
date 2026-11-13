#Librerias
import sympy as sp
from fractions import Fraction
import numpy as np
import os
import shutil
from pathlib import Path

#Programas
import ecuacionesLineales as EcL


"""  Metodos  """

def LineaRecta(tabla):
    expresion = ["x","x**2","y","x*y"]
    n = len(tabla)

    valores = ValorSympy(tabla,expresion,expresion)

    z = {}
    for elemento in expresion:
        z[elemento] = sum(valores[elemento])

    matriz = np.array([
        [n,      z["x"],    z["y"]  ],
        [z["x"], z["x**2"], z["x*y"]]
        ],dtype= Fraction
    )

    datos = {
        "matriz": matriz,
        "expresion": expresion.copy(),
        "calculo":expresion.copy(),
        "valores": valores.copy(),
        "sumatoria": z.copy()
    }
    return datos

def Cuadratica(tabla):
    expresion = ["x","x**2","x**3","x**4","y","x*y","(x**2)*y"]
    n = len(tabla)

    valores = ValorSympy(tabla,expresion,expresion)

    z = {}
    for elemento in expresion:
        z[elemento] = sum(valores[elemento])

    matriz = np.array([
        [n,          z["x"],     z["x**2"],  z["y"]       ],
        [z["x"],     z["x**2"],  z["x**3"],  z["x*y"]     ],
        [z["x**2"],  z["x**3"],  z["x**4"],  z["(x**2)*y"]]
        ],dtype= Fraction
    )    

    datos = {
        "matriz": matriz,
        "expresion": expresion.copy(),
        "calculo":expresion.copy(),
        "valores": valores.copy(),
        "sumatoria": z.copy()
    }
    return datos 

def Cubica(tabla):
    expresion = ["x","x**2","x**3","x**4","x**5","x**6","y","x*y","(x**2)*y","(x**3)*y"]
    n = len(tabla)

    valores = ValorSympy(tabla,expresion,expresion)

    z = {}
    for elemento in expresion:
        z[elemento] = sum(valores[elemento])

    matriz = np.array([
        [n,          z["x"],     z["x**2"],  z["x**3"],  z["y"]       ],
        [z["x"],     z["x**2"],  z["x**3"],  z["x**4"],  z["x*y"]     ],
        [z["x**2"],  z["x**3"],  z["x**4"],  z["x**5"],  z["(x**2)*y"]],
        [z["x**3"],  z["x**4"],  z["x**5"],  z["x**6"],  z["(x**3)*y"]]
        ],dtype= Fraction
    )

    datos = {
        "matriz": matriz,
        "expresion": expresion.copy(),
        "calculo":expresion.copy(),
        "valores": valores.copy(),
        "sumatoria": z.copy()
    }
    return datos 

def LinealFuncion(tabla,funcion):
    expresion = ["x","x**2","f(x)","x*f(x)","f(x)**2","y","x*y","y*f(x)"]
    calculo = [e.replace("f(x)", "(" + funcion + ")") for e in expresion]
    n = len(tabla)

    valores = ValorSympy(tabla,expresion,calculo)

    z = {}
    for elemento in expresion:
        z[elemento] = sum(valores[elemento])

    matriz = np.array([
        [n,          z["x"],       z["f(x)"],     z["y"]     ],
        [z["x"],     z["x**2"],    z["x*f(x)"],   z["x*y"]   ],
        [z["f(x)"],  z["x*f(x)"],  z["f(x)**2"],  z["y*f(x)"]]
        ], dtype= object
    )

    datos = {
        "matriz": matriz,
        "expresion": expresion.copy(),
        "calculo":calculo.copy(),
        "valores": valores.copy(),
        "sumatoria": z.copy()
    }
    return datos     

def CuadraticaFuncion(tabla,funcion):
    expresion = ["x","x**2","x**3","x**4","f(x)","x*f(x)","(x**2)*f(x)","f(x)**2","y","x*y","(x**2)*y","y*f(x)"]
    calculo = [e.replace("f(x)", "(" + funcion + ")") for e in expresion]
    n = len(tabla)

    valores = ValorSympy(tabla,expresion,calculo)

    z = {}
    for elemento in expresion:
        z[elemento] = sum(valores[elemento])

    matriz = np.array([
        [n,          z["x"],       z["x**2"],         z["f(x)"],         z["y"]       ],
        [z["x"],     z["x**2"],    z["x**3"],         z["x*f(x)"],       z["x*y"]     ],
        [z["x**2"],  z["x**3"],    z["x**4"],         z["(x**2)*f(x)"],  z["(x**2)*y"]],
        [z["f(x)"],  z["x*f(x)"],  z["(x**2)*f(x)"],  z["f(x)**2"],      z["y*f(x)"]  ]
        ], dtype= object
    )

    datos = {
        "matriz": matriz,
        "expresion": expresion.copy(),
        "calculo":calculo.copy(),
        "valores": valores.copy(),
        "sumatoria": z.copy()
    }
    return datos 



"""  Complementos  """

def ValorSympy(tabla,expresion,calculo):
    x = sp.Symbol('x')
    y = sp.Symbol('y')
    valores = {}

    n = len(tabla)
    for clave,elemento in zip(expresion,calculo):
        expr = sp.sympify(elemento)
        lista = []
        for i in range(n):
            valor = expr.subs({x: tabla[i][0], y: tabla[i][1]})
            if valor.is_rational:
                valor = Fraction(valor.p, valor.q) #Fraction
            else:
                valor = valor.evalf() #Float
            lista.append(Fraction(valor))
        valores[clave] = lista.copy()
    return valores
