#Librerias
import sympy as sp
from fractions import Fraction
import numpy as np

"""  Metodos  """
def Montante(matriz):
    matriz0 = np.array(matriz, dtype=Fraction)
    matrizi = np.array(matriz, dtype=Fraction)
    n = len(matriz)
    pivote_anterior = 1

    try:
        iteraciones = []
        for k in range(n):

            iteracion = {}
            pasos = []
            for i in range(n):
                if(i == k):
                    continue

                for j in range(n+1):
                    paso = {}
                    if(j == k):
                        matrizi[i][j] = 0
                        continue

                    nuevo = Fraction(((matriz0[k][k]*matriz0[i][j])-(matriz0[i][k]*matriz0[k][j]))/pivote_anterior)
                    paso = {
                        "nuevo_elemento":nuevo,
                        "pivote_actual":matriz0[k][k],
                        "elemento_actual":matriz0[i][j],
                        "elemento_columna":matriz0[i][k],
                        "elemento_fila":matriz0[k][j],
                        "pivote_anterior":pivote_anterior
                    }
                    matrizi[i][j] = nuevo
                    pasos.append(paso.copy())
            iteracion = {
                "pasos":pasos.copy(),
                "matriz":matrizi.copy()
            }
            pivote_anterior = matriz0[k][k]
            matriz0 = matrizi.copy()
            iteraciones.append(iteracion.copy())

    except ZeroDivisionError:
        return {"error": "division_cero"}

    try:
        for k in range(n):
            matrizi[k][n] /= matrizi[k][k]
            matrizi[k][k] /= matrizi[k][k]
    except ZeroDivisionError: 
        return {"error": "division_cero"}

    incognitas=[]
    for k in range(n):
        incognitas.append(matrizi[k][n])

    datos = {
        "iteraciones":iteraciones.copy(),
        "matriz":matrizi.copy(),
        "incognitas":incognitas.copy()
    }
    return datos

def GaussJordan(matriz):
    matriz0 = np.array(matriz, dtype=Fraction)
    matrizi = np.array(matriz, dtype=Fraction)
    n = len(matriz)

    try:
        iteraciones = []
        for g in range(n):
            iteracion = {}
            pasos = []

            for i in range(n+1):
                matrizi[g][i] = matrizi[g][i] / matriz0[g][g]

            for i in range(n):
                if(i == g):
                    continue
                k = Fraction(-matrizi[i][g])

                for j in range(g,n+1):
                    paso = {}

                    Rv = Fraction(matrizi[g][j])
                    Ri = Fraction(matriz0[i][j])
                    nuevo = Fraction(k*Rv + Ri)

                    paso = {
                        "elemento":("x" + str(j)),
                        "nuevo":nuevo,
                        "k":k,
                        "Rv":Rv,
                        "Ri":Ri
                    }
                    matrizi[i][j] = nuevo
                    pasos.append(paso.copy())

            iteracion = {
                "pasos":pasos.copy(),
                "matriz":matrizi.copy()
            }
            matriz0 = matrizi.copy()
            iteraciones.append(iteracion.copy())
    except ZeroDivisionError:
        return {"error": "division_cero"}

    incognitas=[]
    for k in range(n):
        incognitas.append(matrizi[k][n])

    datos = {
        "iteraciones":iteraciones.copy(),
        "matriz":matriz,
        "matriz_final":matriz0.copy(),
        "incognitas":incognitas.copy()
    }
    return datos 

def EliminacionGaussiana(matriz):
    matriz0 = np.array(matriz, dtype=Fraction)
    n = len(matriz)

    try:
        iteraciones = []
        for k in range(n):
            g = Fraction(matriz0[k][k])
            iteracion = {}
            pasos = []

            for j in range(n+1):
                matriz0[k][j] = Fraction(matriz0[k][j] / g)

            for i in range(k,n):
                if(i == k):
                    continue

                h = Fraction(-matriz0[i][k])
                for j in range(k,n+1):
                    paso = {}
                    Rv = Fraction(matriz0[k][j])
                    Ri = Fraction(matriz0[i][j])
                    nuevo = Fraction(h*Rv + Ri)
                    matriz0[i][j] = nuevo

                    paso = {
                        "elemento":("x" + str(j)),
                        "nuevo":nuevo,
                        "k":h,
                        "Rv":Rv,
                        "Ri":Ri
                    }
                    pasos.append(paso.copy())

            iteracion = {
                "pasos":pasos.copy(),
                "matriz":matriz0.copy()
            }
            iteraciones.append(iteracion.copy())

    except ZeroDivisionError:
        return{"error": "division_cero"}

    variables = [Fraction(0)]*n
    variables[n-1] = Fraction(matriz0[n-1][n])
    for i in range(1,n):
        valor = Fraction(matriz0[n-1-i][n])
        for k in range(i):
            valor -= matriz0[n-1-i][n-1-k] * variables[n-1-k]
        variables[n-1-i] = Fraction(valor)

    datos = {
        "iteraciones":iteraciones.copy(),
        "matriz":matriz,
        "matriz_final":matriz0.copy(),
        "incognitas":variables.copy()
        }
    return datos 
    
def GaussSeidel(matriz):
    if(not DiagonalDominante(matriz)):
        return

    xs, despejes = Despeje(matriz)
    fun = [sp.lambdify(xs, d, 'math') for d in despejes]

    lista_despejes = []                            
    for variable, expresion in zip(xs, despejes):
        despeje ={
            "expresion": expresion,
            "variable": variable
        }
        lista_despejes.append(despeje.copy())
    despejes = lista_despejes

    n = len(xs)
    x = [0]*n

    tol = 0.001
    max_iter = 10

    iteraciones = []
    for k in range(1, max_iter + 1):
        x_ant = x.copy()
        for i in range(n):
            x[i] = fun[i](*x)

        errores = [abs(nuevo - ant) for nuevo, ant in zip(x, x_ant)]

        iteracion = {
            "valores": x.copy(),
            "errores": errores.copy()
        }
        iteraciones.append(iteracion.copy())

        if(round(max(errores), 3) <= tol):
            break                                    

    datos = {
        "iteraciones":iteraciones.copy(),
        "matriz":matriz,
        "despejes":despejes.copy(),
        "incognitas":x.copy()
    }
    return datos

def Jacobi(matriz):
    if(not DiagonalDominante(matriz)):
        return
    
    xs, despejes = Despeje(matriz)
    fun = [sp.lambdify(xs, d, 'math') for d in despejes]

    lista_despejes = []                             
    for variable, expresion in zip(xs, despejes):
        despeje ={
            "expresion": expresion,
            "variable": variable
        }
        lista_despejes.append(despeje.copy())
    despejes = lista_despejes
    
    n = len(xs)
    x = [1]*n
    
    tol = 0.001
    max_iter = 10
    
    iteraciones = []
    for k in range(1, max_iter + 1):
        x_ant = x
        x = [f(*x_ant) for f in fun]  

        errores = [abs(nuevo - ant) for nuevo, ant in zip(x, x_ant)]

        iteracion = {
            "valores": x.copy(),
            "errores": errores.copy()
        }
        iteraciones.append(iteracion.copy())
    
        if(round(max(errores), 3) <= tol):
            break                                

    datos = {
        "iteraciones":iteraciones.copy(),
        "matriz":matriz,
        "despejes":despejes.copy(),
        "incognitas":x.copy()
    }
    return datos


"""  Complementos  """

def DiagonalDominante(matriz):
    matrizA = np.array(matriz, dtype=float)
    n = matrizA.shape[0]
    for i in range(n):
        suma_fila = np.sum(np.abs(matrizA[i])) - np.abs(matrizA[i][i]) - np.abs(matrizA[i][n])
        if np.abs(matrizA[i][i]) <= suma_fila:
            return False
    return True

def a_sympy(valor):
    if isinstance(valor, Fraction):
        return sp.Rational(valor.numerator, valor.denominator)
    return sp.nsimplify(valor)

def Despeje(matriz):
    n = len(matriz)

    xs = sp.symbols(f"x1:{n + 1}")
    despejes = []
    for i in range(n):
        suma = sum(a_sympy(matriz[i][j]) * xs[j] for j in range(n) if j != i)
        despejes.append((a_sympy(matriz[i][n]) - suma) / a_sympy(matriz[i][i]))

    return xs, despejes
