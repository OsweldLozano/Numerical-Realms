#Librerias
import sympy as sp
from fractions import Fraction
import numpy as np
import os
import shutil
from pathlib import Path
from enum import Enum
import random




class integralDefinida:
    def __init__(self, funcion, a, b, n):
        self.funcion = str(funcion)
        self.a = Fraction(a)
        self.b = Fraction(b)
        self.n = int(n)


def generadorTablas(n, opcion):
    z = random.choice([[3,0],[2,1]])
    funcion = generadorFuncion(z[0],z[1])
    pass

def generarIntegral(opcion):
    z = random.choice([[3,0],[2,1]])
    funcion = generadorFuncion(z[0],z[1])
    a = Fraction(Fraction(random.randint(1, 10), random.randint(1, 10)) + random.randint(1, 10))
    b = Fraction(a + Fraction(random.randint(1, 10), random.randint(1, 10)) + random.randint(1, 10))
    match opcion:
        case 0: n = random.randrange(3, 11, 2)
        case 1: n = random.randrange(4, 12, 2)
        case 2: n = random.randint(3, 10)
        case 3: n = random.randint(3, 6)
    return integralDefinida(funcion, a, b, n)

def generarDerivada():
    pass

def generadorMatriz(n):
    decimal = False
    while(True):
        # Genera las variables
        variables = []
        for i in range(n):
            x = random.randint(1, 10)
            if (decimal): x += Fraction(random.randint(1, 10),10)
            variables.append(x)

        # Genera el sistema de ecuaciones
        matriz = np.empty((n,n+1), dtype=object)
        for i in range(n):
            val = 0
            for j in range (n):
                num = random.randint(1, 10)
                matriz[i][j] = num
                val += num * variables[j]
            matriz[i][n] = Fraction(val)

        # comprobar que no hay duplicados 
        for i in range(n-1):
            fila1 = matriz[i]
            fila2 = matriz[i+1]
            if (np.array_equal(fila1, fila2)): continue

        return matriz, variables

def generadorFuncion(n,opcion):
    
    def polinomio(n):
        while(True): 
            string = "a*x**b"
            exp = ""

            for i in reversed(range(1,n)):
                val = string
                a = str(random.randint(0, 10))
                if (a == "0"): continue
                val = val.replace("a",a)
                val = val.replace("b",str(i))

                if (random.choice([True, False])): 
                    exp += " + "
                else:
                    exp += " - "
                exp += val

            a = str(random.randint(0, 10))
            if (random.choice([True, False])): 
                exp += " + " + a
            else:
                exp += " - " + a

            if ("1*x" in exp): exp = exp.replace("1*x","x")
            if ("x**1" in exp): exp = exp.replace("x**1","x")
            exp = exp.removeprefix(" + ")

            if (not("*x**" in exp)): continue

            return exp

    def expresion(n):
        error = 1
        while(True):
            error += 1
            if (error == 3): "5*sen(x)"

            lista = ["a*cos(b*x)","a*sen(b*x)","a*log(b*x)","a*exp(b*x)","a*x**(b)"]
            exp = ""
            for i in range(n):
                val = random.choice(lista)
                a = str(random.randint(0, 10))
                b = str(random.randint(0, 20)-10)
                if (a == "0" or b == "0"):continue
                val = val.replace("a",a)
                val = val.replace("b",b)

                if (random.choice([True, False])): 
                    exp += " + " + val
                else:
                    exp += " - " + val

            if ("1*" in exp): exp = exp.replace("1*","")
            if ("**(1)" in exp): exp = exp.replace("**(1)","")
            exp = exp.removeprefix(" + ")
            if (exp == ""): continue
            return exp

    match opcion:
        case 0: return polinomio(n)
        case 1: return expresion(n)


for i in range(10):
    z = random.choice([[3,0],[2,1]])
    funcion = generadorFuncion(2,1)
    print(funcion)


"""for i in range(7):
    n = random.randint(0, 3)
    x = generarIntegral(n)
    print(x.funcion)
    print(float(x.a))
    print(float(x.b))
    print(x.n)"""

"""for i in range(3):
    print()
    n = 3
    x,y = generadorMatriz(n)
    for i in range(n):
        val = ""
        for j in range(n+1):
            val += "  " + str(float(x[i][j]))
        print(val)
    val = ""
    for i in range(n):
        val += "   " + str(float(y[i]))
    print(val)"""




