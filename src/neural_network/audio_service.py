import speech_recognition as sr
import pygame
import requests
import time
import os
from . import voice_config as cfg


class AudioService:
    def __init__(self):
        print("[AUDIO] Initializare Microfon si Boxe...")

        # Init Mixer (Output)
        try:
            pygame.mixer.init()
        except:
            print("[AUDIO ERROR] Nu pot initia PyGame Mixer.")

        # Init Recognizer (Input)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Calibrare setari
        self.recognizer.energy_threshold = cfg.MIC_ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = cfg.MIC_PAUSE_THRESHOLD

    def listen(self):
        print("\n ASCULT... (Vorbeste acum)")
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source, timeout=cfg.MIC_TIMEOUT, phrase_time_limit=cfg.MIC_PHRASE_LIMIT)
                print(" Transcriu...")
                text = self.recognizer.recognize_google(audio, language=cfg.LANGUAGE)
                print(f" Am auzit: '{text}'")
                return text
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except Exception as e:
                print(f"[AUDIO ERROR] {e}")
                return None

    def speak(self, text):
        """ Transforma text in sunet (TTS) si il reda """
        if not text: return
        print(f"[VOCE] {text}")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{cfg.VOICE_ID}"
        headers = {
            "xi-api-key": cfg.ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5}
        }

        try:
            r = requests.post(url, json=payload, headers=headers)
            if r.status_code == 200:
                with open(cfg.AUDIO_OUTPUT_FILE, 'wb') as f:
                    f.write(r.content)
                self._play_file(cfg.AUDIO_OUTPUT_FILE)
            else:
                print(f"[TTS ERROR] API Code: {r.status_code}")
        except Exception as e:
            print(f"[TTS ERROR] {e}")

    def _play_file(self, filename):
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except:
            pass