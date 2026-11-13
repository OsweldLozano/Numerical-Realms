"""
Nivel genérico de métodos numéricos (lee los niveles desde un JSON).

Uso:
    pip install pygame-ce pygame-gui
    python nivel_generico.py                      # busca niveles.json junto al script
    python nivel_generico.py mis_niveles.json     # o indica el archivo

Estructura del JSON (resumen; el detalle está en la respuesta del chat):

{
  "niveles": [
    {
      "titulo": "Interpolación Lineal",          # obligatorio (texto de la píldora)
      "instruccion": "Calcule g(2) ...",         # obligatorio (panel izquierdo)
      "tiempo": 600,                             # opcional, segundos (def. 600)
      "intro": ["g(x) = ...", "Datos: ..."],     # opcional, líneas arriba del pergamino
      "pasos": [                                 # obligatorio, al menos uno
        {
          "titulo": "Paso 1. ...",
          "filas": [
            ["g(x) =", {"in": 2}, "+"],          # texto fijo + casilla
            [{"matriz": [[2, {"in": 1}], [3, 4]]}]
          ]
        }
      ]
    }
  ]
}
Token de una fila:
    "texto" o número        -> etiqueta fija
    {"in": 2.5}             -> casilla con respuesta 2.5  (opcional: "tol", "ancho", "limite")
    {"matriz": [[...],...]} -> matriz; cada celda es texto/número fijo o {"in": ...}
También se acepta un solo nivel (objeto) o una lista de niveles sin la clave "niveles".
"""
import io
import json
import math
import os
import sys

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine, UIScrollingContainer

# ----------------------------------------------------------------- constantes
ANCHO, ALTO = 860, 626
TIEMPO_DEFECTO = 10 * 60

GRIS = (200, 200, 200)
OSCURO = (43, 43, 43)
VERDE = (0, 153, 76)
CAFE = (98, 75, 58)
NARANJA = (200, 133, 90)
BLANCO = (255, 255, 255)
ROJO = (255, 120, 110)
AMARILLO = (255, 226, 120)

PERGAMINO = pygame.Rect(283, 125, 540, 473)
AREA_W = PERGAMINO.width - 20
ENT_W = 48                       # ancho por defecto de una casilla
ALTO_FILA = 38
BOTON_X = AREA_W - 100
MAX_X = BOTON_X - 8              # las filas no pasan de aquí (se parten en varias líneas)
CORCHETE_W = 14

FUENTE_TEMA = {"name": "noto_sans", "size": "16"}
THEME = {
    "label": {
        "colours": {"normal_text": "#2b1d0e"},
        "font": FUENTE_TEMA,
        "misc": {"text_horiz_alignment": "left"},
    },
    "#centrado": {"misc": {"text_horiz_alignment": "center"}},
    "text_entry_line": {
        "colours": {
            "dark_bg": "#fffdf0", "normal_bg": "#fffdf0", "normal_text": "#2b1d0e",
            "selected_bg": "#c58a4a", "selected_text": "#ffffff", "text_cursor": "#2b1d0e",
            "disabled_dark_bg": "#bfe8c4", "disabled_text": "#12351a",
        },
        "font": FUENTE_TEMA,
    },
    "#ok_entry": {"colours": {
        "dark_bg": "#bfe8c4", "normal_bg": "#bfe8c4", "normal_text": "#12351a",
        "disabled_dark_bg": "#bfe8c4", "disabled_text": "#12351a",
        "selected_bg": "#c58a4a", "selected_text": "#ffffff", "text_cursor": "#12351a"}},
    "#wrong_entry": {"colours": {
        "dark_bg": "#f6b9b0", "normal_bg": "#f6b9b0", "normal_text": "#5a1209",
        "disabled_dark_bg": "#f6b9b0", "disabled_text": "#5a1209",
        "selected_bg": "#c58a4a", "selected_text": "#ffffff", "text_cursor": "#5a1209"}},
    "button": {
        "colours": {
            "normal_bg": "#c9895a", "hovered_bg": "#d99a6a", "active_bg": "#a8693f",
            "disabled_bg": "#9a8f7a", "normal_text": "#ffffff", "hovered_text": "#ffffff",
            "active_text": "#ffffff", "disabled_text": "#e6e6e6",
            "normal_border": "#6b3f1d", "hovered_border": "#6b3f1d",
        },
        "font": FUENTE_TEMA,
    },
}


# ------------------------------------------------------- carga y validación JSON
def _err(ruta, msg):
    raise ValueError(f"{ruta}: {msg}")


def _es_numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _es_fijo(v):
    return isinstance(v, str) or _es_numero(v)


def _validar_casilla(d, ruta):
    if "in" not in d:
        _err(ruta, 'la casilla necesita la clave "in" con la respuesta correcta')
    if not _es_fijo(d["in"]):
        _err(ruta, '"in" debe ser un número o un texto')
    if "tol" in d and not (_es_numero(d["tol"]) and d["tol"] >= 0):
        _err(ruta, '"tol" debe ser un número >= 0')
    for k in ("ancho", "limite"):
        if k in d and not (isinstance(d[k], int) and not isinstance(d[k], bool) and d[k] > 0):
            _err(ruta, f'"{k}" debe ser un entero > 0')


def _validar_token(t, ruta):
    """Valida un token y devuelve cuántas casillas contiene."""
    if _es_fijo(t):
        return 0
    if not isinstance(t, dict):
        _err(ruta, 'un token debe ser texto, número, {"in": ...} o {"matriz": ...}')
    if "matriz" in t:
        m = t["matriz"]
        if not (isinstance(m, list) and m and all(isinstance(f, list) and f for f in m)):
            _err(ruta, '"matriz" debe ser una lista no vacía de listas no vacías')
        if len({len(f) for f in m}) != 1:
            _err(ruta, "todas las filas de la matriz deben tener la misma cantidad de celdas")
        n = 0
        for i, fila in enumerate(m):
            for j, c in enumerate(fila):
                r = f'{ruta}.matriz[{i}][{j}]'
                if isinstance(c, dict):
                    _validar_casilla(c, r)
                    n += 1
                elif not _es_fijo(c):
                    _err(r, "una celda debe ser texto, número o {\"in\": ...}")
        return n
    if "in" not in t:
        _err(ruta, 'un objeto debe tener la clave "in" (casilla) o "matriz"')
    _validar_casilla(t, ruta)
    return 1


def validar_nivel(n, ruta):
    if not isinstance(n, dict):
        _err(ruta, "cada nivel debe ser un objeto { ... }")
    for k in ("titulo", "instruccion"):
        if not isinstance(n.get(k), str) or not n[k].strip():
            _err(ruta, f'falta "{k}" (texto)')
    if "tiempo" in n and not (_es_numero(n["tiempo"]) and n["tiempo"] > 0):
        _err(ruta, '"tiempo" debe ser un número > 0 (segundos)')
    if "intro" in n and not (isinstance(n["intro"], list) and all(isinstance(s, str) for s in n["intro"])):
        _err(ruta, '"intro" debe ser una lista de textos')
    pasos = n.get("pasos")
    if not (isinstance(pasos, list) and pasos):
        _err(ruta, '"pasos" debe ser una lista con al menos un paso')
    for i, p in enumerate(pasos):
        rp = f"{ruta}.pasos[{i}]"
        if not isinstance(p, dict):
            _err(rp, "cada paso debe ser un objeto { ... }")
        if not isinstance(p.get("titulo"), str):
            _err(rp, 'falta "titulo" (texto)')
        filas = p.get("filas")
        if not (isinstance(filas, list) and filas):
            _err(rp, '"filas" debe ser una lista con al menos una fila')
        total = 0
        for j, fila in enumerate(filas):
            if not (isinstance(fila, list) and fila):
                _err(f"{rp}.filas[{j}]", "cada fila debe ser una lista de tokens no vacía")
            for k, t in enumerate(fila):
                total += _validar_token(t, f"{rp}.filas[{j}][{k}]")
        if total == 0:
            _err(rp, 'el paso no tiene ninguna casilla {"in": ...} para rellenar')


def cargar_niveles(ruta):
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    if isinstance(datos, dict) and "niveles" in datos:
        niveles = datos["niveles"]
    elif isinstance(datos, list):
        niveles = datos
    elif isinstance(datos, dict):
        niveles = [datos]
    else:
        raise ValueError("el JSON debe ser un objeto o una lista de niveles")
    if not (isinstance(niveles, list) and niveles):
        raise ValueError('"niveles" debe ser una lista con al menos un nivel')
    for i, n in enumerate(niveles):
        validar_nivel(n, f"niveles[{i}]")
    return niveles


# ---------------------------------------------------------------- utilidades
def a_numero(texto):
    t = texto.strip().replace(",", ".")
    try:
        if "/" in t:
            a, b = t.split("/", 1)
            return float(a) / float(b)
        return float(t)
    except (ValueError, ZeroDivisionError):
        return None


def es_correcto(texto, resp, tol):
    if _es_numero(resp):
        v = a_numero(texto)
        return v is not None and abs(v - resp) <= tol
    return texto.strip().lower() == str(resp).strip().lower()


def crear_pergamino(w, h):
    import random
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pergamino.jpg")
    if os.path.exists(ruta):
        return pygame.transform.smoothscale(pygame.image.load(ruta).convert(), (w, h))
    surf = pygame.Surface((w, h))
    surf.fill((222, 184, 105))
    rng = random.Random(7)
    for _ in range(260):
        r = rng.randint(20, 90)
        c = rng.randint(-30, 20)
        blob = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(blob, (200 + c, 150 + c, 70 + c, rng.randint(8, 22)), (r, r), r)
        surf.blit(blob, (rng.randint(-r, w - r), rng.randint(-r, h - r)))
    for i in range(30):
        a = int(90 * (1 - i / 30) ** 2)
        borde = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(borde, (60, 30, 5, a), (i, i, w - 2 * i, h - 2 * i), 1)
        surf.blit(borde, (0, 0))
    return surf


def ajustar_texto(fuente, texto, ancho_max):
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
    return lineas


class Paso:
    def __init__(self, datos):
        self.titulo = datos["titulo"]
        self.filas = datos["filas"]
        self.entradas = []      # [(UITextEntryLine, respuesta, tolerancia)]
        self.boton = None
        self.resuelto = False


# ---------------------------------------------------------------------- juego
class Juego:
    """Pantalla de nivel.

    Modo independiente (modo_mapa=False): recorre todos los niveles con "Siguiente nivel".
    Modo mapa (modo_mapa=True): se juega un solo nivel y `ejecutar()` devuelve
        "completado" | "volver" | "salir"  (ver numerical_realms.py).
    """

    def __init__(self, niveles, modo_mapa=False, sonido=True):
        pygame.init()
        self.modo_mapa = modo_mapa
        self.niveles = niveles
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.manager = pygame_gui.UIManager((ANCHO, ALTO), theme_path=io.StringIO(json.dumps(THEME)))
        self.fuentes = {}
        self.pergamino = crear_pergamino(PERGAMINO.width, PERGAMINO.height)
        self.rect_config = pygame.Rect(22, 30, 60, 65)
        self.rect_sonido = pygame.Rect(780, 30, 60, 65)
        self.sonido = sonido
        self.scroll = UIScrollingContainer(PERGAMINO.copy(), self.manager, allow_scroll_x=False)
        self.corriendo = True
        self.cargar_nivel(0)

    def fuente(self, tam):
        if tam not in self.fuentes:
            self.fuentes[tam] = pygame.font.SysFont("arial", tam)
        return self.fuentes[tam]

    # ---------------------------------------------------------- niveles
    def cargar_nivel(self, idx):
        for el in list(self.scroll.get_container().elements):
            el.kill()
        self.idx = idx
        datos = self.niveles[idx]
        pygame.display.set_caption(datos["titulo"])
        self.titulo = datos["titulo"]
        self.instruccion = datos["instruccion"]
        self.tiempo = float(datos.get("tiempo", TIEMPO_DEFECTO))
        self.pasos_pendientes = [Paso(p) for p in datos["pasos"]]
        self.pasos = []
        self.errores = 0
        self.estado = ""            # "", "ok", "tiempo"
        self.btn_sig = None
        self.btn_volver = None
        self.btn_reintentar = None
        self.pendiente_scroll = 0.0

        y = 6
        y = self.texto_largo(y, self.titulo, 32)
        for linea in datos.get("intro", []):
            y = self.texto_largo(y, linea, 28)
        self.cursor_y = y + 16
        self.agregar_siguiente_paso()

    # ------------------------------------------------- ayudas de interfaz
    def ancho_texto(self, texto):
        try:
            f = self.manager.get_theme().get_font_dictionary().find_font(16, "noto_sans")
            try:
                return f.get_rect(texto).width
            except Exception:
                return f.size(texto)[0]
        except Exception:
            return len(texto) * 9

    def etiqueta(self, rect, texto, centrado=False):
        kw = {"object_id": "#centrado"} if centrado else {}
        return UILabel(rect, texto, self.manager, container=self.scroll, **kw)

    def texto_largo(self, y, texto, alto):
        """Crea etiquetas partiendo el texto en líneas que quepan. Devuelve la nueva y."""
        actual = ""
        lineas = []
        for p in texto.split():
            prueba = (actual + " " + p).strip()
            if self.ancho_texto(prueba) <= AREA_W - 16 or not actual:
                actual = prueba
            else:
                lineas.append(actual)
                actual = p
        lineas.append(actual)
        for l in lineas:
            self.etiqueta(pygame.Rect(0, y, AREA_W, alto - 2), l)
            y += alto - 4
        return y + 4

    def medir(self, tok):
        """-> (tipo, dato, ancho, alto, extra)"""
        if isinstance(tok, dict) and "matriz" in tok:
            m = tok["matriz"]
            anchos = []
            for j in range(len(m[0])):
                w = ENT_W
                for fila in m:
                    c = fila[j]
                    if isinstance(c, dict):
                        w = max(w, c.get("ancho", ENT_W))
                    else:
                        w = max(w, self.ancho_texto(str(c)) + 12)
                anchos.append(w)
            total = sum(anchos) + 4 * (len(anchos) - 1) + 2 * CORCHETE_W
            return ("mat", m, total, len(m) * ALTO_FILA, anchos)
        if isinstance(tok, dict):
            return ("in", tok, tok.get("ancho", ENT_W), ALTO_FILA, None)
        txt = str(tok)
        return ("txt", txt, self.ancho_texto(txt) + 12, ALTO_FILA, None)

    def crear_entrada(self, paso, x, y, d):
        e = UITextEntryLine(pygame.Rect(x, y, d.get("ancho", ENT_W), ALTO_FILA - 4),
                            self.manager, container=self.scroll)
        if _es_numero(d["in"]):
            e.set_allowed_characters(list("0123456789.,-/"))
        e.set_text_length_limit(int(d.get("limite", 8)))
        paso.entradas.append((e, d["in"], d.get("tol", 1e-6)))

    def agregar_siguiente_paso(self):
        if not self.pasos_pendientes:
            return
        paso = self.pasos_pendientes.pop(0)
        self.pasos.append(paso)
        y = self.cursor_y
        y_tit = self.texto_largo(y, paso.titulo, 30)
        ry = y_tit

        for fila in paso.filas:
            # 1) repartir los tokens en líneas según el ancho disponible
            lineas, x = [[]], 4
            for tok in fila:
                it = self.medir(tok)
                if x + it[2] > MAX_X and lineas[-1]:
                    lineas.append([])
                    x = 4
                lineas[-1].append(it)
                x += it[2] + 4
            # 2) crear los elementos
            for linea in lineas:
                lh = max(it[3] for it in linea)
                x = 4
                for tipo, dato, w, h, extra in linea:
                    oy = ry + (lh - h) // 2
                    if tipo == "txt":
                        self.etiqueta(pygame.Rect(x, oy, w, ALTO_FILA - 4), dato)
                    elif tipo == "in":
                        self.crear_entrada(paso, x, oy, dato)
                    else:
                        self.crear_matriz(paso, x, oy, dato, extra)
                    x += w + 4
                ry += lh

        paso.boton = UIButton(pygame.Rect(BOTON_X, y_tit, 96, 34), "Comprobar",
                              self.manager, container=self.scroll)
        self.cursor_y = ry + 18
        self.scroll.set_scrollable_area_dimensions((AREA_W, self.cursor_y + 10))
        self.pendiente_scroll = 1.0 if len(self.pasos) > 1 else 0.0

    def crear_matriz(self, paso, x, y, m, anchos):
        ancho_total = sum(anchos) + 4 * (len(anchos) - 1)
        for i, fila in enumerate(m):
            fy = y + i * ALTO_FILA
            self.etiqueta(pygame.Rect(x, fy, CORCHETE_W, ALTO_FILA - 4), "[")
            self.etiqueta(pygame.Rect(x + CORCHETE_W + ancho_total, fy, CORCHETE_W, ALTO_FILA - 4), "]")
            cx = x + CORCHETE_W
            for j, c in enumerate(fila):
                if isinstance(c, dict):
                    ex = cx + (anchos[j] - c.get("ancho", ENT_W)) // 2
                    self.crear_entrada(paso, ex, fy, c)
                else:
                    self.etiqueta(pygame.Rect(cx, fy, anchos[j], ALTO_FILA - 4), str(c), centrado=True)
                cx += anchos[j] + 4

    def agregar_final(self):
        y = self.cursor_y
        if self.modo_mapa:
            self.btn_volver = UIButton(pygame.Rect(0, y, 180, 36), "Volver al mapa",
                                       self.manager, container=self.scroll)
        elif self.idx + 1 < len(self.niveles):
            self.btn_sig = UIButton(pygame.Rect(0, y, 180, 36), "Siguiente nivel >>",
                                    self.manager, container=self.scroll)
        else:
            self.etiqueta(pygame.Rect(0, y, AREA_W, 30), "¡Terminaste todos los niveles!")
        self.cursor_y = y + 50
        self.scroll.set_scrollable_area_dimensions((AREA_W, self.cursor_y))
        self.pendiente_scroll = 1.0

    def agregar_botones_tiempo(self):
        """Al agotarse el tiempo (modo mapa): ofrece reintentar o volver."""
        y = self.cursor_y
        self.etiqueta(pygame.Rect(0, y, AREA_W, 28), "Se acabó el tiempo. ¿Lo intentas de nuevo?")
        self.btn_reintentar = UIButton(pygame.Rect(0, y + 34, 150, 36), "Reintentar",
                                       self.manager, container=self.scroll)
        self.btn_volver = UIButton(pygame.Rect(160, y + 34, 180, 36), "Volver al mapa",
                                   self.manager, container=self.scroll)
        self.cursor_y = y + 84
        self.scroll.set_scrollable_area_dimensions((AREA_W, self.cursor_y))
        self.pendiente_scroll = 1.0

    def resultado_salida(self):
        """Lo que se devuelve al mapa al cerrar el nivel."""
        return "completado" if self.estado == "ok" else "volver"

    def aplicar_sonido(self):
        try:   # conecta aquí tu música: pygame.mixer.music.set_volume(...)
            pygame.mixer.music.set_volume(1.0 if self.sonido else 0.0)
        except pygame.error:
            pass

    # ------------------------------------------------------------ lógica
    def comprobar(self, paso):
        if paso.resuelto or self.estado:
            return
        todo_bien = True
        for e, resp, tol in paso.entradas:
            ok = es_correcto(e.get_text(), resp, tol)
            todo_bien &= ok
            try:
                e.change_object_id("#ok_entry" if ok else "#wrong_entry")
            except Exception:
                pass
        if not todo_bien:
            self.errores += 1
            return
        paso.resuelto = True
        for e, _, _ in paso.entradas:
            e.disable()
        paso.boton.disable()
        if self.pasos_pendientes:
            self.agregar_siguiente_paso()
        else:
            self.estado = "ok"
            self.agregar_final()

    def bloquear_todo(self):
        for p in self.pasos:
            for e, _, _ in p.entradas:
                e.disable()
            p.boton.disable()

    # ------------------------------------------------------------- dibujo
    def dibujar_fondo(self):
        s = self.pantalla
        s.fill((245, 245, 245))
        pygame.draw.rect(s, OSCURO, (8, 13, 844, 598))
        pygame.draw.rect(s, GRIS, (20, 30, 822, 65))
        pygame.draw.rect(s, NARANJA, (308, 40, 243, 43), border_radius=22)
        titulo = self.titulo
        for tam in (26, 22, 18, 15):
            if self.fuente(tam).size(titulo)[0] <= 225:
                break
        while self.fuente(tam).size(titulo)[0] > 225 and len(titulo) > 4:
            titulo = titulo[:-2].rstrip() + "…" if not titulo.endswith("…") else titulo[:-2] + "…"
        img = self.fuente(tam).render(titulo, True, (40, 20, 5))
        s.blit(img, img.get_rect(center=(429, 62)))
        self.dibujar_icono_config()
        self.dibujar_icono_sonido()

        pygame.draw.rect(s, GRIS, (20, 110, 232, 488))
        t = max(0, int(math.ceil(self.tiempo)))
        pygame.draw.rect(s, VERDE, (30, 125, 210, 87))
        color_t = ROJO if (t <= 60 and self.estado != "ok") else BLANCO
        self.centrado(24, f"Tiempo: {t // 60:02d}:{t % 60:02d}", color_t, (135, 168))

        pygame.draw.rect(s, CAFE, (30, 223, 210, 262))
        self.centrado(24, "Instrucción:", BLANCO, (135, 258))
        for tam in (20, 18, 16, 14, 12):
            f = self.fuente(tam)
            lineas = ajustar_texto(f, self.instruccion, 190)
            if len(lineas) * (tam + 6) <= 150:
                break
        y = 295
        for l in lineas:
            self.centrado(tam, l, BLANCO, (135, y))
            y += tam + 6
        if self.estado == "ok":
            self.centrado(22, "¡Nivel completado!", AMARILLO, (135, 462))
        elif self.estado == "tiempo":
            self.centrado(22, "¡Tiempo agotado!", ROJO, (135, 462))

        pygame.draw.rect(s, VERDE, (30, 497, 210, 87))
        self.centrado(24, f"Errores: {self.errores}", BLANCO, (135, 540))
        pygame.draw.rect(s, GRIS, (264, 110, 578, 488))
        s.blit(self.pergamino, PERGAMINO.topleft)

    def centrado(self, tam, texto, color, centro):
        img = self.fuente(tam).render(texto, True, color)
        self.pantalla.blit(img, img.get_rect(center=centro))

    def dibujar_icono_config(self):
        cx, cy = self.rect_config.center
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(self.pantalla, OSCURO,
                             (cx + 14 * math.cos(a), cy + 14 * math.sin(a)),
                             (cx + 22 * math.cos(a), cy + 22 * math.sin(a)), 7)
        pygame.draw.circle(self.pantalla, OSCURO, (cx, cy), 17)
        pygame.draw.circle(self.pantalla, GRIS, (cx, cy), 7)

    def dibujar_icono_sonido(self):
        s = self.pantalla
        cx, cy = self.rect_sonido.center
        pygame.draw.polygon(s, OSCURO, [(cx - 20, cy - 8), (cx - 10, cy - 8), (cx + 2, cy - 20),
                                        (cx + 2, cy + 20), (cx - 10, cy + 8), (cx - 20, cy + 8)])
        if self.sonido:
            for r in (12, 20):
                pygame.draw.arc(s, OSCURO, (cx + 2 - r, cy - r, 2 * r, 2 * r), -0.9, 0.9, 4)
        else:
            pygame.draw.line(s, (170, 40, 40), (cx + 8, cy - 12), (cx + 24, cy + 12), 4)
            pygame.draw.line(s, (170, 40, 40), (cx + 24, cy - 12), (cx + 8, cy + 12), 4)

    # ----------------------------------------------------------- bucle
    def procesar(self, ev):
        """Devuelve "salir", "volver" o "completado" cuando hay que cerrar el nivel; si no, None."""
        if ev.type == pygame.QUIT:
            self.corriendo = False
            return "salir"
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            return self.resultado_salida()
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect_sonido.collidepoint(ev.pos):
                self.sonido = not self.sonido
                self.aplicar_sonido()
            elif self.rect_config.collidepoint(ev.pos):
                print("Abrir ajustes (pendiente de implementar)")
        elif ev.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.btn_volver is not None and ev.ui_element is self.btn_volver:
                return self.resultado_salida()
            if self.btn_reintentar is not None and ev.ui_element is self.btn_reintentar:
                self.cargar_nivel(self.idx)
                return None
            if self.btn_sig is not None and ev.ui_element is self.btn_sig:
                self.cargar_nivel(self.idx + 1)
                return None
            for p in self.pasos:
                if ev.ui_element is p.boton:
                    self.comprobar(p)
        elif ev.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            for p in self.pasos:
                if any(ev.ui_element is e for e, _, _ in p.entradas):
                    self.comprobar(p)
        self.manager.process_events(ev)
        return None

    def cuadro(self, dt):
        if not self.estado:
            self.tiempo -= dt
            if self.tiempo <= 0:
                self.tiempo = 0
                self.estado = "tiempo"
                self.bloquear_todo()
                if self.modo_mapa:
                    self.agregar_botones_tiempo()
        self.manager.update(dt)
        if self.pendiente_scroll is not None:
            barra = getattr(self.scroll, "vert_scroll_bar", None)
            if barra is not None:
                try:
                    barra.set_scroll_from_start_percentage(self.pendiente_scroll)
                except Exception:
                    pass
            self.pendiente_scroll = None
        self.dibujar_fondo()
        self.manager.draw_ui(self.pantalla)
        pygame.display.flip()

    def ejecutar(self):
        """Bucle del nivel. Devuelve "completado", "volver" o "salir"."""
        self.aplicar_sonido()
        while True:
            dt = self.reloj.tick(60) / 1000.0
            for ev in pygame.event.get():
                r = self.procesar(ev)
                if r:
                    return r
            self.cuadro(dt)

    def run(self):
        """Modo independiente: corre hasta cerrar la ventana (o Esc) y sale de pygame."""
        self.ejecutar()
        pygame.quit()


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, "niveles.json")
    try:
        niveles = cargar_niveles(ruta)
    except FileNotFoundError:
        sys.exit(f"No encuentro el archivo: {ruta}\nUso: python nivel_generico.py [archivo.json]")
    except json.JSONDecodeError as e:
        sys.exit(f"JSON mal formado en {ruta}: {e}")
    except ValueError as e:
        sys.exit(f"Estructura inválida en {ruta}\n  {e}")
    Juego(niveles).run()


if __name__ == "__main__":
    main()
