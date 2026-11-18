#Librerias
import sympy as sp
from fractions import Fraction
import numpy as np



"""  Metodos  """

def EulerModificado(expresion, h, yn, yn1, tn=0, n=2): 
    y,t = sp.symbols("y t")
    funcion = sp.lambdify([y,t], expresion)

    yi = 0
    iteraciones = []
    y0,y1,t0,t1, = yn,yn1,tn,tn+h
    for i in range(1,n+1):
        yi = y0 + (h/2)*(funcion(y0,t0) + funcion(y1,t1))

        iteracion={
            "yi": yi,
            "y0": y0,
            "y1": y1,
            "t0": t0,
            "t1": t1
        }
        iteraciones.append(iteracion.copy())

        y0 = yi                         
        t0 = t1
        t1 = t1+h
        y1 = y0 + h*funcion(y0, t0)     

    datos={
        "expresion": expresion,
        "iteraciones": iteraciones.copy()
    }
    return datos

def EulerHaciaAdelante(expresion, h, yn, tn=0, n=2): 
    y,t = sp.symbols("y t")
    funcion = sp.lambdify([y,t], expresion)

    yi = 0
    iteraciones = []
    y0,t0 = yn,tn
    for i in range(1,n+1):
        yi = y0 + h*funcion(y0,t0)

        iteracion={
            "yi": yi,
            "y0": y0,
            "t0": t0
        }
        iteraciones.append(iteracion.copy())

        y0 = yi
        t0 = t0+h

    datos={
        "expresion": expresion,
        "iteraciones": iteraciones.copy()
    }
    return datos

def EulerHaciaAtras(expresion, yn, yn1, h, tn=0, n=2): 
    y,t = sp.symbols("y t")
    funcion = sp.lambdify([y,t], expresion)

    yi = 0
    iteraciones = []
    y0,y1,t1, = yn,yn1,tn+h
    for i in range(1,n+1):
        yi = y0 + h*funcion(y1,t1)

        iteracion={
            "yi": yi,
            "y0": y0,
            "y1": y1,
            "t1": t1
        }
        iteraciones.append(iteracion.copy())

        y0 = yi                         
        y1 = y0 + h*funcion(y0, t1)     
        t1 = t1+h

    datos={
        "expresion": expresion,
        "iteraciones": iteraciones.copy()
    }
    return datos

def RungeKutta2Orden(expresion, h, yn, tn=0, n=2): 
    y,t = sp.symbols("y t")
    funcion = sp.lambdify([y,t], expresion)

    yi = 0
    iteraciones = []
    y0,t0, = yn,tn
    for i in range(1,n+1):
        k1 = h*funcion(y0,t0)
        k2 = h*funcion(y0+k1,t0+h)
        yi = y0 + (1/2)*(k1+k2)

        iteracion={
            "k1": {"k":k1,"h":h,"y":y0,"t":t0},
            "k2": {"k":k2,"h":h,"y":y0+k1,"t":t0+h},  
            "yi": {"yi":yi,"k1":k1,"k2":k2}
        }
        iteraciones.append(iteracion.copy())

        y0 = yi
        t0 = t0+h

    datos={
        "expresion": expresion,
        "iteraciones": iteraciones.copy()
    }
    return datos

def RungeKutta3Orden(expresion, h, yn, tn=0, n=2): 
    y,t = sp.symbols("y t")
    funcion = sp.lambdify([y,t], expresion)

    yi = 0
    iteraciones = []
    y0,t0, = yn,tn
    for i in range(1,n+1):
        k1 = h*funcion(y0,t0)
        k2 = h*funcion(y0 + k1/2, t0 + h/2)
        k3 = h*funcion(y0 - k1 + 2*k2, t0 + h)      
        yi = y0 + (1/6)*(k1 + 4*k2 + k3)

        iteracion={
            "k1": {"k":k1,"h":h,"y":y0,"t":t0},
            "k2": {"k":k2,"h":h,"y":y0 + k1/2,"t":t0 + h/2},
            "k3": {"k":k3,"h":h,"y":y0 - k1 + 2*k2,"t":t0 + h},   
            "yi": {"yi":yi,"k1":k1,"k2":k2,"k3":k3}
        }
        iteraciones.append(iteracion.copy())

        y0 = yi
        t0 = t0+h

    datos={
        "expresion": expresion,
        "iteraciones": iteraciones.copy()
    }
    return datos

def RungeKutta4Orden1_3Simpson(expresion, h, yn, tn=0, n=2): 
    y,t = sp.symbols("y t")
    funcion = sp.lambdify([y,t], expresion)

    yi = 0
    iteraciones = []
    y0,t0, = yn,tn
    for i in range(1,n+1):
        k1 = h*funcion(y0,t0)
        k2 = h*funcion(y0 + k1/2, t0 + h/2)
        k3 = h*funcion(y0 + k2/2, t0 + h/2)
        k4 = h*funcion(y0 + k3, t0 + h)
        yi = y0 + (1/6)*(k1 + 2*k2 + 2*k3 + k4)

        iteracion={
            "k1": {"k":k1,"h":h,"y":y0,"t":t0},
            "k2": {"k":k2,"h":h,"y":y0 + k1/2,"t":t0 + h/2},
            "k3": {"k":k3,"h":h,"y":y0 + k2/2,"t":t0 + h/2},
            "k4": {"k":k4,"h":h,"y":y0 + k3,"t":t0 + h},
            "yi": {"yi":yi,"k1":k1,"k2":k2,"k3":k3,"k4":k4}
        }
        iteraciones.append(iteracion.copy())

        y0 = yi
        t0 = t0+h

    datos={
        "expresion": expresion,
        "iteraciones": iteraciones.copy()
    }
    return datos

def RungeKutta4Orden3_8Simpson(expresion, h, yn, tn=0, n=2): 
    y,t = sp.symbols("y t")
    funcion = sp.lambdify([y,t], expresion)

    yi = 0
    iteraciones = []
    y0,t0, = yn,tn
    for i in range(1,n+1):
        k1 = h*funcion(y0,t0)
        k2 = h*funcion(y0 + k1/3, t0 + h/3)
        k3 = h*funcion(y0 - k1/3 + k2, t0 + h*(2/3))   
        k4 = h*funcion(y0 + k1 - k2 + k3, t0 + h)
        yi = y0 + (1/8)*(k1 + 3*k2 + 3*k3 + k4)

        iteracion={
            "k1": {"k":k1,"h":h,"y":y0,"t":t0},
            "k2": {"k":k2,"h":h,"y":y0 + k1/3,"t":t0 + h/3},
            "k3": {"k":k3,"h":h,"y":y0 - k1/3 + k2,"t":t0 + h*(2/3)},  
            "k4": {"k":k4,"h":h,"y":y0 + k1 - k2 + k3,"t":t0 + h},
            "yi": {"yi":yi,"k1":k1,"k2":k2,"k3":k3,"k4":k4}
        }
        iteraciones.append(iteracion.copy())

        y0 = yi
        t0 = t0+h

    datos={
        "expresion": expresion,
        "iteraciones": iteraciones.copy()
    }
    return datos

def RungeKuttaOrdenSuperior(expresion, h, yn, ypn, tn=0, n=2): 
    yp,y,t = sp.symbols("yp y t")
    funcion = sp.lambdify([yp,y,t], expresion)

    yi, ypi = 0,0
    iteraciones = []
    Vn,Un,qn, = ypn,yn,tn
    for i in range(1,n+1):
        k1 = h*Vn
        m1 = h*funcion(Vn,Un,qn)
        k2 = h*(Vn + m1)
        m2 = h*funcion(Vn + m1, Un + k1, qn + h)

        yi = Un + (1/2)*(k1 + k2)
        ypi = Vn + (1/2)*(m1 + m2)

        iteracion={
            "k1": {"k1":k1, "h":h, "Vn":Vn},
            "m1": {"m1":m1, "h":h, "Vn":Vn, "Un":Un, "qn":qn},
            "k2": {"k2":k2, "h":h, "Vn":Vn + m1},
            "m2": {"m2":m2, "h":h, "Vn":Vn + m1, "Un":Un + k1, "qn":qn + h},
            "yi": {"yi":yi, "Un":Un, "k1":k1, "k2":k2},
            "ypi": {"ypi":ypi, "Vn":Vn, "m1":m1, "m2":m2}
        }
        iteraciones.append(iteracion.copy())

        Vn = ypi
        Un = yi
        qn = qn + h

    datos={
        "expresion": expresion,
        "iteraciones": iteraciones.copy()
    }
    return datos


