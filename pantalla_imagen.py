import pygame

import ventana
from pantalla_inicio import contener
from ventana import ANCHO, ALTO

ESPERA = 0.5            # segundos en que se ignoran teclas y clics al aparecer
APARECER = 0.25         # segundos del fundido de entrada (0 = sin fundido)

_cache = {}


def cargar(ruta):
    """Imagen ya ajustada a la pantalla, o None si no hay ruta o no se puede abrir."""
    if not ruta:
        return None
    if ruta not in _cache:
        try:
            img = pygame.image.load(ruta).convert()
        except (pygame.error, FileNotFoundError, OSError) as e:
            print(f"No pude abrir la imagen {ruta!r}: {e}")
            _cache[ruta] = None
        else:
            _cache[ruta] = contener(img, (ANCHO, ALTO))
    return _cache[ruta]


def _es_tecla_para_seguir(ev):
    if ev.type == pygame.KEYDOWN:
        return ev.key != pygame.K_F11
    return ev.type in (pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN, pygame.CONTROLLERBUTTONDOWN,
                       pygame.FINGERDOWN)


def mostrar(pantalla, ruta):
    """Muestra la imagen hasta que se presione algo. Devuelve "seguir" o "salir"."""
    img = cargar(ruta)
    if img is None:
        return "seguir"
    reloj = pygame.time.Clock()
    t = 0.0
    pygame.event.clear()
    while True:
        dt = reloj.tick(60) / 1000.0
        t += dt
        if ventana.sin_foco():
            return "salir"
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "salir"
            if ventana.tecla_global(ev):
                continue
            if t >= ESPERA and _es_tecla_para_seguir(ev):
                pygame.event.clear()        # que la misma tecla no llegue a la escena siguiente
                return "seguir"
        pantalla.fill((0, 0, 0))
        if APARECER and t < APARECER:
            img.set_alpha(int(255 * t / APARECER))
            pantalla.blit(img, (0, 0))
            img.set_alpha(None)
        else:
            pantalla.blit(img, (0, 0))
        pygame.display.flip()


def mostrar_varias(pantalla, rutas):
    """Muestra varias imágenes seguidas. Devuelve "salir" si alguna se cerró, si no "seguir"."""
    for r in rutas:
        if mostrar(pantalla, r) == "salir":
            return "salir"
    return "seguir"
