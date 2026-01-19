import time
import math
import cv2
import sys
import os

# Adaug calea catre radacina proiectului ca sa pot importa modulele din alte foldere
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# Import modulele mele
import config.config as config
import src.app.vision_handler as vision
import src.app.control as control
import src.app.memory as memory
import src.app.planner as planner
from src.neural_network.voice_engine import PoliNAVSystem


def main():
    print("=== START PROIECT POLINAV ===")

    # 1. Conectare la Simulator (CoppeliaSim)
    client = RemoteAPIClient()
    sim = client.require('sim')
    sim.setStepping(False)  # Las simularea sa mearga in timp real, nu pas cu pas

    try:
        # Aici iau handle-urile (adresele) componentelor robotului ca sa le pot controla
        motor_l = sim.getObject('/PioneerP3DX/leftMotor')
        motor_r = sim.getObject('/PioneerP3DX/rightMotor')
        camera = sim.getObject('/PioneerP3DX/visionSensor')
        robot = sim.getObject('/PioneerP3DX')

        # Senzorii ultrasonici (fata, stanga, dreapta si diagonale)
        s_front = sim.getObject('/PioneerP3DX/sensor_front')
        s_left = sim.getObject('/PioneerP3DX/sensor_left')
        s_right = sim.getObject('/PioneerP3DX/sensor_right')
        s_diag_left = sim.getObject('/PioneerP3DX/sensor_diag_left')
        s_diag_right = sim.getObject('/PioneerP3DX/sensor_diag_right')
    except Exception as e:
        print(f"[EROARE INITIALIZARE] Nu gasesc robotul: {e}")
        return

    # Pornesc simularea
    sim.startSimulation()

    # 2. Initializare sisteme
    memorie_lista = memory.incarca_harta()  # Incarc ce a invatat robotul pana acum
    grid_map = config.genereaza_harta_L()  # Creez harta virtuala a laboratorului

    # Pornesc algoritmul A*
    my_planner = planner.AStarPlanner(grid_map, config.MAP_RESOLUTION, config.MAP_ORIGIN_X, config.MAP_ORIGIN_Y)

    # Pornesc sistemul vocal (aici se incarca modelul AI, dureaza putin)
    print("[MAIN] Incarc modulul vocal...")
    voice_bot = PoliNAVSystem()
    print("[MAIN] Sistem Gata. Apasa tasta 'N' ca sa ii dai o comanda.")

    # 3. Variabile de stare (ca sa stiu ce face robotul la un moment dat)
    stare = "EXPLORE"  # Incepe direct in modul de explorare
    current_path = []  # Aici tin lista de puncte pe unde trebuie sa mearga
    target_name = ""  # Numele destinatiei curente
    is_wall_following = False  # Variabila ca sa stiu daca ocolesc un obstacol

    # 4. Bucla principala (Ruleaza continuu cat timp merge programul)
    while True:
        # --- A. Citesc senzorii ---
        def read_prox(h):
            # Functie ajutatoare: daca senzorul nu vede nimic, returnez 10 metri (liber)
            res, dist, _, _, _ = sim.readProximitySensor(h)
            return dist if res > 0 else 10.0

        d_front = read_prox(s_front)
        d_l, d_r = read_prox(s_left), read_prox(s_right)
        d_dl, d_dr = read_prox(s_diag_left), read_prox(s_diag_right)
        sensors = (d_front, d_l, d_r, d_dl, d_dr)

        # Iau pozitia curenta a robotului (GPS)
        rx, ry, r_theta = control.get_robot_pose(sim, robot)

        # --- B. Procesare imagine ---
        img_raw, res = sim.getVisionSensorImg(camera)
        img_display = None
        if len(img_raw) > 0:
            # Daca camera merge, trimit imaginea la YOLO
            img_display = vision.process_camera(img_raw, res)

        # --- C. Verificare taste ---
        key = cv2.waitKey(1) & 0xFF

        # Daca apas N, robotul se opreste si asculta
        if key == ord('n'):
            print("\n[MAIN] STOP. Ascult comanda...")
            control.stop_robot(sim, motor_l, motor_r)  # Franez motoarele

            # Functia asta blocheaza programul pana cand termin de vorbit
            target_id = voice_bot.listen_and_decide(memorie_lista, rx, ry)

            if target_id:
                # Daca a inteles comanda si a gasit ID-ul
                tinte = [o for o in memorie_lista if o['id'] == target_id]
                if tinte:
                    tinta = tinte[0]
                    # Calculez drumul cu A*
                    path = my_planner.plan(rx, ry, tinta['x'], tinta['y'])
                    if path:
                        current_path = path
                        target_name = f"{tinta['tip']} #{tinta['id']}"
                        stare = "NAVIGATE"  # Trec in modul navigare
                        is_wall_following = False
                        print(f"[MAIN] Ruta calculata catre {target_name}!")
                    else:
                        print("[MAIN] Nu pot gasi drum catre tinta (e blocat?).")
            else:
                print("Cel mai probabil a fost o conversatie LLM.")

        # =========================================================
        # LOGICA PRINCIPALA (Ce face robotul in functie de stare)
        # =========================================================

        # CAZ 1: EXPLORE (Se plimba singur)
        if stare == "EXPLORE":
            # Folosesc algoritmul simplu de ocolire obstacole
            control.avoid_obstacles(sim, motor_l, motor_r, sensors)

            # Daca am imagine, caut obiecte
            if img_display is not None:
                obiecte_detectate = vision.detect_objects(img_display)

                for obj in obiecte_detectate:
                    nume_clasa = obj['name']
                    conf = obj['conf']
                    h_box = obj['box'][3]
                    raport_vizual = h_box / res[1]

                    # Filtrez obiectele care sunt prea departe sau nesigure
                    prag_vizual = config.VISUAL_MIN_HEIGHT.get(nume_clasa, config.VISUAL_MIN_HEIGHT['default'])
                    if conf > 0.60 and raport_vizual > prag_vizual:

                        # Estimez unde e obiectul pe harta
                        dist_estimata = 1.0
                        ox = rx + dist_estimata * math.cos(r_theta)
                        oy = ry + dist_estimata * math.sin(r_theta)

                        # Verific daca e un obiect nou sau unul vechi
                        memorie_lista, msg = memory.proceseaza_obiect(memorie_lista, nume_clasa, ox, oy)

                        # Salvez in fisier doar daca s-a schimbat ceva
                        if "NOU!" in msg or "Actualizat" in msg:
                            memory.salveaza_harta(memorie_lista)
                            if "NOU!" in msg:
                                print(f"--> {msg}")
                                # Desenez un cerc rosu pe ecran ca feedback
                                cv2.circle(img_display, (30, 30), 20, (0, 0, 255), -1)

        # CAZ 2: NAVIGATE (Merge la tinta)
        elif stare == "NAVIGATE":
            if len(current_path) > 0:
                nx, ny = current_path[0]  # Urmatorul punct unde trebuie sa ajung

                if not is_wall_following:
                    # Daca apare ceva brusc in fata, intru in mod de ocolire
                    if d_front < 0.6:
                        print("[NAV] Obstacol neasteptat! Incep ocolirea...")
                        is_wall_following = True
                    else:
                        # Merg spre punct
                        ajuns = control.navigate_to_point(sim, motor_l, motor_r, robot, nx, ny)
                        if ajuns:
                            current_path.pop(0)  # Scot punctul din lista daca am ajuns la el
                else:
                    # Sunt in mod de ocolire (Wall Follow)
                    control.follow_wall(sim, motor_l, motor_r, sensors)

                    # Verific daca am trecut de obstacol
                    angle_target = math.atan2(ny - ry, nx - rx)
                    diff = angle_target - r_theta
                    while diff > math.pi: diff -= 2 * math.pi
                    while diff < -math.pi: diff += 2 * math.pi

                    if abs(diff) < 0.5 and d_front > 1.0:
                        print("[NAV] Drum liber. Revin la A*.")
                        is_wall_following = False
            else:
                print(f"DESTINATIE ATINSA: {target_name}")
                control.stop_robot(sim, motor_l, motor_r)

                # Robotul spune vocal ca a ajuns
                voice_bot.speak("Am ajuns la destinatie.")

                stare = "EXPLORE"  # Ma intorc la explorare

        # Afisez imaginea de la camera cu starea curenta scrisa pe ea
        if img_display is not None:
            cv2.putText(img_display, f"Mod: {stare}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow("Robot Vision", img_display)

        # Iesire din program cu Q
        if key == ord('q'):
            break

    sim.stopSimulation()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()