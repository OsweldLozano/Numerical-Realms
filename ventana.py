import os

# Suavizado al escalar (sin esto pygame escala "pixelado", que se ve mal en factores
# como 1600 -> 1920). Debe definirse antes de crear la ventana.
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "linear")

import pygame  # noqa: E402

ANCHO, ALTO = 1600, 900          # resolución lógica (la de los fondos)
PANTALLA_COMPLETA = True         # numerical_realms.py --ventana lo pone en False
CERRAR_AL_PERDER_FOCO = True     # numerical_realms.py --sin-autocierre lo pone en False
GRACIA_MS = 1500                 # tiempo sin revisar el foco tras crear la ventana o pulsar F11

_ignorar_hasta = 0               # pygame.time.get_ticks() hasta el que no se revisa el foco
_tuvo_foco = False               # la ventana ya estuvo en primer plano al menos una vez


def _dar_gracia():
    global _ignorar_hasta
    _ignorar_hasta = pygame.time.get_ticks() + GRACIA_MS


def obtener_pantalla(titulo=None):
    """Devuelve la superficie de dibujo del juego. Solo se crea una vez: las escenas
    la comparten, así la ventana nunca cambia de tamaño al pasar de una a otra."""
    pygame.init()
    pantalla = pygame.display.get_surface()
    if pantalla is None or pantalla.get_size() != (ANCHO, ALTO):
        banderas = pygame.SCALED
        if PANTALLA_COMPLETA:
            banderas |= pygame.FULLSCREEN
        pantalla = pygame.display.set_mode((ANCHO, ALTO), banderas)
        _dar_gracia()
    if titulo:
        pygame.display.set_caption(titulo)
    return pantalla


def tecla_global(ev):
    """Atajos que valen en todas las escenas. Devuelve True si el evento ya se usó."""
    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
        _dar_gracia()
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error as e:              # algunos sistemas no permiten cambiar de modo
            print(f"No pude cambiar el modo de pantalla: {e}")
        return True
    return False


def sin_foco():
    """True si el juego quedó en segundo plano (otra ventana al frente o minimizado) y por
    eso hay que cerrarlo. Llamar una vez por cuadro."""
    global _tuvo_foco
    if not CERRAR_AL_PERDER_FOCO:
        return False
    enfocada = pygame.key.get_focused() and pygame.display.get_active()
    if enfocada:
        _tuvo_foco = True
        return False
    if not _tuvo_foco or pygame.time.get_ticks() < _ignorar_hasta:
        return False
    print("El juego pasó a segundo plano: se cierra.")
    return True
