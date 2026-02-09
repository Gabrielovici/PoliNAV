import os
from llama_cpp import Llama
from.import voice_config as cfg

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

    def generate_response(self, user_text, context_info=None):

        full_system_prompt = cfg.LLM_SYSTEM_PROMPT #promptul din config

        # Construim formatul ChatML
        prompt = f"""<|im_start|>system
{full_system_prompt}
<|im_end|>
<|im_start|>user
{user_text}
<|im_end|>
<|im_start|>assistant
"""
        try:
            # Temperatura mica (0.1) pentru precizie maxima
            output = self.model(
                prompt,
                max_tokens=100,  # Limita stricta de lungime
                stop=["<|im_end|>"],
                temperature=0.1,
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            return "Am o eroare la procesare."