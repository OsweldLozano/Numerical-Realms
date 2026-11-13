"""
Mapa de niveles: 34 botones circulares dispersos por la pantalla, fondo JPG y
los botones de opciones y sonido (íconos SVG) de la pantalla de inicio.
Cada nivel es independiente: no hay orden, ni líneas que los unan, ni números.

Requiere pantalla_inicio.py en la misma carpeta (reutiliza sus íconos y utilidades).

Archivos que busca junto a este script:
    fondo_mapa.jpg          fondo (se escala para cubrir la ventana sin deformarse)
    posiciones_mapa.json    (opcional) posiciones de los botones, la crea el modo edición
    icono_opciones.svg, icono_sonido.svg, icono_sonido_off.svg   (los mismos del inicio)

Estados de cada botón (todos son "disponible" salvo que tú indiques otra cosa):
    disponible  lavanda, sin marca
    completado  verde con una palomita
    bloqueado   gris con un candado, no responde al clic (opcional)

Como los botones no llevan número, al pasar el ratón aparece una etiqueta con el
nombre del nivel (usa `nombres=[...]`; si no, "Nivel n").

Teclas:
    Esc  -> "volver" (por ejemplo, al menú de inicio)
    F2   -> modo edición: arrastra los botones sobre tu fondo (en este modo SÍ se
            muestra el número de cada uno, para que sepas cuál es cuál) y pulsa S
            para guardar las posiciones en posiciones_mapa.json.

Uso:
    python mapa_niveles.py

Integración:
    mapa = MapaNiveles(total=34, nombres=[...], completados={3, 7}, bloqueados={20})
    r = mapa.ejecutar()      # ("nivel", n) | "opciones" | "volver" | "salir"
    ...jugar el nivel n...
    mapa.completar(n)        # lo marca como completado (no desbloquea ningún otro)
    mapa.desbloquear(k)      # si algún nivel debe abrirse por otra condición
"""
import json
import math
import os
import random

import pygame

from pantalla_inicio import (
    ANCHO, ALTO, MARGEN, TAM_ICONO, BotonIcono, cargar_svg, cubrir, fondo_respaldo,
    icono_respaldo, ruta, RUTA_SVG_OPCIONES, RUTA_SVG_SONIDO, RUTA_SVG_SILENCIO,
)

# ----------------------------------------------------------------- configuración
TOTAL_NIVELES = 34
DIAMETRO = 62                    # diámetro de cada botón circular
RUTA_FONDO = ruta("fondo_mapa.jpg")
RUTA_POSICIONES = ruta("posiciones_mapa.json")
OSCURECER = 0                    # 0-255: velo negro sobre el fondo

ESTILOS = {   # (relleno, borde)
    "bloqueado": ((122, 124, 138), (72, 74, 88)),
    "disponible": ((232, 222, 248), (112, 82, 168)),
    "completado": ((92, 190, 120), (30, 105, 60)),
}


# ------------------------------------------------------------------ posiciones
def posiciones_por_defecto(total, semilla=11):
    """Reparto libre y parejo (algoritmo del "mejor candidato": cada botón nuevo se coloca
    en el punto más alejado de los ya puestos). Devuelve [[x, y], ...] en fracciones (0 a 1).
    Es determinista: siempre sale la misma distribución."""
    rng = random.Random(semilla)
    r = DIAMETRO // 2 + 14
    pts = []
    for _ in range(total):
        mejor, mejor_d = None, -1.0
        for _ in range(60):
            x, y = rng.uniform(r, ANCHO - r), rng.uniform(55, ALTO - r)
            if y < 125 and (x < 135 or x > ANCHO - 135):      # no tapar los íconos de las esquinas
                continue
            d = min((math.hypot(x - qx, y - qy) for qx, qy in pts), default=1e9)
            if d > mejor_d:
                mejor, mejor_d = (x, y), d
        pts.append(mejor)
    return [[x / ANCHO, y / ALTO] for x, y in pts]


def cargar_posiciones(total, ruta_pos=None, semilla=11):
    ruta_pos = ruta_pos or RUTA_POSICIONES
    pos = posiciones_por_defecto(total, semilla)
    if os.path.exists(ruta_pos):
        try:
            with open(ruta_pos, encoding="utf-8") as f:
                datos = json.load(f)["posiciones"]
            for i, p in enumerate(datos[:total]):
                pos[i] = [float(p[0]), float(p[1])]
        except (OSError, ValueError, KeyError, TypeError, IndexError) as e:
            print(f"No pude leer {ruta_pos} ({e}); uso las posiciones por defecto.")
    return pos


# --------------------------------------------------------------------- dibujo
def crear_circulo(d, relleno, borde, grosor=4):
    """Círculo suavizado (dibujado a 4x y reducido) con borde y sombra."""
    ss, total = 4, d + 12
    big = pygame.Surface((total * ss, total * ss), pygame.SRCALPHA)
    c, r = total * ss // 2, d * ss // 2
    pygame.draw.circle(big, (0, 0, 0, 90), (c, c + 3 * ss), r)
    pygame.draw.circle(big, borde, (c, c), r)
    pygame.draw.circle(big, relleno, (c, c), r - grosor * ss)
    return pygame.transform.smoothscale(big, (total, total))


def aclarar(color, n=18):
    return tuple(min(255, v + n) for v in color)


def dibujar_palomita(s, cx, cy):
    pygame.draw.lines(s, (255, 255, 255), False,
                      [(cx - 12, cy + 1), (cx - 4, cy + 9), (cx + 13, cy - 9)], 6)


def dibujar_candado(s, cx, cy):
    pygame.draw.arc(s, (210, 210, 220), (cx - 8, cy - 17, 16, 20), 0, math.pi, 3)
    pygame.draw.line(s, (210, 210, 220), (cx - 8, cy - 7), (cx - 8, cy - 1), 3)
    pygame.draw.line(s, (210, 210, 220), (cx + 7, cy - 7), (cx + 7, cy - 1), 3)
    pygame.draw.rect(s, (210, 210, 220), (cx - 12, cy - 2, 24, 18), border_radius=4)
    pygame.draw.circle(s, (72, 74, 88), (cx, cy + 6), 3)


def cargar_fondo(tam, rutas=None):
    """`rutas`: una ruta o una lista de alternativas; se usa la primera que exista y se pueda leer."""
    if rutas is None:
        rutas = [RUTA_FONDO]
    elif isinstance(rutas, str):
        rutas = [rutas]
    fondo = None
    for r in rutas:
        if os.path.exists(r):
            try:
                fondo = cubrir(pygame.image.load(r).convert(), tam)
                break
            except pygame.error as e:
                print(f"No pude leer {r}: {e}")
    if fondo is None:
        fondo = fondo_respaldo(tam)
    if OSCURECER:
        velo = pygame.Surface(tam, pygame.SRCALPHA)
        velo.fill((0, 0, 0, OSCURECER))
        fondo.blit(velo, (0, 0))
    return fondo


# ---------------------------------------------------------------------- mapa
class MapaNiveles:
    def __init__(self, pantalla=None, total=TOTAL_NIVELES, completados=(), bloqueados=(),
                 nombres=None, sonido=True, titulo="Mapa de niveles",
                 ruta_fondo=None, ruta_posiciones=None, semilla=11):
        """total: cuántos botones hay. completados / bloqueados: números de botón (1..total).
        ruta_fondo: ruta o lista de alternativas para el JPG.
        ruta_posiciones: JSON donde se guardan las posiciones (modo edición).
        semilla: cambia el reparto por defecto de los botones."""
        pygame.init()
        pygame.display.set_caption(titulo)
        self.pantalla = pantalla or pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.w, self.h = self.pantalla.get_size()
        self.total = total
        self.completados = set(completados)
        self.bloqueados = set(bloqueados)
        self.nombres = nombres or []
        self.sonido = sonido

        self.ruta_posiciones = ruta_posiciones or RUTA_POSICIONES
        self.fondo = cargar_fondo((self.w, self.h), ruta_fondo)
        self.pos = cargar_posiciones(total, self.ruta_posiciones, semilla)

        self.img_opciones = cargar_svg(RUTA_SVG_OPCIONES, TAM_ICONO) or icono_respaldo("opciones", TAM_ICONO)
        self.img_sonido = cargar_svg(RUTA_SVG_SONIDO, TAM_ICONO) or icono_respaldo("sonido", TAM_ICONO)
        self.img_silencio = cargar_svg(RUTA_SVG_SILENCIO, TAM_ICONO) or icono_respaldo("silencio", TAM_ICONO)
        lado = TAM_ICONO + 8
        self.btn_opciones = BotonIcono(pygame.Rect(MARGEN, MARGEN, lado, lado), self.img_opciones)
        self.btn_sonido = BotonIcono(pygame.Rect(self.w - MARGEN - lado, MARGEN, lado, lado), self.img_sonido)

        self.circulos = {}
        for estado, (rel, bor) in ESTILOS.items():
            self.circulos[(estado, False)] = crear_circulo(DIAMETRO, rel, bor)
            self.circulos[(estado, True)] = crear_circulo(DIAMETRO, aclarar(rel), bor)
        self.f_num = pygame.font.SysFont("arial", 24, bold=True)    # solo en modo edición
        self.f_tip = pygame.font.SysFont("arial", 18)

        self.editando = False
        self.arrastrando = None
        self.aplicar_sonido()

    # --------------------------------------------------------------- progreso
    def estado(self, n):
        if n in self.completados:
            return "completado"
        return "bloqueado" if n in self.bloqueados else "disponible"

    def completar(self, n):
        self.completados.add(n)

    def bloquear(self, n):
        self.bloqueados.add(n)

    def desbloquear(self, n):
        self.bloqueados.discard(n)

    def aplicar_sonido(self):
        self.btn_sonido.imagen = self.img_sonido if self.sonido else self.img_silencio
        try:   # conecta aquí tu música: pygame.mixer.music.set_volume(...)
            pygame.mixer.music.set_volume(1.0 if self.sonido else 0.0)
        except pygame.error:
            pass

    # -------------------------------------------------------------- geometría
    def centro(self, i):
        return int(self.pos[i][0] * self.w), int(self.pos[i][1] * self.h)

    def nivel_en(self, punto):
        """Número de nivel (1..total) bajo `punto`, o None."""
        for i in range(self.total - 1, -1, -1):
            cx, cy = self.centro(i)
            if math.hypot(punto[0] - cx, punto[1] - cy) <= DIAMETRO / 2:
                return i + 1
        return None

    def guardar_posiciones(self):
        with open(self.ruta_posiciones, "w", encoding="utf-8") as f:
            json.dump({"posiciones": [[round(x, 4), round(y, 4)] for x, y in self.pos]}, f, indent=2)
        print("Posiciones guardadas en", self.ruta_posiciones)

    # ----------------------------------------------------------------- eventos
    def procesar(self, ev):
        """Devuelve ("nivel", n), "opciones", "volver", "salir" o None."""
        if ev.type == pygame.QUIT:
            return "salir"
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                return "volver"
            if ev.key == pygame.K_F2:
                self.editando = not self.editando
                self.arrastrando = None
            elif ev.key == pygame.K_s and self.editando:
                self.guardar_posiciones()
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.btn_sonido.rect.collidepoint(ev.pos):
                self.sonido = not self.sonido
                self.aplicar_sonido()
            elif self.btn_opciones.rect.collidepoint(ev.pos):
                return "opciones"
            else:
                n = self.nivel_en(ev.pos)
                if n is not None:
                    if self.editando:
                        self.arrastrando = n - 1
                    elif self.estado(n) != "bloqueado":
                        return ("nivel", n)
        elif ev.type == pygame.MOUSEMOTION and self.arrastrando is not None:
            m = DIAMETRO // 2 + 4
            x = min(max(ev.pos[0], m), self.w - m)
            y = min(max(ev.pos[1], m), self.h - m)
            self.pos[self.arrastrando] = [x / self.w, y / self.h]
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.arrastrando = None
        return None

    # ------------------------------------------------------------------ dibujo
    def cuadro(self, dt):
        s = self.pantalla
        s.blit(self.fondo, (0, 0))
        raton = pygame.mouse.get_pos()
        sobre = None if self.arrastrando is not None else self.nivel_en(raton)

        for i in range(self.total):
            n = i + 1
            cx, cy = self.centro(i)
            estado = self.estado(n)
            img = self.circulos[(estado, n == sobre and (estado != "bloqueado" or self.editando))]
            s.blit(img, img.get_rect(center=(cx, cy)))
            if self.editando:
                txt = self.f_num.render(str(n), True, (50, 40, 70))
                s.blit(txt, txt.get_rect(center=(cx, cy)))
                pygame.draw.circle(s, (255, 90, 90), (cx, cy), DIAMETRO // 2 + 3, 2)
            elif estado == "completado":
                dibujar_palomita(s, cx, cy)
            elif estado == "bloqueado":
                dibujar_candado(s, cx, cy)

        self.btn_opciones.dibujar(s, raton)
        self.btn_sonido.dibujar(s, raton)

        if sobre is not None and not self.editando:
            self.dibujar_tooltip(sobre)
        if self.editando:
            self.dibujar_banner()
        pygame.display.flip()

    def dibujar_tooltip(self, n):
        nombre = self.nombres[n - 1] if n - 1 < len(self.nombres) else f"Nivel {n}"
        if self.estado(n) == "bloqueado":
            nombre += " (bloqueado)"
        img = self.f_tip.render(nombre, True, (255, 255, 255))
        caja = img.get_rect().inflate(20, 12)
        cx, cy = self.centro(n - 1)
        caja.midbottom = (cx, cy - DIAMETRO // 2 - 10)
        caja.clamp_ip(self.pantalla.get_rect().inflate(-8, -8))
        pygame.draw.rect(self.pantalla, (30, 28, 40), caja, border_radius=8)
        self.pantalla.blit(img, img.get_rect(center=caja.center))

    def dibujar_banner(self):
        img = self.f_tip.render("MODO EDICIÓN  -  arrastra los botones   |   S: guardar   |   F2: salir",
                                True, (255, 255, 255))
        caja = img.get_rect().inflate(28, 14)
        caja.midtop = (self.w // 2, 10)
        pygame.draw.rect(self.pantalla, (170, 40, 40), caja, border_radius=10)
        self.pantalla.blit(img, img.get_rect(center=caja.center))

    def ejecutar(self):
        while True:
            dt = self.reloj.tick(60) / 1000.0
            for ev in pygame.event.get():
                accion = self.procesar(ev)
                if accion:
                    return accion
            self.cuadro(dt)


if __name__ == "__main__":
    # Demo: algunos niveles completados y tres bloqueados, para ver los tres estados.
    mapa = MapaNiveles(completados={2, 5, 9, 14, 21}, bloqueados={30, 31, 32})
    while True:
        r = mapa.ejecutar()
        if r == "opciones":
            print("Abrir pantalla de opciones (pendiente de implementar)")
            continue
        if isinstance(r, tuple):
            print("Abrir nivel", r[1])
            mapa.completar(r[1])      # solo para la demo
            continue
        break
    pygame.quit()
