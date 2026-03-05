from ultralytics import YOLO
import os
import torch

# Configuração de dispositivo (GPU se disponível). Sendo assim, fica agnóstico para o ambiente de cada um.
def get_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"

if __name__ == '__main__':
    # Carrega modelo
    model = YOLO("yolov8n.pt") 

    # seleciona do device disponível (GPU > MPS > CPU)
    device = get_device()
    print(f"Using device: {device}")

    # Configurações de diretórios
    BASE_DIR = os.path.dirname(__file__) 
    dataset_path = os.path.join(BASE_DIR, "..", "database", "dataset_yolo", "data.yaml")
    training_dir = os.path.join(BASE_DIR, "Treinamentos")
    
    results = model.train(
        data=dataset_path,
        project=training_dir,
        name="yolov8n_icons",
        
        # --- ESTRATÉGIA DE TREINO ---
        imgsz=640,          
        epochs=120,        # Para 8000 imagens, 100 épocas é um bom número inicial.
        patience=20,       # Se não melhorar em 15 épocas, ele para (economiza tempo).
        
        # --- AUGMENTATION (Mosaic e Scale Ativados) ---
        mosaic=1.0,         # Mistura 4 imagens em 1 (CRUCIAL para variedade)
        scale=0.6,          # Zoom in/out agressivo (0.6 = +/- 60% de zoom)
        
        # --- Outras Augmentations ---
        degrees=10.0,       # Rotação
        mixup=0.15,         # Transparência
        copy_paste=0.3,     # Recorte e cola
        close_mosaic=10,    # Desliga mosaic no fim para refinar
        
        # --- Ajustes de Cor ---
        hsv_h=0.015,        # Matiz conservador
        hsv_s=0.8,          # Saturação agressiva (para ícones 'lavados')
        hsv_v=0.4,          # Brilho
        
        # --- Otimização ---
        batch=-1,           # AutoBatch
        device=device,      # Usa GPU se disponível
        workers=4,          # Aumentei workers para dar conta de carregar 8000 imagens rápido
        cache=True,         # Usa cache RAM/Disco para acelerar
        amp=True,
        
        optimizer='AdamW',
        exist_ok=True
    )
    
    print("✅ Treinamento concluído!")