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

        # Feedback initial
        self.audio.speak("Spune-mi te rog, cu ce te pot ajuta.")

        # BUCLA DE DIALOG
        # Ramanem aici cat timp robotul are intrebari de pus (context activ)
        while True:
            # 1. Ascultare
            user_text = self.audio.listen()

            # Daca nu aude nimic sau zici Stop, iesim
            if not user_text:
                self.audio.speak("Nu am auzit. Anulez.")
                return None

            if any(w in user_text.lower() for w in ["stop", "anuleaza", "lasa"]):
                self.audio.speak("Anulat.")
                return None

            # 2. Analiza Logica
            decision = self.logic.analyze(user_text, current_memory, (rx, ry))

            # 3. Fallback la LLM (doar daca Logica nu a dat niciun rezultat si nici nu e o intrebare in curs)
            if not decision:
                # Generam contextul doar daca e nevoie de LLM
                context_string = self._generate_memory_context(current_memory)
                ai_response = self.llm.generate_response(user_text, context_info=context_string)
                decision = {"action": "chat", "text": ai_response}

            # 4. Executie si Vorbire
            if decision.get("text"):
                self.audio.speak(decision["text"])

            # 5. DECIZIA DE IESIRE DIN BUCLA
            action = decision.get("action")

            if action == "navigate":
                # Daca am gasit tinta, returnam ID-ul si iesim din bucla
                return decision["target_id"]

            elif action == "ask":
                print("[SYSTEM] Astept raspunsul utilizatorului...")
                continue

            else:
                # Daca e doar "chat" sau altceva, conversatia s-a terminat.
                return None

    def speak(self, text):
        self.audio.speak(text)

    def _generate_memory_context(self, memory_data):
        if not memory_data:
            return "Memoria mea este goala."
        items = [f"{obj['tip']} (ID {obj['id']})" for obj in memory_data]
        return "Obiecte cunoscute: " + ", ".join(items) + "."