import os
import sys
import base64
import json
import requests
import pytesseract
from PIL import Image
from ultralytics import YOLO
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

# --- Configuração do Caminho do Tesseract (Caso necessário, descomente e ajuste) ---
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_icons(img_path, model_path):
    """
    Função 1: Extrai ícones usando o modelo YOLO.
    Retorna a lista de bounding boxes, pois o modelo só detecta a categoria genérica 'icon'.
    """
    print(f" > Iniciando detecção de ícones com YOLO...")
    try:
        model = YOLO(model_path)
        # Confiança 0.6 para filtrar falsos positivos
        results = model(img_path, conf=0.6)
        
        icons_data = []
        for result in results:
            for box in result.boxes:
                # O modelo customizado retorna tudo como classe 'icon', então salvamos a posição
                # para ajudar a LLM a localizar se necessário, ou apenas confirmar a existência.
                icons_data.append({
                    "box": box.xyxy[0].tolist(), # Coordenadas [x1, y1, x2, y2]
                    "confidence": float(box.conf[0])
                })
        print(f" > {len(icons_data)} ícones detectados.")
        return icons_data
    except Exception as e:
        print(f"Erro no YOLO: {e}")
        return []

def extract_text(img_path):
    """
    Função 2: Extrai texto da imagem usando Pytesseract.
    """
    print(f" > Iniciando extração de texto com OCR...")
    try:
        image = Image.open(img_path)
        # Tenta extrair em Português e Inglês
        text = pytesseract.image_to_string(image, lang='por+eng')
        print(f" > Texto extraído ({len(text)} caracteres).")
        return text.strip()
    except Exception as e:
        print(f"Erro no Tesseract: {e}")
        print("DICA: Verifique se o Tesseract-OCR está instalado no Windows e no PATH.")
        return ""

def generate_stride_report(img_path, icons, text):
    """
    Função 3: Envia a imagem + dados para a LLM gerar o relatório STRIDE.
    Usa OpenRouter (Gemini 2.0 Flash) com capacidade visual para identificar os ícones.
    """
    print(f" > Enviando dados para a LLM (OpenRouter)...")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERRO: OPENROUTER_API_KEY não encontrada no .env")
        return

    # Codificar imagem em base64 para a LLM ver o diagrama e identificar os ícones
    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    prompt = f"""
    Atue como um Especialista em Segurança de Software.
    
    Analise o Diagrama de Fluxo de Dados (DFD) fornecido nesta imagem.
    
    METADADOS EXTRAÍDOS AUTOMATICAMENTE:
    1. OCR (Texto Detectado):
    {text}
    
    2. VISÃO COMPUTACIONAL:
    Detectamos {len(icons)} elementos gráficos marcados como ícones/nós no diagrama.
    Como o modelo de deteção apenas identifica que "existe um ícone", VOCÊ DEVE IDENTIFICAR VISUALMENTE O QUE CADA ÍCONE REPRESENTA (ex: Banco de Dados, Usuário, Celular, Nuvem AWS, Servidor, etc) olhando para a imagem.
    
    TAREFA:
    Gere um Relatório de Modelagem de Ameaças usando a metodologia STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).
    
    O relatório deve ser SIMPLES, DIRETO e em PORTUGUÊS.
    Estrutura:
    - Lista de Componentes Identificados (Baseado na sua visão e no texto).
    - Análise STRIDE (Para cada letra, liste 1 ou 2 ameaças principais para este cenário).
    - Mitigações Recomendadas (Resumidas).
    """

    # Payload para OpenRouter (Compatível com OpenAI Vision / Gemini Vision)
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.0-flash-001", # Modelo multimodal rápido e barato
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_string}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result:
            content = result['choices'][0]['message']['content']
            
            # Salvar relatório
            output_file = "Relatorio_STRIDE.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"\nRELATÓRIO GERADO COM SUCESSO!\nSalvo em: {output_file}")
            print("-" * 30)
            print(content)
        else:
            print(f"Erro na resposta da API: {result}")
            
    except Exception as e:
        print(f"Erro na requisição LLM: {e}")

def main():
    # Caminhos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "Treinamentos", "yolov8n_icons", "weights", "best.pt")
    img_path = os.path.join(base_dir, "diagramas", "aws_diagrama.png") # Ajuste conforme necessário
    
    if not os.path.exists(model_path):
        print("Modelo não encontrado.")
        return
    if not os.path.exists(img_path):
        print("Imagem não encontrada.")
        return

    # 1. Extrair Ícones
    icons = extract_icons(img_path, model_path)
    
    # 2. Extrair Texto
    text = extract_text(img_path)
    
    # 3. Gerar Relatório
    generate_stride_report(img_path, icons, text)

if __name__ == "__main__":
    main()
