import json
import math
import os
import sys

# --- IMPORTURI DINAMICE ---
# Adaugam radacina proiectului in calea sistemului pentru a putea importa 'config'
# "../.." ne duce din src/app inapoi in radacina PoliNAV
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config.config as config

# --- CALCUL CALE FISIER ---
# Calculam calea absoluta catre fisierul JSON, indiferent de unde rulam scriptul
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MEMORY_FILE = os.path.join(BASE_DIR, "data", "harta_robot.json")


def incarca_harta():
    """
    Citeste fisierul JSON de pe disc si returneaza lista de obiecte.
    """
    # Verificam daca fisierul exista fizic
    if not os.path.exists(MEMORY_FILE):
        return []  # Daca nu, returnam o memorie goala
    try:
        # Deschidem fisierul in mod citire ("r" - read)
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            # Ne asiguram ca datele citite sunt o lista valida
            if isinstance(data, list):
                return data
            return []
    except:
        # In caz de eroare (fisier corupt), returnam lista goala pentru a nu bloca robotul
        return []


def salveaza_harta(lista_obiecte):
    """
    Scrie lista actualizata de obiecte inapoi in fisierul JSON.
    """
    try:
        # Deschidem fisierul in mod scriere ("w" - write), ceea ce sterge continutul vechi
        with open(MEMORY_FILE, "w") as f:
            # Scriem datele formatat frumos (indent=4) ca sa fie citibile de om
            json.dump(lista_obiecte, f, indent=4)
    except Exception as e:
        print(f"[MEMORIE EROARE] Nu pot salva harta: {e}")


def get_next_id(lista_obiecte):
    """
    Genereaza un ID unic pentru un obiect nou (Ex: daca avem 1,2,3 -> returneaza 4).
    """
    if not lista_obiecte:
        return 1
    # Gasim cel mai mare ID existent in lista si adaugam 1
    max_id = max([o['id'] for o in lista_obiecte])
    return max_id + 1


def proceseaza_obiect(lista_obiecte, tip, x, y):
    """
    Nucleul memoriei: Decide daca un obiect vazut este NOU sau este unul VECHI actualizat.
    """

    # 1. Obtinem raza de toleranta pentru acest tip de obiect din config
    raza_identitate = config.MEMORY_THRESHOLDS.get(tip, config.MEMORY_THRESHOLDS['default'])

    cel_mai_apropiat = None
    dist_minima = 999.0

    # 2. Cautam in memorie: Avem deja un obiect de acest tip in apropiere?
    for obj in lista_obiecte:
        if obj['tip'] == tip:
            # Calculam distanta Euclidiana (Pitagora) intre ce vedem si ce stim
            d = math.sqrt((obj['x'] - x) ** 2 + (obj['y'] - y) ** 2)

            # Retinem obiectul care este cel mai aproape de detectia curenta
            if d < dist_minima:
                dist_minima = d
                cel_mai_apropiat = obj

    # 3. Luam decizia
    if cel_mai_apropiat is not None and dist_minima < raza_identitate:
        # CAZ A: DUPLICAT -> Este acelasi obiect pe care l-am mai vazut.
        # Rafinam pozitia facand media intre vechea pozitie si cea noua.
        cel_mai_apropiat['x'] = (cel_mai_apropiat['x'] + x) / 2.0
        cel_mai_apropiat['y'] = (cel_mai_apropiat['y'] + y) / 2.0

        msg = f"Actualizat {tip} #{cel_mai_apropiat['id']} (Dist: {dist_minima:.2f}m)"
        return lista_obiecte, msg
    else:
        # CAZ B: OBIECT NOU -> Nu avem nimic asemanator in zona.
        new_id = get_next_id(lista_obiecte)
        nou_obiect = {
            "id": new_id,
            "tip": tip,
            "x": round(x, 2),  # Rotunjim coordonatele pentru curatenie
            "y": round(y, 2),
        }
        lista_obiecte.append(nou_obiect)
        msg = f"NOU! {tip} detectat -> ID:{new_id} la ({x:.1f}, {y:.1f})"
        return lista_obiecte, msg