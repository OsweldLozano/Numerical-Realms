#Librerias
import sympy as sp
from fractions import Fraction
import numpy as np
import os
import shutil
from pathlib import Path

#Programas
import utilidades as util

"""  Metodos  """

def NewtonRaphson(funcion):
    titulo = "NewtonRaphson"
    archivo = open(util.Ruta(titulo), "w")
    InicioEcuacionNoLineal(archivo, titulo, funcion)
    
    x = sp.Symbol('x')

    derivada = sp.diff(funcion, x)
    archivo.write("f'(x): " + str(derivada) + " \n\n")

    funcion_num = sp.lambdify(x, funcion, 'numpy')
    derivada_num = sp.lambdify(x, derivada, 'numpy')

    xi = 1
    tol = 0.000001
    max_iter = 100

    archivo.write("0 \t\t 1 \t\t --- \n")
    for i in range(1,max_iter):
        fx = funcion_num(xi)
        fpx = derivada_num(xi)

        if fpx == 0:
            archivo.write("Derivada = 0, no se puede continuar")
            archivo.close()
            return

        x_nuevo = xi - fx / fpx
        error = abs(x_nuevo - xi)

        archivo.write(str(i) + "\t\t" + format(x_nuevo, ".15f") + "\t\t" + format(error, ".15f") + "\n")

        if(error < tol):
            archivo.write("\n x = " + str(x_nuevo))
            archivo.close()
            return

        xi = x_nuevo

    archivo.write("\nMaxima iteración alcanzada")
    archivo.close()

def PuntoFijo(funcion, g):
    titulo = "PuntoFijo"
    archivo = open(util.Ruta(titulo), "w")
    InicioEcuacionNoLineal(archivo, titulo, funcion)
    x = sp.Symbol('x')
    g_num = sp.lambdify(x, g, 'numpy')

    archivo.write("x = " + str(g) + " \n\n")

    xi = 0
    tol = 0.00001
    max_iter = 100

    archivo.write("0 \t\t 0 \t\t --- \n")
    for i in range(1,max_iter):
        x_nuevo = g_num(xi)
        error = abs(x_nuevo - xi)

        archivo.write(str(i) + "\t\t" + format(x_nuevo, ".15f") + "\t\t" + format(error, ".15f") + "\n")

        if(error < tol):
            archivo.write("\n x = " + str(x_nuevo))
            archivo.close()
            return

        xi = x_nuevo

    archivo.write("\nMaxima iteración alcanzada")
    archivo.close()

def FalsaPosicion(funcion):
    titulo = "FalsaPosicion"
    archivo = open(util.Ruta(titulo), "w")
    InicioEcuacionNoLineal(archivo, titulo, funcion)

    x = sp.Symbol('x')
    f_num = sp.lambdify(x, funcion, 'numpy')

    puntos = Tabulacion(f_num, archivo)
    archivo.write("\n")
    if(puntos == None):
        archivo.write("No se encontro ninguna raiz")
        archivo.close()
        return

    a, b = puntos[0], puntos[1]
    f_a, f_b = f_num(a), f_num(b)


    tol = 0.001
    max_iter = 100

    archivo.write("0 \t\t" + str(b) + "\t\t" + str(f_b) + "\t\t" + str(a) + "\t\t --- \t\t" + str(f_a) + "\t\t ---  \n")

    for i in range(1,max_iter):

        xi = a - ((f_a * (b - a))/(f_b - f_a))

        error = abs(a - xi)

        archivo.write(str(i) + "\t\t" + str(b) + "\t\t" + str(f_b) + "\t\t" + format(a, ".15f") + "\t\t" + format(xi, ".15f") + "\t\t" + format(f_a, ".15f") + "\t\t" + format(error, ".15f") +  "\n")

        if(round(error, 3) <= tol):
            archivo.write("\n x = " + str(xi))
            archivo.close()
            return

        a = xi
        f_a = f_num(a)

    archivo.write("\nMaxima iteración alcanzada")
    archivo.close()

def Secante(funcion):
    titulo = "Secante"
    archivo = open(util.Ruta(titulo), "w")
    InicioEcuacionNoLineal(archivo, titulo, funcion)

    x = sp.Symbol('x')
    f_num = sp.lambdify(x, funcion, 'numpy')

    tol = 0.001
    max_iter = 100
    x0 = 0
    f_X0 = f_num(x0)
    xi = 1
    f_Xi = f_num(xi)

    archivo.write("0 \t\t" + str(x0) + "\t\t" + str(f_X0) + "\t\t --- \n")
    archivo.write("1 \t\t" + str(xi) + "\t\t" + str(f_Xi) + "\t\t" + str(xi - x0) + "\n")

    for i in range(2,max_iter):

        x_nuevo = xi - (f_Xi*(xi -x0))/(f_Xi - f_X0)
        f_x_nuevo = f_num(x_nuevo)
        error = abs(x_nuevo - xi)

        archivo.write(str(i) + "\t\t" + format(x_nuevo, ".15f")+ "\t\t" + format(f_x_nuevo, ".15f") + "\t\t" + format(error, ".15f") +  "\n")

        if(round(error, 3) <= tol):
            xi = x_nuevo
            archivo.write("\n x = " + str(xi))
            archivo.close()
            return

        x0, f_X0 = xi, f_Xi
        xi, f_Xi = x_nuevo, f_x_nuevo 
        

    archivo.write("\nMaxima iteración alcanzada")    
    archivo.close()



"""  Complementos  """
