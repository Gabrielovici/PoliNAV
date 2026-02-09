#Conditii multiple Triggers
import math
from . import voice_config as cfg


class CommandProcessor:
    def __init__(self):
        self.context_state = None

    def analyze(self, text, memory_data, robot_pos):

        text = text.lower()
        rx, ry = robot_pos

        #Desigur, se putea pune si in voice_config.py.
        if self.context_state == "WAITING_BAIE_GENDER":
            if any(w in text for w in ["fete", "femei"]):
                return self._create_nav_target("rosu", memory_data, rx, ry)
            if any(w in text for w in ["baieti", "băieți","bărbați"]):
                return self._create_nav_target("albastru", memory_data, rx, ry)
            self.context_state = None

        #TRIGGERS SPECIALI
        # Baie
        if any(w in text for w in ["baie", "baia", "toaleta"]):
            self.context_state = "WAITING_BAIE_GENDER"
            return {"action": "ask", "text": "Pentru fete sau pentru băieți?"}

        #Gabriel Sima
        if any(w in text for w in ["sima"]):
            self.context_state = "WAITING_SIMA_NAME"
            return {"action": "ask", "text": "Care din ei?"}


       #CAUTARE IN DICTIONAR
        for key, words in cfg.SYNONYMS.items():
            if any(w in text for w in words):
                return self._create_nav_target(key, memory_data, rx, ry)

        #NIMIC GASIT
        return None
        #Cautare cel mai apropiat punct din lista.
    def _create_nav_target(self, target_type, memory_data, rx, ry):

        self.context_state = None

        candidates = [o for o in memory_data if target_type in o['tip'].lower()]

        if not candidates:
            return {"action": "chat", "text": f"Nu știu unde este {target_type}."}

        # Matematica: Distanta Euclidiana
        best = min(candidates, key=lambda o: math.sqrt((o['x'] - rx) ** 2 + (o['y'] - ry) ** 2))

        return {
            "action": "navigate",
            "target_id": best['id'],
            "text": f"Am înțeles. Mergem la {best['tip']}."
        }