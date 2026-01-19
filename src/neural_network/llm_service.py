import os
from llama_cpp import Llama
from . import voice_config as cfg


class LLMService:
    def __init__(self):
        if not os.path.exists(cfg.MODEL_PATH):
            raise FileNotFoundError(f"LIPSESTE MODELUL GGUF: {cfg.MODEL_PATH}")

        print("[LLM] Incarc modelul Qwen... (poate dura)")
        self.model = Llama(
            model_path=cfg.MODEL_PATH,
            n_ctx=2048,
            n_threads=6,
            verbose=False
        )
        print("[LLM] Model Incarcat.")

    def generate_response(self, user_text):
        """ Genereaza un raspuns scurt, conversational """
        prompt = f"""<|im_start|>system
Esti PoliNAV, un robot asistent, creeat de Gabriel Ciucă. Raspunde SCURT in romana.
<|im_end|>
<|im_start|>user
{user_text}
<|im_end|>
<|im_start|>assistant
"""
        try:
            output = self.model(
                prompt,
                max_tokens=25,
                stop=["<|im_end|>"],
                temperature=0.2,
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            return "Am o eroare la procesare."