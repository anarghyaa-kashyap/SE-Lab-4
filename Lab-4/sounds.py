import math
from array import array
import pygame

class Sounds:
    VOLUME = 0.25
    FADE_SECONDS = 0.005

    def __init__(self):
        self.enabled = False
        self._sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            frequency, size, channels = pygame.mixer.get_init()
            if size != -16:
                return
            self._rate = frequency
            self._channels = channels
            self._sounds = {
                "jump": self._make([(400, 800, 0.12)]),
                "score": self._make([(880, 880, 0.06), (1320, 1320, 0.08)]),
                "game_over": self._make([(440, 110, 0.6)]),
            }
            self.enabled = True
        except (pygame.error, NotImplementedError):
            self.enabled = False
            self._sounds = {}

    def _make(self, segments):
        samples = array("h")
        amplitude = self.VOLUME * 32767
        fade = max(1, int(self._rate * self.FADE_SECONDS))
        phase = 0.0
        for start_hz, end_hz, duration in segments:
            n = int(self._rate * duration)
            for i in range(n):
                hz = start_hz + (end_hz - start_hz) * (i / n)
                phase += 2 * math.pi * hz / self._rate
                value = amplitude if math.sin(phase) >= 0 else -amplitude
                envelope = min(1.0, i / fade, (n - i) / fade)
                sample = int(value * envelope)
                for _ in range(self._channels):
                    samples.append(sample)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if self.enabled:
            self._sounds[name].play()