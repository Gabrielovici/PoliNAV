import os

# ==========================================
# CONSTANTE SI CONFIGURARI VOCALE
# ==========================================

# Chei API (ElevenLabs)
ELEVENLABS_API_KEY = "9af36c78c52d66a40ff8d83f0cab0f45edb795249489bc34d31fbc1f94e470ad"
VOICE_ID = "sGcPNcpR5PikknzyXcy7"

# Căi Fișiere (Calculate relativ la acest fișier)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "llm", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
AUDIO_OUTPUT_FILE = "robot_response.mp3" #aici salveaza fisierul cu sunetul, se actulizaza mereu

# Setări Microfon
MIC_ENERGY_THRESHOLD = 350
MIC_PAUSE_THRESHOLD = 2.0
MIC_TIMEOUT = 4
MIC_PHRASE_LIMIT = 7
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
    "turcoaz":["turcoaz","tucoaz"],
}