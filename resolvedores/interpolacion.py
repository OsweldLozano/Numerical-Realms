#Librerias
import sympy as sp
import numpy as np
import math


"""  Metodos  """

def InterpolacionLineal(valor, a, b, expresion,):
    x = sp.symbols('x')
    funcion = sp.lambdify(x, expresion)

    f_a = funcion(a)
    f_b = funcion(b)
    f_x = funcion(valor)

    g_x = ((f_b - f_a)/(b - a))*(valor - a) + f_a       

    error = abs(f_x - g_x)

    datos = {
        "x": valor,
        "a": a,
        "b": b,
        "f_x": f_x,
        "f_a": f_a,                                     
        "f_b": f_b,
        "g_x": g_x,
        "error": error
    }
    return datos

def NewtonHaciaAdelante(x, tabla):
    n = len(tabla)

    # Uniformidad
    h = tabla[1][0] - tabla[0][0]
    listah = []
    for i in range(n-1):
        x1 = tabla[i+1][0]
        x0 = tabla[i][0]
        hi = x1 - x0
        listah.append({"hi":hi,"x1":x1,"x0":x0})    

    # Discriminante
    delta, discriminante, entrada, salida = [],[],[],[]
    for i in range(n): entrada.append(tabla[i][1])
    for i in range(n-1):
        for j in range(n-1-i):
            y1 = entrada[j+1]
            y0 = entrada[j]
            valor = y1 - y0
            salida.append(valor)
            discriminante.append(valor)
            delta.append({"valor":valor,"y1":y1,"y0":y0})
        entrada = salida.copy()
        salida.clear()
    
    # S
    xi = tabla[0][0]
    s = (x - xi)/h
    valors = {"s":s,"x":x,"xi":xi,"h":h}

    # g(x)
    coeficiente = []
    coeficiente.append(tabla[0][1])
    i, j = 0, n
    while(len(coeficiente) < n):
        coeficiente.append(discriminante[i])               
        j -= 1
        i += j

    g_x = 0
    operacion = []
    for i in range(n):
        if (i==0): factor = 1 
        elif (i==1): factor = s
        else: 
            multiplo = s
            for j in range(1,i): multiplo *= s-j
            factor = multiplo/math.factorial(i)
        valor = coeficiente[i]*factor
        g_x += valor
        operacion.append({"valor":valor, "coeficiente":coeficiente[i], "factor":factor})

    valorg_x = {
        "valor":g_x,
        "operacion": operacion
    }

    datos = {
        "x": x,
        "tabla": tabla,
        "h": listah,
        "delta": delta,
        "s": valors,
        "g_x": valorg_x
    }
    return datos

def NewtonHaciaAtras(x, tabla):
    n = len(tabla)

    # Uniformidad
    h = tabla[1][0] - tabla[0][0]
    listah = []
    for i in range(n-1):
        x1 = tabla[i+1][0]
        x0 = tabla[i][0]
        hi = x1 - x0
        listah.append({"hi":hi,"x1":x1,"x0":x0})    

    # Discriminante
    delta, discriminante, entrada, salida = [],[],[],[]
    for i in range(n): entrada.append(tabla[i][1])
    for i in range(n-1):
        for j in range(n-1-i):
            y1 = entrada[j+1]
            y0 = entrada[j]
            valor = y1 - y0
            salida.append(valor)
            discriminante.append(valor)
            delta.append({"valor":valor,"y1":y1,"y0":y0})
        entrada = salida.copy()
        salida.clear()
    
    # S
    xi = tabla[-1][0]
    s = (x - xi)/h
    valors = {"s":s,"x":x,"xi":xi,"h":h}

    # g(x)
    coeficiente = []
    coeficiente.append(tabla[-1][1])
    i, j = n-2, n-2
    while(len(coeficiente) < n):
        coeficiente.append(discriminante[i])             
        i += j
        j -= 1

    g_x = 0
    operacion = []
    for i in range(n):
        if (i==0): factor = 1 
        elif (i==1): factor = s
        else: 
            multiplo = s
            for j in range(1,i): multiplo *= s+j
            factor = multiplo/math.factorial(i)
        valor = coeficiente[i]*factor
        g_x += valor
        operacion.append({"valor":valor, "coeficiente":coeficiente[i], "factor":factor})

    valorg_x = {
        "valor":g_x,
        "operacion": operacion
    }

    datos = {
        "x": x,
        "tabla": tabla,
        "h": listah,
        "delta": delta,
        "s": valors,
        "g_x": valorg_x
    }
    return datos

def NewtonconDiferenciasDivididas(x, tabla):
    n = len(tabla)

    # Uniformidad
    h = tabla[1][0] - tabla[0][0]
    listah = []
    for i in range(n-1):
        x1 = tabla[i+1][0]
        x0 = tabla[i][0]
        hi = x1 - x0
        listah.append({"hi":hi,"x1":x1,"x0":x0})  

    # Diferencia
    delta, diferencia, entrada, salida = [],[],[],[]
    for i in range(n): entrada.append(tabla[i][1])
    for i in range(n-1):
        for j in range(n-1-i):
            y1 = entrada[j+1]
            y0 = entrada[j]
            x1 = tabla[j+i+1][0]
            x0 = tabla[j][0]
            valor = (y1 - y0)/(x1 - x0)
            salida.append(valor)
            diferencia.append(valor)
            delta.append({"valor":valor,"y1":y1,"y0":y0,"x1":x1,"x0":x0})  
        entrada = salida.copy()
        salida.clear()  

    # g(x)  
    coeficiente = []
    coeficiente.append(tabla[0][1])
    i, j = 0, n
    while(len(coeficiente) < n):
        coeficiente.append(diferencia[i])                  
        j -= 1
        i += j       
    
    g_x = 0
    operacion = []
    for i in range(n):
        if (i==0): factor = 1 
        else: 
            multiplo = 1
            for j in range(i): multiplo *= x-tabla[j][0]
            factor = multiplo
        valor = coeficiente[i]*factor
        g_x += valor
        operacion.append({"valor":valor, "coeficiente":coeficiente[i], "factor":factor})

    valorg_x = {
        "valor":g_x,
        "operacion": operacion
    }

    datos = {
        "x": x,
        "tabla": tabla,
        "h": listah,
        "delta": delta,
        "g_x": valorg_x
    }
    return datos    

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
        "x": x,
        "tabla": tabla,
        "pasos":pasos.copy(),
        "g_x": g_x
    }
    return datos

