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

def InterpolacionLineal(x, tabla):
    inferior = Inferior(tabla, x)
    superior = Superior(tabla, x)
    if((inferior is False) or (superior is False)):
        return {"error": "x_fuera_de_rango"}

    a = tabla[inferior][0]
    f_a = tabla[inferior][1]
    b = tabla[superior][0]
    f_b = tabla[superior][1]
    g_x = ((f_b - f_a) / (b - a)) * (x - a) + f_a

    datos = {
        "a": a,
        "b": b,
        "f_a": f_a,
        "f_b": f_b,
        "g_x": g_x
    }
    return datos

def NewtonHaciaAdelante(x, tabla):
    titulo = "NewtonHaciaAdelante"
    archivo = open(util.Ruta(titulo), "w")
    InicioInterpolar(archivo, titulo, tabla, x)

    h = tabla[1][0] - tabla[0][0]
    if(not Uniformidad(tabla,h,archivo)):
        archivo.write("No se puede resolver \n")
        archivo.close()
        return

    n = len(tabla)
    discriminante = NewtonDelta(tabla, n)

    for i in range(n):
        archivo.write("\n")
        for j in range(n+1-i):
            if(j<2):
                archivo.write(util.strf(tabla[i][j]) + "\t\t")
                continue
            archivo.write(util.strf(discriminante[j-2][i]) + "\t\t")
    archivo.write("\n\n")

    s = S(x,tabla[0][0],h, archivo)

    g_x = tabla[0][1] + discriminante[0][0]*s
    archivo.write("g(x) = (" + util.strf(tabla[0][1]) + ")(1) + (" + util.strf(discriminante[0][0]) + ")(" + util.strf(s) + ")")

    for i in range(n-2):
        multiplo = s
        archivo.write(" + (" + util.strf(discriminante[i+1][0]) + ")((" + util.strf(s) + ")")

        for j in range(1, i + 2):
            multiplo *= (s-j)
            archivo.write("(" + util.strf(s) + " - " + str(j) + ")")
        archivo.write(")/" + str(i+2) + "!")

        g_x += discriminante[i+1][0] * (multiplo/Factorial(i+2))
    archivo.write(" = " + util.strf(g_x))

    archivo.close()

def NewtonHaciaAtras(x, tabla):
    titulo = "NewtonHaciaAtras"
    archivo = open(util.Ruta(titulo), "w")
    InicioInterpolar(archivo, titulo, tabla, x)

    h = tabla[1][0] - tabla[0][0]
    if(not Uniformidad(tabla,h,archivo)):
        archivo.write("No se puede resolver \n")
        archivo.close()
        return

    n = len(tabla)
    gradiente = NewtonDelta(tabla, n)

    for i in range(n):
            archivo.write("\n")
            for j in range(2+i):
                if(j<2):
                    archivo.write(util.strf(tabla[i][j]) + "\t\t\t")
                    continue
                archivo.write(util.strf(gradiente[j-2][i-4]) + "\t\t\t")
    archivo.write("\n\n")

    s = S(x,tabla[-1][0],h, archivo)

    g_x = tabla[-1][1] + gradiente[0][-1]*s
    archivo.write("g(x) = (" + util.strf(tabla[-1][1]) + ")(1) + (" + util.strf(gradiente[0][-1]) + ")(" + util.strf(s) + ")")
    
    for i in range(n-2):
        multiplo = s
        archivo.write(" + (" + util.strf(gradiente[i+1][-1]) + ")((" + util.strf(s) + ")")
    
        for j in range(1, i + 2):
            multiplo *= (s+j)
            archivo.write("(" + util.strf(s) + " + " + str(j) + ")")
        archivo.write(")/" + str(i+2) + "!")
    
        g_x += gradiente[i+1][-1] * (multiplo/Factorial(i+2))
    archivo.write(" = " + util.strf(g_x))

    archivo.close()

def NewtonconDiferenciasDivididas(x, tabla):
    titulo = "NewtonconDiferenciasDivididas"
    archivo = open(util.Ruta(titulo), "w")
    InicioInterpolar(archivo, titulo, tabla, x)
    
    n = len(tabla)
    diferencia = NewtonDiferencia(tabla, n)
    
    for i in range(n):
        archivo.write("\n")
        for j in range(n+1-i):
            if(j<2):
                archivo.write(util.strf(tabla[i][j]) + "\t\t")
                continue
            archivo.write(util.strf(diferencia[j-2][i]) + "\t\t")
    archivo.write("\n\n")


    g_x = tabla[0][1]
    archivo.write("g(x) = (" + util.strf(tabla[0][1]) + ")")

    for i in range(n-1):
        multiplo = Fraction(1)
        archivo.write(" + (" + util.strf(diferencia[i][0]) + ")")

        for j in range(i+1):
            multiplo *= Fraction(x-tabla[j][0])
            archivo.write("(" + str(x) + " - " + util.strf(tabla[j][0]) + ")")

        g_x += Fraction(diferencia[i][0] * multiplo)
    archivo.write("\ng(x) = " + util.strf(g_x))

    archivo.close()

def Lagrange(x, tabla):
    n = len(tabla)
    g_x = 0

    pasos=[]
    for i in range(n):
        arriba={"x":x, "lista":[]}
        abajo={"x":tabla[i][0], "lista":[]}

        multiplo = 1
        dividendo = 1

        lista=[]
        for j in range(n):
            if(i == j):
                continue
            multiplo *= x - tabla[j][0]
            lista.append(tabla[j][0])
        arriba["lista"] = lista.copy()

        lista=[]
        for j in range(n):
            if(i == j):
                continue
            dividendo *= tabla[i][0] - tabla[j][0]
            lista.append(tabla[j][0])
        abajo["lista"] = lista.copy()

        try:
            valor = tabla[i][1] * (multiplo/dividendo)
        except ZeroDivisionError:
            return {"error": "division_cero"}
        g_x += valor

        paso={
            "y": tabla[i][1],
            "arriba": arriba.copy(),
            "abajo": abajo.copy(),
            "valor": valor
        }
        pasos.append(paso.copy())

    datos={
        "pasos":pasos.copy(),
        "g_x": g_x
    }
    return datos



"""  Complementos  """

def InicioInterpolar(archivo, titulo, tabla, x):
    
    archivo.write(titulo)
    archivo.write(f"\n\nElemento buscado (X): {util.strf(x)}")
    archivo.write("\n\nTabla: ")
    n = len(tabla)
    for i in range(n):
        a,b = util.strf(tabla[i][0]), util.strf(tabla[i][1])
        archivo.write(f"\n {i}:  {a}  {b}")
    archivo.write("\n")

def Inferior(tabla, x):
    lugar = -1
    n = len(tabla)
    for i in range(n):
        if((tabla[i][0] < x)):
            valor = tabla[i][0]
            lugar = i
            break

    if(lugar == -1):
        return False
    
    for i in range(n):
        if((tabla[i][0] >= valor) and (tabla[i][0] < x)):
            valor = tabla[i][0]
            lugar = i

    return lugar

def Superior(tabla, x):
    lugar = -1
    n = len(tabla)
    for i in range(n):
        if((tabla[i][0] > x)):
            valor = tabla[i][0]
            lugar = i
            break

    if(lugar == -1):
        return False
    
    for i in range(n):
        if((tabla[i][0] <= valor) and (tabla[i][0] > x)):
            valor = tabla[i][0]
            lugar = i

    return lugar

def Uniformidad(tabla,h,archivo):
    eps = 1e-9
    n = len(tabla)

    archivo.write("Intervalos: \n")
    for i in range(n-1):
        hi = tabla[i+1][0] - tabla[i][0]
        archivo.write("h" + str(i+1) + " = |" + str(tabla[i+1][0]) + " - " + str(tabla[i][0]) + "| = " + str(hi) + "\n")
        if(abs(h - hi) > eps):
            archivo.write("Intervalos No Uniformes \n\n")
            return False

    archivo.write("Intervalos Uniformes \n\n")
    return True

def NewtonDelta(tabla, n):
    delta = []
    entrada = []
    salida = [] 

    for i in range(n):
        entrada.append(tabla[i][1])

    for i in range(n-1):
        for j in range(n-1-i):
            salida.append(entrada[j+1]-entrada[j])
        delta.append(salida.copy())
        entrada = salida.copy()
        salida.clear()

    return delta

def S(x,xi,h, archivo):
    s = (x - xi)/h
    archivo.write( "s = (" + str(x) + " - " + str(xi) + ")/" + str(h) + " = " + str(s) + "\n\n" )
    return s

def Factorial(n):
    x = 1
    for i in range(n):
        x *= i+1    
    return x

def NewtonDiferencia(tabla, n):
    delta = []
    entrada = []
    salida = [] 
    
    for i in range(n):
        entrada.append(Fraction(tabla[i][1]))
    
    for i in range(n-1):
        for j in range(n-1-i):
            multiplo = Fraction(entrada[j+1] - entrada[j])
            dividendo = Fraction(tabla[j+i+1][0] - tabla[j][0])
            salida.append(Fraction(multiplo/dividendo))
        delta.append(salida.copy())
        entrada = salida.copy()
        salida.clear()
    
    return delta

