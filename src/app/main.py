import time
import math
import cv2
import sys
import os

# Aici adaug calea principala ca sa pot importa fisierele mele din alte foldere
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# Import modulele
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
    sim.setStepping(False)  # Vreau timp real, nu frame cu frame

    try:
        # Iau controlul asupra pieselor robotului (motoare, senzori)
        motor_l = sim.getObject('/PioneerP3DX/leftMotor')
        motor_r = sim.getObject('/PioneerP3DX/rightMotor')
        camera = sim.getObject('/PioneerP3DX/visionSensor')
        robot = sim.getObject('/PioneerP3DX')

        # Iau handle-urile pentru senzori
        s_front = sim.getObject('/PioneerP3DX/sensor_front')
        s_left = sim.getObject('/PioneerP3DX/sensor_left')
        s_right = sim.getObject('/PioneerP3DX/sensor_right')
        s_diag_left = sim.getObject('/PioneerP3DX/sensor_diag_left')
        s_diag_right = sim.getObject('/PioneerP3DX/sensor_diag_right')
    except Exception as e:
        print(f"[EROARE INITIALIZARE] Nu gasesc robotul: {e}")
        return

    # Dau drumul la simulare
    sim.startSimulation()

    # 2. Initializare sisteme interne
    memorie_lista = memory.incarca_harta()  # Incarc ce a tinut minte pana acum
    grid_map = config.genereaza_harta_L()  # Creez harta laboratorului (matricea)

    # Pregatesc algoritmul de planificare A*
    my_planner = planner.AStarPlanner(grid_map, config.MAP_RESOLUTION, config.MAP_ORIGIN_X, config.MAP_ORIGIN_Y)

    # Incarc "creierul" vocal (aici dureaza putin pana incarca modelul AI)
    print("[MAIN] Incarc modulul vocal...")
    voice_bot = PoliNAVSystem()
    print("[MAIN] Sistem Gata. Apasa tasta 'N' pentru comanda vocala.")

    # 3. Variabile pe care le folosesc sa stiu starea robotului
    stare = "EXPLORE"  # Incep prin a ma plimba
    current_path = []  # Lista cu punctele pe unde trebuie sa merg
    target_name = ""  # Unde vreau sa ajung
    is_wall_following = False  # Daca sunt in modul de ocolire obstacol

    # 4. Bucla principala (Ruleaza la infinit cat timp merge programul)
    while True:
        # --- A. Citesc toti senzorii ---
        def read_prox(h):
            # Daca senzorul nu vede nimic, zic ca e liber (10 metri)
            res, dist, _, _, _ = sim.readProximitySensor(h)
            return dist if res > 0 else 10.0

        d_front = read_prox(s_front)
        d_l, d_r = read_prox(s_left), read_prox(s_right)
        d_dl, d_dr = read_prox(s_diag_left), read_prox(s_diag_right)
        sensors = (d_front, d_l, d_r, d_dl, d_dr)

        # Aflu unde sunt pe harta (GPS)
        rx, ry, r_theta = control.get_robot_pose(sim, robot)

        # --- B. Ma uit cu camera ---
        img_raw, res = sim.getVisionSensorImg(camera)
        img_display = None
        if len(img_raw) > 0:
            # Procesez imaginea pentru YOLO
            img_display = vision.process_camera(img_raw, res)

        # --- C. Verific daca am apasat ceva ---
        key = cv2.waitKey(1) & 0xFF

        # Cand apas N, opresc robotul si pornesc ascultarea
        if key == ord('n'):
            print("\n[MAIN] STOP. Ascult comanda...")
            control.stop_robot(sim, motor_l, motor_r)  # Frana

            # Aici programul asteapta pana termin de vorbit si proceseaza comanda
            target_id = voice_bot.listen_and_decide(memorie_lista, rx, ry)

            # --- FIX: Verificam cu 'is not None' ca sa mearga si pentru ID-ul 0 ---
            if target_id is not None:
                # Caut obiectul in memorie dupa ID
                tinte = [o for o in memorie_lista if o['id'] == target_id]
                if tinte:
                    tinta = tinte[0]
                    # Calculez traseul pana acolo
                    path = my_planner.plan(rx, ry, tinta['x'], tinta['y'])
                    if path:
                        current_path = path
                        target_name = f"{tinta['tip']} #{tinta['id']}"
                        stare = "NAVIGATE"  # Schimb modul in navigare
                        is_wall_following = False
                        print(f"[MAIN] Ruta calculata catre {target_name}!")
                    else:
                        print("[MAIN] Nu pot gasi drum catre tinta (e blocat?).")
                        voice_bot.speak("Nu pot calcula un drum pana acolo.")
            else:
                # Daca target_id e None, inseamna ca a fost doar chat sau am anulat
                print("[MAIN] Conversatie incheiata sau comanda anulata.")

        # =========================================================
        # MASINA DE STARI (Logica de comportament)
        # =========================================================

        # CAZ 1: EXPLORE (Ma plimb si caut obiecte)
        if stare == "EXPLORE":
            # Algoritm simplu sa nu dau in pereti
            control.avoid_obstacles(sim, motor_l, motor_r, sensors)

            # Daca vad ceva cu camera
            if img_display is not None:
                obiecte_detectate = vision.detect_objects(img_display)

                for obj in obiecte_detectate:
                    nume_clasa = obj['name']
                    conf = obj['conf']
                    h_box = obj['box'][3]
                    raport_vizual = h_box / res[1]

                    # Filtrez ce e departe sau nesigur
                    prag_vizual = config.VISUAL_MIN_HEIGHT.get(nume_clasa, config.VISUAL_MIN_HEIGHT['default'])
                    if conf > 0.60 and raport_vizual > prag_vizual:

                        # Calculez unde e obiectul pe harta
                        dist_estimata = 1.0
                        ox = rx + dist_estimata * math.cos(r_theta)
                        oy = ry + dist_estimata * math.sin(r_theta)

                        # Il bag in memorie sau il actualizez
                        memorie_lista, msg = memory.proceseaza_obiect(memorie_lista, nume_clasa, ox, oy)

                        # Daca e ceva nou, salvez fisierul JSON
                        if "NOU!" in msg or "Actualizat" in msg:
                            memory.salveaza_harta(memorie_lista)
                            if "NOU!" in msg:
                                print(f"--> {msg}")
                                # Desenez un cerc pe ecran sa vad ca l-a vazut
                                cv2.circle(img_display, (30, 30), 20, (0, 0, 255), -1)

        # CAZ 2: NAVIGATE (Am o tinta precisa)
        elif stare == "NAVIGATE":
            if len(current_path) > 0:
                nx, ny = current_path[0]  # Urmatorul pas

                if not is_wall_following:
                    # Daca imi sare ceva in fata, intru in ocolire
                    if d_front < 0.6:
                        print("[NAV] Obstacol neasteptat! Incep ocolirea...")
                        is_wall_following = True
                    else:
                        # Merg spre punct
                        ajuns = control.navigate_to_point(sim, motor_l, motor_r, robot, nx, ny)
                        if ajuns:
                            current_path.pop(0)  # Am ajuns aici, trec la urmatorul
                else:
                    # Ocolesc peretele (Wall Follow)
                    control.follow_wall(sim, motor_l, motor_r, sensors)

                    # Verific daca am scapat de obstacol si pot reveni la traseu
                    angle_target = math.atan2(ny - ry, nx - rx)
                    diff = angle_target - r_theta
                    while diff > math.pi: diff -= 2 * math.pi
                    while diff < -math.pi: diff += 2 * math.pi

                    if abs(diff) < 0.5 and d_front > 1.0:
                        print("[NAV] Drum liber. Revin la A*.")
                        is_wall_following = False
            else:
                # Lista e goala, deci am ajuns
                print(f"DESTINATIE ATINSA: {target_name}")
                control.stop_robot(sim, motor_l, motor_r)

                # Anunt vocal ca am ajuns
                voice_bot.speak("Am ajuns la destinatie.")

                stare = "EXPLORE"  # Ma intorc la explorare

        # Pun text pe imagine ca sa stiu in ce mod sunt
        if img_display is not None:
            cv2.putText(img_display, f"Mod: {stare}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow("Robot Vision", img_display)

        # Ies cu Q
        if key == ord('q'):
            break

    sim.stopSimulation()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()