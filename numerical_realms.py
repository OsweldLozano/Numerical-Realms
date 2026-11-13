"""
Numerical Realms: une la pantalla de inicio, el mapa de niveles y los niveles.

    inicio --Iniciar--> mapa --clic en un botón--> nivel --Volver al mapa--> mapa
       ^                  |
       +------ Esc -------+            (Esc en el inicio cierra el juego)

Archivos que necesita en la misma carpeta:
    pantalla_inicio.py   mapa_niveles.py   nivel_generico.py
    icono_opciones.svg   icono_sonido.svg  icono_sonido_off.svg
    niveles.json         (o, si no existe, usa ejemplo_niveles.json)
Opcionales: fondo_inicio.jpg, fondo_mapa.jpg, pergamino.jpg, fuente.ttf, posiciones_mapa.json

Uso:
    pip install pygame-ce pygame-gui
    python numerical_realms.py                    # usa niveles.json
    python numerical_realms.py mis_niveles.json   # otro archivo de niveles
    python numerical_realms.py --reiniciar        # borra el progreso guardado

Cómo se relacionan el JSON y el mapa:
    El nivel n del mapa es el n-ésimo elemento de "niveles" del JSON, y el nombre que
    aparece al pasar el ratón es su "titulo". Los botones del mapa que no tienen nivel
    en el JSON aparecen con candado (así puedes ir agregando niveles poco a poco).

Progreso:
    Los niveles completados y el estado del sonido se guardan en progreso.json
    (junto al script) y se recuperan al volver a abrir el juego.
"""
import json
import os
import sys

import pygame

import mapa_niveles
import nivel_generico
import pantalla_inicio

BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_PROGRESO = os.path.join(BASE, "progreso.json")

actual = None


"""  Progreso  """
def cargar_progreso(ruta, n_niveles):
    progreso = {"completados": set(), "sonido": True}
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        for n in datos.get("completados", []):
            try:
                n = int(n)
            except (ValueError, TypeError):
                continue
            if 1 <= n <= n_niveles:
                progreso["completados"].add(n)
        progreso["sonido"] = bool(datos.get("sonido", True))
    except FileNotFoundError:
        pass
    except (OSError, ValueError, TypeError, AttributeError) as e:
        print(f"No pude leer {ruta} ({e}); empiezo sin progreso.")
    return progreso

def guardar_progreso(ruta, progreso):
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"completados": sorted(progreso["completados"]),
                       "sonido": progreso["sonido"]}, f, indent=2)
    except OSError as e:
        print(f"No pude guardar el progreso en {ruta}: {e}")


"""  juego  """
def ejecutar_juego(niveles, ruta_progreso=RUTA_PROGRESO):
    global actual
    pygame.init()
    progreso = cargar_progreso(ruta_progreso, len(niveles))
    total = max(mapa_niveles.TOTAL_NIVELES, len(niveles))
    nombres = [n["titulo"] for n in niveles]
    sin_contenido = set(range(len(niveles) + 1, total + 1))
    escena, numero = "inicio", None

    while True:
        pygame.event.clear()                 # evita que un clic se "cuele" a la escena siguiente

        if escena == "inicio":
            actual = pantalla_inicio.PantallaInicio(sonido=progreso["sonido"])
            r = actual.ejecutar()
            progreso["sonido"] = actual.sonido
            if r == "iniciar":
                escena = "mapa"
            elif r == "salir":
                break
            elif r == "opciones":
                print("Abrir pantalla de opciones (pendiente de implementar)")

        elif escena == "mapa":
            actual = mapa_niveles.MapaNiveles(
                total=total, completados=progreso["completados"], bloqueados=sin_contenido,
                nombres=nombres, sonido=progreso["sonido"])
            r = actual.ejecutar()
            progreso["sonido"] = actual.sonido
            if isinstance(r, tuple):
                numero, escena = r[1], "nivel"
            elif r == "volver":
                escena = "inicio"
            elif r == "salir":
                break
            elif r == "opciones":
                print("Abrir pantalla de opciones (pendiente de implementar)")

        elif escena == "nivel":
            actual = nivel_generico.Juego([niveles[numero - 1]], modo_mapa=True,
                                          sonido=progreso["sonido"])
            r = actual.ejecutar()
            progreso["sonido"] = actual.sonido
            if r == "completado":
                progreso["completados"].add(numero)
            guardar_progreso(ruta_progreso, progreso)
            if r == "salir":
                break
            escena = "mapa"

        guardar_progreso(ruta_progreso, progreso)

    guardar_progreso(ruta_progreso, progreso)
    pygame.quit()


def main():
    args = sys.argv[1:]
    if "--reiniciar" in args:
        args.remove("--reiniciar")
        try:
            os.remove(RUTA_PROGRESO)
            print("Progreso borrado.")
        except FileNotFoundError:
            pass
    ruta = args[0] if args else os.path.join(BASE, "niveles.json")
    if not args and not os.path.exists(ruta):
        ruta = os.path.join(BASE, "ejemplo_niveles.json")
        print("No hay niveles.json; uso ejemplo_niveles.json")
    try:
        niveles = nivel_generico.cargar_niveles(ruta)
    except FileNotFoundError:
        sys.exit(f"No encuentro el archivo de niveles: {ruta}")
    except json.JSONDecodeError as e:
        sys.exit(f"JSON mal formado en {ruta}: {e}")
    except ValueError as e:
        sys.exit(f"Estructura inválida en {ruta}\n  {e}")
    ejecutar_juego(niveles)


if __name__ == "__main__":
    main()
