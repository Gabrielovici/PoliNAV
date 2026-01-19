from .audio_service import AudioService
from .llm_service import LLMService
from .command_processor import CommandProcessor


class PoliNAVSystem:
    def __init__(self):
        print("\n[SYSTEM] Initializare PoliNAV Modular...")

        # Initializam componentele
        self.audio = AudioService()
        self.llm = LLMService()
        self.logic = CommandProcessor()

        print("[SYSTEM] Sistem Modular Online.\n")

    def listen_and_decide(self, current_memory, rx, ry):
        """
        Functia principala apelata din Main cand apesi 'N'.
        """
        # 1. Feedback Audio
        self.audio.speak("Te ascult.")

        # 2. Ascultare
        user_text = self.audio.listen()

        # Verificari rapide
        if not user_text:
            self.audio.speak("Nu am auzit nimic.")
            return None

        if any(w in user_text.lower() for w in ["stop", "anuleaza"]):
            self.audio.speak("Anulat.")
            return None

        # 3. Analiza Logica (fara AI)
        decision = self.logic.analyze(user_text, current_memory, (rx, ry))

        # 4. Fallback la LLM (AI) daca logica nu a gasit o comanda clara
        if not decision:
            ai_response = self.llm.generate_response(user_text)
            decision = {"action": "chat", "text": ai_response}

        # 5. Executie
        if decision.get("text"):
            self.audio.speak(decision["text"])

        if decision.get("action") == "navigate":
            return decision["target_id"]

        return None

    def speak(self, text):

        self.audio.speak(text)