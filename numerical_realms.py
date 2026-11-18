import json
import os
import sys

import pygame

import constructor_niveles
import estructura as est_mod
import mapa_niveles
import ventana
import nivel_generico
import pantalla_imagen
import pantalla_inicio

BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_PROGRESO = os.path.join(BASE, "progreso.json")

actual = None   # escena en ejecución (útil para pruebas y depuración)


def ruta(nombre):
    return os.path.join(BASE, nombre)


# ----------------------------------------------------------------------- música
class Musica:
    """Música de fondo. Una escena sin música definida deja sonando la anterior, y una pista
    que ya está sonando no se reinicia."""

    def __init__(self):
        self.actual = None
        self._avisadas = set()

    def reproducir(self, ruta_audio, sonido=True):
        if not ruta_audio:
            return
        try:
            if ruta_audio != self.actual:
                pygame.mixer.music.load(ruta_audio)
                pygame.mixer.music.play(-1)
                self.actual = ruta_audio
            # al cargar una pista nueva pygame vuelve al volumen máximo: se aplica siempre
            pygame.mixer.music.set_volume(1.0 if sonido else 0.0)
        except (pygame.error, OSError) as e:
            if ruta_audio not in self._avisadas:
                self._avisadas.add(ruta_audio)
                print(f"No pude reproducir {ruta_audio}: {e}")


# ----------------------------------------------------------------------- estados
def estado_nivel(nivel, completados):
    """Estado con el que se ve un nivel: completado, bloqueado o disponible."""
    if nivel.clave in completados:
        return "completado"
    if nivel.contenido is None:               # sin contenido en el JSON de niveles: no se puede abrir
        return "bloqueado"
    return nivel.estado                       # el estado inicial de la estructura


def estado_submapa(sub, completados):
    if not sub.niveles:                       # marcador {} o submapa sin niveles
        return "bloqueado"
    if all(estado_nivel(n, completados) == "completado" for n in sub.niveles):
        return "completado"
    return sub.estado


# ---------------------------------------------------------------------- progreso
def cargar_progreso(ruta_json):
    progreso = {"completados": set(), "sonido": True}
    try:
        with open(ruta_json, encoding="utf-8") as f:
            datos = json.load(f)
        progreso["completados"] = {c for c in datos.get("completados", []) if isinstance(c, str)}
        progreso["sonido"] = bool(datos.get("sonido", True))
    except FileNotFoundError:
        pass
    except (OSError, ValueError, TypeError, AttributeError) as e:
        print(f"No pude leer {ruta_json} ({e}); empiezo sin progreso.")
    return progreso


def guardar_progreso(ruta_json, progreso):
    try:
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump({"completados": sorted(progreso["completados"]),
                       "sonido": progreso["sonido"]}, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"No pude guardar el progreso en {ruta_json}: {e}")


def guardar_posiciones_en_estructura(est, items, posiciones):
    est_mod.actualizar_posiciones(items, posiciones)
    try:
        est_mod.guardar_estructura(est)
    except OSError as e:
        print(f"No pude guardar {est.ruta}: {e}")


# ------------------------------------------------------------------------ juego
def ejecutar_juego(est, ruta_progreso=RUTA_PROGRESO):
    global actual
    pantalla = ventana.obtener_pantalla()     # una sola ventana para todo el juego
    progreso = cargar_progreso(ruta_progreso)
    musica = Musica()
    escena, ks, kn = "inicio", None, None    # ks: índice del submapa, kn: índice del nivel

    while True:
        pygame.event.clear()                 # evita que un clic se "cuele" a la escena siguiente
        comp = progreso["completados"]

        if escena == "inicio":
            musica.reproducir(pantalla_inicio.RUTA_MUSICA, progreso["sonido"])
            actual = pantalla_inicio.PantallaInicio(pantalla, sonido=progreso["sonido"])
            r = actual.ejecutar()
            progreso["sonido"] = actual.sonido
            if r == "iniciar":
                if pantalla_imagen.mostrar(pantalla, est.historia) == "salir":
                    break
                escena = "mapa"
            elif r == "salir":
                break
            elif r == "opciones":
                print("Abrir pantalla de opciones (pendiente de implementar)")

        elif escena == "mapa":
            musica.reproducir(est.musica, progreso["sonido"])
            estados = [estado_submapa(s, comp) for s in est.submapas]
            nombres = []
            for s in est.submapas:
                hechos = sum(1 for n in s.niveles if estado_nivel(n, comp) == "completado")
                nombres.append(f"{s.nombre}  ({hechos}/{len(s.niveles)})" if s.niveles else s.nombre)
            actual = mapa_niveles.MapaNiveles(
                pantalla,
                total=len(est.submapas),
                completados={i + 1 for i, e in enumerate(estados) if e == "completado"},
                bloqueados={i + 1 for i, e in enumerate(estados) if e == "bloqueado"},
                nombres=nombres, sonido=progreso["sonido"],
                titulo="Numerical Realms - Mapa general",
                ruta_fondo=[est.fondo] if est.fondo else [],
                posiciones=est_mod.posiciones_de(est.submapas),
                al_guardar=lambda pos: guardar_posiciones_en_estructura(est, est.submapas, pos))
            r = actual.ejecutar()
            progreso["sonido"] = actual.sonido
            if isinstance(r, tuple):
                ks, escena = r[1] - 1, "submapa"
            elif r == "volver":
                escena = "inicio"
            elif r == "salir":
                break
            elif r == "opciones":
                print("Abrir pantalla de opciones (pendiente de implementar)")

        elif escena == "submapa":
            sub = est.submapas[ks]
            musica.reproducir(sub.musica or est.musica, progreso["sonido"])
            estados = [estado_nivel(n, comp) for n in sub.niveles]
            fondo = sub.fondo or est.fondo
            actual = mapa_niveles.MapaNiveles(
                pantalla,
                total=len(sub.niveles),
                completados={i + 1 for i, e in enumerate(estados) if e == "completado"},
                bloqueados={i + 1 for i, e in enumerate(estados) if e == "bloqueado"},
                nombres=[n.nombre for n in sub.niveles], sonido=progreso["sonido"],
                titulo=f"Numerical Realms - {sub.nombre}",
                ruta_fondo=[fondo] if fondo else [],
                posiciones=est_mod.posiciones_de(sub.niveles), semilla=12 + ks,
                al_guardar=lambda pos, sub=sub: guardar_posiciones_en_estructura(est, sub.niveles, pos))
            r = actual.ejecutar()
            progreso["sonido"] = actual.sonido
            if isinstance(r, tuple):
                kn, escena = r[1] - 1, "nivel"
            elif r == "volver":
                escena = "mapa"
            elif r == "salir":
                break
            elif r == "opciones":
                print("Abrir pantalla de opciones (pendiente de implementar)")

        elif escena == "nivel":
            nivel = est.submapas[ks].niveles[kn]
            contenido = nivel.contenido
            if constructor_niveles.es_plantilla(contenido):
                # problema nuevo cada vez que se abre el nivel
                try:
                    contenido = constructor_niveles.generar_nivel(contenido)
                except Exception as e:
                    print(f"No pude generar el nivel {nivel.nombre!r}: {e}")
                    escena = "submapa"
                    continue
            pant = nivel.pantallas
            if pantalla_imagen.mostrar_varias(pantalla, [pant["inicio"], pant["guia"]]) == "salir":
                break
            actual = nivel_generico.Juego([contenido], modo_mapa=True, guia=pant["guia"],
                                          sonido=progreso["sonido"], pantalla=pantalla)
            r = actual.ejecutar()
            progreso["sonido"] = actual.sonido
            if r == "completado":
                progreso["completados"].add(nivel.clave)
            guardar_progreso(ruta_progreso, progreso)
            if r == "salir":
                break
            if r == "completado":
                pygame.event.clear()
                if pantalla_imagen.mostrar_varias(pantalla, [pant["final"], pant["imagen"]]) == "salir":
                    break
            escena = "submapa"

        guardar_progreso(ruta_progreso, progreso)

    guardar_progreso(ruta_progreso, progreso)
    pygame.quit()


def main():
    args = sys.argv[1:]
    if "--ventana" in args:
        args.remove("--ventana")
        ventana.PANTALLA_COMPLETA = False
    if "--sin-autocierre" in args:
        args.remove("--sin-autocierre")
        ventana.CERRAR_AL_PERDER_FOCO = False
    if "--reiniciar" in args:
        args.remove("--reiniciar")
        try:
            os.remove(RUTA_PROGRESO)
            print("Progreso borrado.")
        except FileNotFoundError:
            pass
    ruta_est = args[0] if args else ruta("estructura.json")
    ruta_niv = args[1] if len(args) > 1 else None
    # plantillas (problema nuevo cada vez) + niveles fijos opcionales
    plantillas, avisos = constructor_niveles.cargar_plantillas()
    for aviso in avisos:
        print("Aviso (plantillas):", aviso)

    fijos = []
    if ruta_niv is None:
        ruta_niv = ruta("niveles.json")
        if not os.path.exists(ruta_niv):
            ruta_niv = None if plantillas else ruta("ejemplo_niveles.json")
    if ruta_niv is not None:
        try:
            fijos = nivel_generico.cargar_niveles(ruta_niv)
        except FileNotFoundError:
            sys.exit(f"No encuentro el archivo de niveles: {ruta_niv}")
        except json.JSONDecodeError as e:
            sys.exit(f"JSON mal formado en {ruta_niv}: {e}")
        except ValueError as e:
            sys.exit(f"Niveles inválidos en {ruta_niv}\n  {e}")
    if not plantillas and not fijos:
        sys.exit("No hay niveles: agrega plantillas en la carpeta plantillas/ o un niveles.json")

    try:
        est = est_mod.cargar_estructura(ruta_est)
    except FileNotFoundError:
        sys.exit(f"No encuentro el archivo de estructura: {ruta_est}\n"
                 "Crea un estructura.json (puedes partir de ejemplo_estructura.json) o indica otro:\n"
                 "    python numerical_realms.py mi_estructura.json")
    except json.JSONDecodeError as e:
        sys.exit(f"JSON mal formado en {ruta_est}: {e}")
    except ValueError as e:
        sys.exit(f"Estructura inválida en {ruta_est}\n  {e}")

    est_mod.vincular_contenido(est, plantillas + fijos)     # gana la plantilla si se repite
    for aviso in est.avisos:
        print("Aviso:", aviso)
    ejecutar_juego(est)


if __name__ == "__main__":
    main()
