import math
import sys
import os

# Import config pentru viteze
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config.config as config

# Variabile globale pentru algoritmul de urmarire perete (PID)
last_error = 0
follow_side = 1  # 1 = Peretele e in Dreapta, -1 = Peretele e in Stanga


def get_robot_pose(sim, robot_handle):
    """
    Citeste senzorii GPS/Busola din simulator si returneaza pozitia X, Y si Unghiul.
    """
    pos = sim.getObjectPosition(robot_handle, -1)
    _, _, yaw = sim.getObjectOrientation(robot_handle, -1)
    return pos[0], pos[1], yaw


def stop_robot(sim, left_motor, right_motor):
    """
    Opreste robotul complet (Viteza 0).
    """
    sim.setJointTargetVelocity(left_motor, 0)
    sim.setJointTargetVelocity(right_motor, 0)


def avoid_obstacles(sim, left_motor, right_motor, sensors_data):
    """
    Algoritm "Braitenberg" simplu pentru explorare autonoma.
    Robotul fuge de obstacole cand senzorii detecteaza ceva aproape.
    """
    d_front, d_left, d_right, d_diag_l, d_diag_r = sensors_data
    vl, vr = config.VITEZA_BASE, config.VITEZA_BASE

    # REGULA 1: Daca e ceva in fata sau pe diagonale, ocolim
    if d_front < 0.6 or d_diag_l < 0.45 or d_diag_r < 0.45:
        # Alegem directia cu mai mult spatiu liber
        if d_left > d_right:
            vl, vr = -0.5, 0.5  # Rotire pe loc spre Stanga
        else:
            vl, vr = 0.5, -0.5  # Rotire pe loc spre Dreapta

    # REGULA 2: Daca suntem prea aproape de pereti laterali, ne distantam usor
    elif d_left < 0.4:
        vl, vr = 0.6, 0.4  # Viraj usor dreapta
    elif d_right < 0.4:
        vl, vr = 0.4, 0.6  # Viraj usor stanga

    # Trimitem vitezele calculate la motoare
    sim.setJointTargetVelocity(left_motor, vl)
    sim.setJointTargetVelocity(right_motor, vr)


def follow_wall(sim, left_motor, right_motor, sensors_data):
    """
    Algoritm PID avansat pentru a urmari conturul unui obstacol.
    Se activeaza cand Planner-ul (A*) esueaza sau intalneste un obstacol neasteptat.
    """
    global last_error, follow_side

    d_front, d_left, d_right, d_diag_l, d_diag_r = sensors_data

    # Distanta pe care incercam sa o mentinem fata de perete
    TARGET_DIST = 0.50
    BASE_SPEED = config.VITEZA_BASE

    # Coeficienti PID (Tuned manual)
    Kp = 2.0  # Cat de agresiv reactioneaza la eroare
    Kd = 1.5  # Cat de repede reactioneaza la schimbarea erorii

    # 1. Decidem pe ce parte e peretele (doar daca avem obstacol in fata)
    if d_front < 0.7:
        if d_left > d_right:
            follow_side = 1  # Perete pe dreapta (sens trigonometric invers)
        else:
            follow_side = -1  # Perete pe stanga

    # 2. Urgenta: Daca suntem in colt, rotim pe loc
    if d_front < 0.6:
        if follow_side == 1:
            sim.setJointTargetVelocity(left_motor, -0.5)
            sim.setJointTargetVelocity(right_motor, 0.8)
        else:
            sim.setJointTargetVelocity(left_motor, 0.8)
            sim.setJointTargetVelocity(right_motor, -0.5)
        last_error = 0
        return

    # 3. Calculam distanta curenta pana la perete
    if follow_side == 1:
        dist_to_wall = min(d_right, d_diag_r)
    else:
        dist_to_wall = min(d_left, d_diag_l)

    # 4. Cazul in care am pierdut peretele (colt exterior) -> Facem o curba larga
    if dist_to_wall > 1.2:
        if follow_side == 1:
            sim.setJointTargetVelocity(left_motor, BASE_SPEED)
            sim.setJointTargetVelocity(right_motor, BASE_SPEED * 0.5)
        else:
            sim.setJointTargetVelocity(left_motor, BASE_SPEED * 0.5)
            sim.setJointTargetVelocity(right_motor, BASE_SPEED)
        last_error = 0
        return

    # 5. Calculul Erorii si PID
    error = TARGET_DIST - dist_to_wall
    derivative = error - last_error
    turn_adjustment = (Kp * error) + (Kd * derivative)

    # 6. Aplicam corectia la vitezele motoarelor
    if follow_side == 1:
        vl = BASE_SPEED - turn_adjustment
        vr = BASE_SPEED + turn_adjustment
    else:
        vl = BASE_SPEED + turn_adjustment
        vr = BASE_SPEED - turn_adjustment

    # 7. Limitam vitezele (Saturatie) pentru a nu arde motoarele simulate
    vl = max(min(vl, 3.0), 0.1)
    vr = max(min(vr, 3.0), 0.1)

    sim.setJointTargetVelocity(left_motor, vl)
    sim.setJointTargetVelocity(right_motor, vr)

    last_error = error


def navigate_to_point(sim, left_motor, right_motor, robot_handle, target_x, target_y):
    """
    Controler Proportional pentru a naviga de la A la B in linie dreapta.
    Folosit de Planner pentru a executa pasii din A*.
    Returneaza True cand a ajuns.
    """
    # Obtinem pozitia curenta
    rx, ry, ryaw = get_robot_pose(sim, robot_handle)

    # Calculam distanta pana la tinta
    dist = math.sqrt((target_x - rx) ** 2 + (target_y - ry) ** 2)

    # Calculam unghiul catre tinta
    angle_to_target = math.atan2(target_y - ry, target_x - rx)

    # Calculam diferenta de unghi (Eroarea de orientare)
    angle_diff = angle_to_target - ryaw

    # Normalizam unghiul intre -PI si +PI
    while angle_diff > math.pi: angle_diff -= 2 * math.pi
    while angle_diff < -math.pi: angle_diff += 2 * math.pi

    # Verificam daca am ajuns
    if dist < config.TOLERANTA_TINTA:
        return True

    # Logica de miscare
    if abs(angle_diff) > 0.45:
        # Daca robotul nu se uita spre tinta, se roteste pe loc
        turn_speed = 1.0
        if angle_diff > 0:
            vl, vr = -turn_speed, turn_speed
        else:
            vl, vr = turn_speed, -turn_speed
    else:
        # Daca se uita spre tinta, inainteaza si corecteaza fin directia
        speed = config.VITEZA_BASE
        k_turn = 2.0  # Factor de corectie
        vl = speed - (angle_diff * k_turn)
        vr = speed + (angle_diff * k_turn)

    sim.setJointTargetVelocity(left_motor, vl)
    sim.setJointTargetVelocity(right_motor, vr)
    return False