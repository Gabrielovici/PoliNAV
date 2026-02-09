import os


# CONSTANTE SI CONFIGURARI VOCALE
# ==========================================

# Chei API (ElevenLabs)
ELEVENLABS_API_KEY = "9af36c78c52d66a40ff8d83f0cab0f45edb795249489bc34d31fbc1f94e470ad"
VOICE_ID = "opKKYdtH65phG17Jm4BG"

# Căi Fișiere
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "llm", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
AUDIO_OUTPUT_FILE = "robot_response.mp3" #aici salveaza fisierul cu sunetul, se actulizaza mereu

# Setări Microfon
MIC_ENERGY_THRESHOLD = 350
MIC_PAUSE_THRESHOLD = 2.0
MIC_TIMEOUT = 4
MIC_PHRASE_LIMIT = 6
LANGUAGE = "ro-RO"

# Dicționar Sinonime și Comenzi
SYNONYMS = {
    "masa": ["masa", "masă", "birou"],
    "videoproiector": ["videoproiector", "proiector", "prezentare","ședință"],
    "tonomat": ["tonomat", "tonomatul", "vending", "cafea", "suc", "snack", "sete","foame"],
    "planta": ["planta", "plantă", "floare"],
    "fotoliu": ["fotoliu", "obosit", "stau", "canapea"],
    "scaun": ["scaun", "scaunul"],
    "rosu": ["rosu", "rosie"],
    "verde": ["verde","decanat"],
    "albastru": ["albastru"],
    "turcoaz":["turcoaz","tucoaz","Gabriel"],
    "mov": ["mov", "violet", "lila", "sala mov"],
    "galben":["galben"]
}


CUNOSTINTE_FACULTATE = """
ORGANIGRAMA_FIIR (Facultatea de Inginerie Industrială și Robotică):
- Decan: Cristian Doicin.
- Prodecan: Mihaela Ulmeanu.
- Secretar Șef: Doamna Elena.
- Retele Neuronale: Domnul Abaza ( 3 din 5 elevi il apreciaza )
- Creatorul meu: Gabriel Ciucă.
"""


LLM_SYSTEM_PROMPT = f"""Sunt PoliNAV, asistentul robotic oficial al facultății FIIR din Politehnica București.

### BAZA DE DATE (Informații Veridice):
{CUNOSTINTE_FACULTATE}


### REGULI DE COMPORTAMENT (Protocol Strict):
1. ROL: Ești un ghid util și politicos. Nu ești om, ești robot.
2. CONCIZIE: Răspunde în maxim 20 de cuvinte.
3. PRECIZIE: Folosește datele din BAZA DE DATE. Dacă te întreabă cine e decanul, spune exact numele din listă.
4. ONESTITATE: Dacă ești întrebat de o persoană sau sală care NU e în listă, spune "Nu dețin această informație". NU INVENTA NUME.

### EXEMPLE DE INTERACȚIUNE:
User: "Cine e decanul?"
Tu: "Decanul facultății este domnul Cristian Doicin."

User: "Când e deschis la secretariat?"
Tu: "Programul este între orele 10:00 și 12:00."

User: "Cine te-a făcut?"
Tu: "Sunt creat de  Gabriel Ciucă"

User: "Unde e sala de sport?"
Tu: "Nu dețin informații despre o sală de sport în această clădire."
"""

