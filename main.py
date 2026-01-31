import os
import cv2
import base64
import numpy as np
from ultralytics import YOLO
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure OpenRouter (via OpenAI SDK)
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

def encode_cv2_image(cv2_img):
    """Encodes a CV2 image (numpy array) to base64 string."""
    _, buffer = cv2.imencode('.jpg', cv2_img)
    return base64.b64encode(buffer).decode('utf-8')

def detect_and_crop_components(image_path, model_path, conf_threshold=0.75):
    """
    Detects components using YOLO, CROPS them, and returns a list of base64 encoded images.
    Returns: (list_of_base64_strings, count)
    """
    print(f"[INFO] Loading YOLO model from {model_path}...")
    model = YOLO(model_path)
    
    print(f"[INFO] Predicting on {image_path} with conf > {conf_threshold}...")
    # Load original image for cropping
    original_img = cv2.imread(image_path)
    if original_img is None:
        raise ValueError(f"Could not load image from {image_path}")
        
    results = model(image_path, conf=conf_threshold, verbose=False)
    
    cropped_images_b64 = []
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Get coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            
            # Crop the icon
            # Ensure coordinates are within bounds
            h, w, _ = original_img.shape
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            if x2 > x1 and y2 > y1:
                crop = original_img[y1:y2, x1:x2]
                
                # Check if crop is valid
                if crop.size > 0:
                    b64_str = encode_cv2_image(crop)
                    cropped_images_b64.append(b64_str)
    
    count = len(cropped_images_b64)
    print(f"[INFO] Extracted {count} valid icon crops.")
    return cropped_images_b64, count

def analyze_stride_icons(icon_images_b64):
    """
    Sends MULTIPLE icon images to OpenRouter for identification and STRIDE.
    """
    print(f"[INFO] Sending {len(icon_images_b64)} icons to OpenRouter (google/gemini-2.0-flash-001)...")
    
    # Construct the message content
    content_payload = [
        {
            "type": "text",
            "text": f"""
            Você é um Especialista em Segurança focado em Modelagem de Ameaças usando a metodologia STRIDE.
            
            Abaixo eu forneço **{len(icon_images_b64)} imagens recortadas** individualmente de um diagrama de sistema. Cada imagem contém UM único componente/ícone (ex: um servidor, um banco de dados, um usuário, um firewall, etc).
            
            **Sua Tarefa:**
            1.  **IDENTIFICAÇÃO DE COMPONENTES**: Analise cada imagem individualmente e identifique qual tecnologia ou componente ela representa.
            2.  **INFERÊNCIA DE ARQUITETURA**: Com base na lista de componentes identificados, tente deduzir qual seria a arquitetura provável desse sistema (ex: se você vê um "AWS Cloud" e um "EC2", é uma arquitetura AWS).
            3.  **ANÁLISE STRIDE**: Realize uma análise de ameaças STRIDE para o sistema como um todo, considerando esses componentes.
            4.  **MITIGAÇÃO**: Forneça mitigações para cada ameaça.
            
            Formate a saída como um relatório em CORPO DE TEXTO (não markdown):
            
            RELATÓRIO DE ANÁLISE DE AMEAÇAS STRIDE (BASEADO EM ÍCONES)
            
            COMPONENTES IDENTIFICADOS:
            - Ícone 1: [O que você vê?]
            - Ícone 2: [O que você vê?]
            ... (liste todos)
            
            VISÃO GERAL DO SISTEMA (Inferida)
            ...
            
            AMEAÇAS IDENTIFICADAS (STRIDE)
            Categoria: ...
            Componente Afetado: ...
            Descrição: ...
            Mitigação: ...
            --------------------------------------------------
            
            CONCLUSÃO
            ...
            """
        }
    ]
    
    # Append all images to the payload
    for i, b64_img in enumerate(icon_images_b64):
        content_payload.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64_img}",
                "detail": "low" # Use low detail to save tokens/latency if images are small crops
            }
        })
    
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://antigravity.ai", 
                "X-Title": "Antigravity Agent", 
            },
            model="google/gemini-2.0-flash-001",
            messages=[
                {
                    "role": "user",
                    "content": content_payload
                }
            ]
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"[ERROR] OpenRouter API Error: {e}")
        # Identify if payload was too large
        if "413" in str(e) or "too large" in str(e).lower():
            print("[HINT] The payload with all images might be too large for the API.")
        raise e

def main():
    # Configuration
    MODEL_PATH = r"C:\Projetos\Organizar Icones\Treinamentos\yolov8n_icons\weights\best.pt"
    # Default image
    IMAGE_PATH = r"C:\Projetos\Organizar Icones\diagramas\aws_diagrama.png"
    
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Model not found at {MODEL_PATH}")
        return

    if not os.path.exists(IMAGE_PATH):
        print(f"[ERROR] Image not found at {IMAGE_PATH}")
        return

    try:
        # 1. Detect and Crop
        icon_images, count = detect_and_crop_components(IMAGE_PATH, MODEL_PATH, conf_threshold=0.75)
        
        if count == 0:
            print("[WARN] No icons detected to analyze.")
            return

        # 2. Analyze Icons with LLM
        # Limit to first 20 icons to avoid context window explosion in testing, if needed
        # But user asked for "all", so let's try all.
        print(f"[INFO] Analyzable components: {count}")
        
        report = analyze_stride_icons(icon_images)
        
        print("\n" + "="*50)
        print("REPORT GENERATED")
        print("="*50 + "\n")
        print(report)
        
        # Save report
        with open("stride_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n[INFO] Report saved to stride_report.txt")
        
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
