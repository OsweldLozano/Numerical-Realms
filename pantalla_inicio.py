"""
Pantalla de inicio: título central, botones Iniciar / Salir y dos íconos
superiores (opciones y sonido).

Archivos que busca junto a este script (todos reemplazables):
    fondo_inicio.jpg        fondo (se escala para cubrir la ventana sin deformarse)
    icono_opciones.svg      ícono de opciones (esquina superior izquierda)
    icono_sonido.svg        ícono de sonido activo (esquina superior derecha)
    icono_sonido_off.svg    ícono de sonido silenciado
    fuente.ttf              (opcional) tipografía del título

Si falta el JPG se dibuja un degradado; si falla un SVG se dibuja un ícono simple.

Uso:
    pip install pygame-ce pygame-gui
    python pantalla_inicio.py

Para integrarla en tu juego:
    inicio = PantallaInicio()
    while True:
        accion = inicio.ejecutar()      # "iniciar" | "salir" | "opciones"
        if accion == "opciones":
            ...abrir tu pantalla de opciones...
            continue
        break
    # inicio.sonido guarda si el sonido está activo (True/False)
"""
import io
import json
import math
import os
from pathlib import Path

import pygame
import pygame_gui
from pygame_gui.elements import UIButton

"""  configuración  """

BASE = os.path.dirname(os.path.abspath(__file__))
def ruta(nombre):
    return os.path.join(BASE, nombre)

ANCHO, ALTO = 1024, 720
TITULO = "Numerical Realms"
RUTA_FONDO = ruta(Path(__file__).parent / "assets" /"fondos" / "inicio.jpg")
RUTA_SVG_OPCIONES = ruta(Path(__file__).parent / "assets" /"iconos" / "opciones.svg")
RUTA_SVG_SONIDO = ruta(Path(__file__).parent / "assets" /"iconos" / "sonido.svg")
RUTA_SVG_SILENCIO = ruta(Path(__file__).parent / "assets" /"iconos" / "sonido_off.svg")
RUTA_FUENTE = ruta(Path(__file__).parent / "assets" /"tipografia" / "JacquesFrancois.ttf")

TAM_ICONO = 60           # lado en píxeles de los íconos SVG
MARGEN = 18              # separación de los íconos con los bordes
TAM_TITULO = 96
GROSOR_CONTORNO = 3
OSCURECER = 0            # 0-255: velo negro sobre el fondo (sube si el título no se lee)
BOTON_W, BOTON_H, BOTON_SEP = 190, 60, 16

BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)

THEME = {
    "button": {
        "colours": {
            "normal_bg": "#E8DEF8", "hovered_bg": "#D9CCF2", "active_bg": "#C7B6EA",
            "normal_text": "#49454F", "hovered_text": "#2B2833", "active_text": "#2B2833",
            "normal_border": "#E8DEF8", "hovered_border": "#D9CCF2", "active_border": "#C7B6EA",
        },
        "font": {"name": "noto_sans", "size": "22"},
        "misc": {"shape": "rounded_rectangle", "shape_corner_radius": "14", "border_width": "0"},
    }
}


"""  recursos  """
def cargar_svg(ruta_svg, tam):
    """Carga un SVG a `tam` x `tam`. Devuelve None si no se puede."""
    try:
        return pygame.image.load_sized_svg(ruta_svg, (tam, tam)).convert_alpha()
    except Exception:
        pass
    try:   # versiones sin load_sized_svg: carga normal y reescala
        img = pygame.image.load(ruta_svg).convert_alpha()
        return pygame.transform.smoothscale(img, (tam, tam))
    except Exception:
        return None


def icono_respaldo(tipo, tam):
    """Ícono dibujado a mano por si el SVG no existe o no carga."""
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    c = tam // 2
    if tipo == "opciones":
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(s, BLANCO, (c + tam * .25 * math.cos(a), c + tam * .25 * math.sin(a)),
                             (c + tam * .45 * math.cos(a), c + tam * .45 * math.sin(a)), max(3, tam // 8))
        pygame.draw.circle(s, BLANCO, (c, c), int(tam * .3), max(3, tam // 6))
    else:
        pygame.draw.polygon(s, BLANCO, [(tam * .08, tam * .38), (tam * .28, tam * .38), (tam * .5, tam * .16),
                                        (tam * .5, tam * .84), (tam * .28, tam * .62), (tam * .08, tam * .62)])
        if tipo == "sonido":
            for r in (.2, .36):
                pygame.draw.arc(s, BLANCO, (c + tam * .06 - tam * r, c - tam * r, tam * 2 * r, tam * 2 * r),
                                -0.9, 0.9, max(3, tam // 12))
        else:
            pygame.draw.line(s, BLANCO, (tam * .65, tam * .38), (tam * .92, tam * .62), max(3, tam // 12))
            pygame.draw.line(s, BLANCO, (tam * .92, tam * .38), (tam * .65, tam * .62), max(3, tam // 12))
    return s


def cubrir(img, tam):
    """Escala `img` para cubrir `tam` sin deformarla (recorta lo que sobre)."""
    iw, ih = img.get_size()
    esc = max(tam[0] / iw, tam[1] / ih)
    nuevo = pygame.transform.smoothscale(img, (math.ceil(iw * esc), math.ceil(ih * esc)))
    surf = pygame.Surface(tam)
    surf.blit(nuevo, nuevo.get_rect(center=(tam[0] // 2, tam[1] // 2)))
    return surf


def fondo_respaldo(tam):
    w, h = tam
    surf = pygame.Surface(tam)
    for y in range(h):
        t = y / h
        col = (int(70 + 40 * t), int(120 + 60 * t), int(170 - 80 * t))
        pygame.draw.line(surf, col, (0, y), (w, y))
    return surf


def cargar_fondo(tam):
    if os.path.exists(RUTA_FONDO):
        try:
            fondo = cubrir(pygame.image.load(RUTA_FONDO).convert(), tam)
        except pygame.error as e:
            print(f"No pude leer {RUTA_FONDO}: {e}")
            fondo = fondo_respaldo(tam)
    else:
        fondo = fondo_respaldo(tam)
    if OSCURECER:
        velo = pygame.Surface(tam, pygame.SRCALPHA)
        velo.fill((0, 0, 0, OSCURECER))
        fondo.blit(velo, (0, 0))
    return fondo


def cargar_fuente(tam):
    if os.path.exists(RUTA_FUENTE):
        try:
            return pygame.font.Font(RUTA_FUENTE, tam)
        except Exception:
            pass
    return pygame.font.SysFont("arial", tam)


def texto_con_contorno(fuente, texto, color, color_borde, g):
    base = fuente.render(texto, True, color_borde)
    w, h = base.get_size()
    surf = pygame.Surface((w + 2 * g, h + 2 * g), pygame.SRCALPHA)
    for dx in range(-g, g + 1):
        for dy in range(-g, g + 1):
            if dx * dx + dy * dy <= g * g + 1:
                surf.blit(base, (g + dx, g + dy))
    surf.blit(fuente.render(texto, True, color), (g, g))
    return surf


def crear_titulo(texto, tam, ancho_max):
    fuente = cargar_fuente(tam)
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if fuente.size(prueba)[0] <= ancho_max or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    imgs = [texto_con_contorno(fuente, l, BLANCO, NEGRO, GROSOR_CONTORNO) for l in lineas]
    paso = fuente.get_linesize() - 6
    w = max(i.get_width() for i in imgs)
    surf = pygame.Surface((w, paso * (len(imgs) - 1) + imgs[-1].get_height()), pygame.SRCALPHA)
    for k, img in enumerate(imgs):
        surf.blit(img, ((w - img.get_width()) // 2, k * paso))
    return surf


# ---------------------------------------------------------------- botón de ícono
class BotonIcono:
    def __init__(self, rect, imagen):
        self.rect = rect
        self.imagen = imagen

    def dibujar(self, pantalla, pos_raton):
        if self.rect.collidepoint(pos_raton):          # resaltado al pasar el ratón
            halo = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 255, 255, 55), halo.get_rect().center, self.rect.width // 2)
            pantalla.blit(halo, self.rect)
        pantalla.blit(self.imagen, self.imagen.get_rect(center=self.rect.center))


# ---------------------------------------------------------------- pantalla
class PantallaInicio:
    def __init__(self, pantalla=None, sonido=True):
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.pantalla = pantalla or pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        w, h = self.pantalla.get_size()
        self.sonido = sonido

        self.fondo = cargar_fondo((w, h))
        self.titulo = crear_titulo(TITULO, TAM_TITULO, int(w * 0.55))
        self.rect_titulo = self.titulo.get_rect(center=(w // 2, int(h * 0.33)))

        self.img_opciones = cargar_svg(RUTA_SVG_OPCIONES, TAM_ICONO) or icono_respaldo("opciones", TAM_ICONO)
        self.img_sonido = cargar_svg(RUTA_SVG_SONIDO, TAM_ICONO) or icono_respaldo("sonido", TAM_ICONO)
        self.img_silencio = cargar_svg(RUTA_SVG_SILENCIO, TAM_ICONO) or icono_respaldo("silencio", TAM_ICONO)
        lado = TAM_ICONO + 8
        self.btn_opciones = BotonIcono(pygame.Rect(MARGEN, MARGEN, lado, lado), self.img_opciones)
        self.btn_sonido = BotonIcono(pygame.Rect(w - MARGEN - lado, MARGEN, lado, lado), self.img_sonido)

        self.manager = pygame_gui.UIManager((w, h), theme_path=io.StringIO(json.dumps(THEME)))
        x = (w - BOTON_W) // 2
        y = int(h * 0.505)
        self.btn_iniciar = UIButton(pygame.Rect(x, y, BOTON_W, BOTON_H), "Iniciar", self.manager)
        self.btn_salir = UIButton(pygame.Rect(x, y + BOTON_H + BOTON_SEP, BOTON_W, BOTON_H),
                                  "Salir", self.manager)
        self.aplicar_sonido()

    def aplicar_sonido(self):
        self.btn_sonido.imagen = self.img_sonido if self.sonido else self.img_silencio
        try:   # conecta aquí tu música: pygame.mixer.music.set_volume(...)
            pygame.mixer.music.set_volume(1.0 if self.sonido else 0.0)
        except pygame.error:
            pass

    def procesar(self, ev):
        """Devuelve "iniciar", "salir", "opciones" o None."""
        if ev.type == pygame.QUIT:
            return "salir"
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return "iniciar"
            if ev.key == pygame.K_ESCAPE:
                return "salir"
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.btn_sonido.rect.collidepoint(ev.pos):
                self.sonido = not self.sonido
                self.aplicar_sonido()
            elif self.btn_opciones.rect.collidepoint(ev.pos):
                return "opciones"
        if ev.type == pygame_gui.UI_BUTTON_PRESSED:
            if ev.ui_element is self.btn_iniciar:
                return "iniciar"
            if ev.ui_element is self.btn_salir:
                return "salir"
        self.manager.process_events(ev)
        return None

    def cuadro(self, dt):
        self.manager.update(dt)
        self.pantalla.blit(self.fondo, (0, 0))
        self.pantalla.blit(self.titulo, self.rect_titulo)
        raton = pygame.mouse.get_pos()
        self.btn_opciones.dibujar(self.pantalla, raton)
        self.btn_sonido.dibujar(self.pantalla, raton)
        self.manager.draw_ui(self.pantalla)
        pygame.display.flip()

    def ejecutar(self):
        while True:
            dt = self.reloj.tick(60) / 1000.0
            for ev in pygame.event.get():
                accion = self.procesar(ev)
                if accion:
                    return accion
            self.cuadro(dt)


if __name__ == "__main__":
    inicio = PantallaInicio()
    while True:
        accion = inicio.ejecutar()
        if accion == "opciones":
            print("Abrir pantalla de opciones (pendiente de implementar)")
            continue
        break
    print("Acción elegida:", accion)
    pygame.quit()
