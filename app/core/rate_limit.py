"""Limitador de intentos en memoria, para frenar la fuerza bruta.

El backend corre como un solo proceso de uvicorn, así que un contador en
memoria alcanza. Si el servicio se reinicia, los contadores se ponen a cero: es
un límite «suficiente», no un antifraude.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class IntentoThrottle:
    """Cuenta fallos por clave (p. ej. «correo|ip») dentro de una ventana.

    Al llegar a `max_intentos` fallos dentro de `ventana_seg`, la clave queda
    bloqueada durante `bloqueo_seg`. Un acierto la limpia.
    """

    def __init__(self, max_intentos: int = 8, ventana_seg: int = 300, bloqueo_seg: int = 900):
        self.max_intentos = max_intentos
        self.ventana_seg = ventana_seg
        self.bloqueo_seg = bloqueo_seg
        self._fallos: dict[str, deque[float]] = defaultdict(deque)
        self._bloqueo_hasta: dict[str, float] = {}
        self._lock = Lock()

    def _purgar(self, clave: str, ahora: float) -> None:
        cola = self._fallos[clave]
        while cola and ahora - cola[0] > self.ventana_seg:
            cola.popleft()

    def segundos_de_espera(self, clave: str) -> int:
        """0 si la clave puede intentar; si no, cuántos segundos faltan."""
        ahora = time.monotonic()
        with self._lock:
            fin = self._bloqueo_hasta.get(clave)
            if fin is None:
                return 0
            if ahora >= fin:
                self._bloqueo_hasta.pop(clave, None)
                self._fallos.pop(clave, None)
                return 0
            return int(fin - ahora) + 1

    def registrar_fallo(self, clave: str) -> None:
        ahora = time.monotonic()
        with self._lock:
            cola = self._fallos[clave]
            cola.append(ahora)
            self._purgar(clave, ahora)
            if len(cola) >= self.max_intentos:
                self._bloqueo_hasta[clave] = ahora + self.bloqueo_seg

    def limpiar(self, clave: str) -> None:
        with self._lock:
            self._fallos.pop(clave, None)
            self._bloqueo_hasta.pop(clave, None)


# Login: 8 fallos en 5 min → 15 min de bloqueo.
login_throttle = IntentoThrottle(max_intentos=8, ventana_seg=300, bloqueo_seg=900)

# Recuperación de contraseña (verificar-correo / restablecer-clave): más laxo,
# por IP, para no ayudar a enumerar correos ni a probar restablecimientos.
recuperacion_throttle = IntentoThrottle(max_intentos=15, ventana_seg=600, bloqueo_seg=900)
