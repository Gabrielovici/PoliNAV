from ultralytics import YOLO
import os


def main():
    print("=== START ANTRENARE YOLOv8 (MOD CPU) ===")

    # 1. Configurare Cale Absoluta
    current_dir = os.getcwd()
    yaml_path = os.path.join(current_dir, "dataset", "data.yaml")

    if not os.path.exists(yaml_path):
        print(f"[EROARE] Nu gasesc: {yaml_path}")
        return

    print(f"Configuratie: {yaml_path}")

    # 2. Incarcare Model
    model = YOLO('yolov8n.pt')

    # 3. Start Antrenament
    print("Incep antrenamentul pe PROCESOR (CPU)...")
    print("Va dura mai mult decat pe placa video. Ai rabdare.")

    try:
        results = model.train(
            data=yaml_path,
            epochs=100,  # Am redus la 50 pentru ca esti pe CPU (sa nu dureze o vesnicie)
            imgsz=640,
            plots=True,
            batch=8,  # Am redus batch-ul la 8 sa nu incarce memoria RAM
            device='cpu',  # <--- AICI ERA PROBLEMA. Am fortat CPU.
            workers=2  # Numar redus de procese paralele pentru stabilitate
        )

        print("\n---------------------------------------------------")
        print("ANTRENARE REUSITA!")
        print("Modelul tau se afla in folderul 'runs/detect/train/weights/best.pt'")
        print("---------------------------------------------------")

    except Exception as e:
        print(f"\n[EROARE]: {e}")


if __name__ == '__main__':
    from multiprocessing import freeze_support

    freeze_support()
    main()