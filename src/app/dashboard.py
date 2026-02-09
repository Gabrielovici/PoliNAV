import streamlit as st
import cv2
import threading
import time
import sys
import os
import queue

# --- SETUP CĂI ---
# Adăugăm calea ca să putem importa modulele tale existente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Importăm modulele tale (Backend-ul)
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import config.config as config
import src.app.vision_handler as vision
import src.app.control as control
import src.app.memory as memory
import src.app.planner as planner
from src.neural_network.voice_engine import PoliNAVSystem

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(
    page_title="PoliNAV Control Center",
    page_icon="🤖",
    layout="wide"
)


# --- CLASA ROBOT (BACKGROUND THREAD) ---
# Aceasta rulează logica din main.py, dar în fundal
class RobotThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = False
        self.sim_connected = False
        self.current_frame = None
        self.logs = []
        self.robot_state = "IDLE"
        self.target_name = "Niciuna"

        # Coada pentru comenzi de la UI la Robot
        self.command_queue = queue.Queue()

    def add_log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.logs.insert(0, f"[{timestamp}] {text}")  # Adaugam la inceput
        if len(self.logs) > 10: self.logs.pop()  # Pastram doar ultimele 10

    def run(self):
        self.running = True
        self.add_log("Conectare la Simulator...")

        # 1. INITIALIZARE (Copiat din main.py)
        client = RemoteAPIClient()
        sim = client.require('sim')
        sim.setStepping(False)

        try:
            # Handle-uri
            self.motor_l = sim.getObject('/PioneerP3DX/leftMotor')
            self.motor_r = sim.getObject('/PioneerP3DX/rightMotor')
            self.camera = sim.getObject('/PioneerP3DX/visionSensor')
            self.robot = sim.getObject('/PioneerP3DX')
            # ... (restul senzorilor)

            sim.startSimulation()
            self.sim_connected = True
            self.add_log("Simulator Conectat!")
        except Exception as e:
            self.add_log(f"Eroare Conectare: {e}")
            self.running = False
            return

        # Initializare AI
        self.add_log("Încărcare Module AI...")
        # voice_bot = PoliNAVSystem() # Decomenteaza cand vrei voce
        self.add_log("AI Online.")

        # 2. BUCLA PRINCIPALA
        while self.running:
            # A. Procesare Video
            img_raw, res = sim.getVisionSensorImg(self.camera)
            if len(img_raw) > 0:
                img_display = vision.process_camera(img_raw, res)

                # Detectie (Optional, poti comenta pentru viteza)
                # obiecte = vision.detect_objects(img_display)

                # Salvam imaginea pentru a fi afisata in UI
                # Convertim din BGR (OpenCV) in RGB (Streamlit)
                self.current_frame = cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB)

            # B. Verificam Comenzi din UI
            if not self.command_queue.empty():
                cmd = self.command_queue.get()
                self.add_log(f"Comanda primita: {cmd}")
                if cmd == "STOP":
                    control.stop_robot(sim, self.motor_l, self.motor_r)
                    self.robot_state = "OPRIT"
                # Aici poti adauga logica de navigare manuala

            time.sleep(0.05)  # Pauza mica sa nu fiarba procesorul

        # La final
        sim.stopSimulation()
        self.add_log("Simulare Oprită.")


# --- INTERFATA STREAMLIT (FRONTEND) ---

# 1. Gestionare Sesiune (Singleton)
if 'robot_thread' not in st.session_state:
    st.session_state.robot_thread = None

st.title("🤖 PoliNAV - Panou de Comandă")

# 2. Sidebar - Controale
with st.sidebar:
    st.header("Control Sistem")

    if st.button("🔌 CONECTEAZĂ & PORNEȘTE", type="primary"):
        if st.session_state.robot_thread is None:
            thread = RobotThread()
            thread.start()
            st.session_state.robot_thread = thread
            st.success("Sistem Pornit!")

    if st.button("🛑 STOP URGENȚĂ"):
        if st.session_state.robot_thread:
            st.session_state.robot_thread.command_queue.put("STOP")

    st.markdown("---")
    st.subheader("Stare Curentă")

    # Placeholder pentru metrici live
    status_text = st.empty()
    target_text = st.empty()

# 3. Zona Principală
col_video, col_logs = st.columns([2, 1])

with col_video:
    st.subheader("Flux Video Live (YOLO)")
    video_placeholder = st.empty()

with col_logs:
    st.subheader("Jurnal AI (LLM & System)")
    log_placeholder = st.empty()

# 4. Bucla de Actualizare UI
# Streamlit ruleaza asta o data. Ca sa avem video live, facem un loop aici.
if st.session_state.robot_thread and st.session_state.robot_thread.is_alive():
    try:
        while True:
            thread = st.session_state.robot_thread

            # Actualizare Video
            if thread.current_frame is not None:
                video_placeholder.image(thread.current_frame, channels="RGB", use_column_width=True)

            # Actualizare Logs
            log_text = "\n".join(thread.logs)
            log_placeholder.text_area(
                "Logs",
                value=log_text,
                height=400,
                key=f"log_{time.time()}"
            )

            # Actualizare Sidebar
            status_text.info(f"Mod: {thread.robot_state}")
            target_text.warning(f"Tinta: {thread.target_name}")

            time.sleep(0.1)  # Refresh rate UI (10 FPS)
    except Exception as e:
        st.error(f"Eroare UI: {e}")