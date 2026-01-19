import numpy as np

# --- CONFIGURARE GENERALA NAVIGARE ---
# Distanta maxima (in metri) la care robotul considera un obiect valid pentru memorare
DIST_MEMORARE = 1.2

# Viteza standard de deplasare a motoarelor (unitati relative CoppeliaSim)
VITEZA_BASE = 1.3

# Cat de aproape (in metri) trebuie sa fie robotul de tinta X,Y ca sa spuna "Am ajuns"
TOLERANTA_TINTA = 0.30

# --- CONFIGURARE EVITARE OBSTACOLE ---
# Distanta minima fata de un obstacol la care robotul incepe manevra de ocolire
DIST_OCOLIRE = 0.30

# --- CALIBRARE HARTA SI GRID ---
# Dimensiunea fizica a unui patratel din harta digitala (0.5 metri x 0.5 metri)
MAP_RESOLUTION = 0.5

# Coordonata X de unde incepe harta in lumea simulatorului (Coltul stanga-sus)
MAP_ORIGIN_X = -12.20

# Coordonata Y de unde incepe harta in lumea simulatorului
MAP_ORIGIN_Y = -12.30

# --- PARAMETRI MEMORIE (RAZA DE IDENTITATE) ---
# Daca robotul vede un obiect nou la o distanta mai mica de X metri fata de unul vechi,
# considera ca este acelasi obiect si doar ii actualizeaza pozitia, nu creeaza dublura.
MEMORY_THRESHOLDS = {
    'scaun': 1.2,      # Scaunele sunt dese, raza mica
    'fotoliu': 0.6,    # Fotoliile sunt mari
    'persoana': 1.0,   # Oamenii se misca
    'planta': 0.55,
    'tonomat': 3.0,    # Tonomatul e mare, il vedem de departe
    'masa': 1.3,
    'default': 15.0    # Valoare de siguranta pentru obiecte necunoscute
}

# --- PARAMETRI FILTRARE VIZUALA ---
# Un obiect trebuie sa ocupe minim X% din inaltimea ecranului pentru a fi validat.
# Asta previne detectarea obiectelor minuscule aflate in celalalt capat al halei.
VISUAL_MIN_HEIGHT = {
    'scaun': 0.20,     # Minim 20% din ecran
    'fotoliu': 0.55,   # Trebuie sa fie foarte aproape
    'planta': 0.70,
    'tonomat': 1.00,   # Trebuie sa fim langa el
    'masa': 1.00,
    'default': 0.25
}

# --- FUNCTIE GENERARE HARTA VIRTUALA ---
def genereaza_harta_L():
    """
    Construieste o matrice (grid) care reprezinta forma halei (litera L).
    0 = Spatiu Liber (Podea), 1 = Zid/Interzis.
    """
    # Dimensiunile totale ale halei in metri
    width_m = 20.0
    height_m = 15.0

    # Calculam cate celule (patratele) incap pe orizontala si verticala
    cols = int(width_m / MAP_RESOLUTION)
    rows = int(height_m / MAP_RESOLUTION)

    # Initializam totul cu 1 (Presupunem ca totul e zid la inceput)
    grid = [[1 for _ in range(cols)] for _ in range(rows)]

    # Definim o marja de siguranta (padding) ca robotul sa nu se lipeasca de pereti
    padding = 0.25

    # Parcurgem fiecare celula din matrice pentru a "sculpta" forma halei
    for r in range(rows):
        for c in range(cols):
            # Calculam coordonata reala (in metri) a centrului celulei curente
            x = (c * MAP_RESOLUTION) + (MAP_RESOLUTION / 2)
            y = (r * MAP_RESOLUTION) + (MAP_RESOLUTION / 2)

            is_walkable = False

            # Definim Zona 1: Baza L-ului (holul lung de jos)
            if (padding < x < 20.0 - padding) and (padding < y < 5.0 - padding):
                is_walkable = True

            # Definim Zona 2: Turnul din stanga
            if (padding < x < 5.0 - padding) and (4.5 <= y < 10.0 - padding):
                is_walkable = True

            # Definim Zona 3: Turnul din mijloc
            if (10.0 + padding < x < 15.0 - padding) and (4.5 <= y < 15.0 - padding):
                is_walkable = True

            # Daca celula se afla intr-una din zonele libere, o marcam cu 0 (Liber)
            if is_walkable:
                grid[r][c] = 0

    return grid