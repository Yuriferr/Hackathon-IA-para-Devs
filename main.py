import os
import sys
import base64
import json
import requests
import pytesseract
import shutil
from PIL import Image
from ultralytics import YOLO
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import tempfile

# Carrega variáveis de ambiente (.env)
load_dotenv()

# --- Configuração do Caminho do Tesseract (Caso necessário, descomente e ajuste) ---
# --- Configuração do Caminho do Tesseract (Opcional - O código agora usa Fallback para LLM) ---
# Se você tiver o Tesseract instalado, aponte o caminho aqui:
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

app = FastAPI(title="Diagram Analysis API")

# Configurar CORS para permitir que o frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique a origem do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_icons(img_path, model_path):
    """
    Função 1: Extrai ícones usando o modelo YOLO.
    Retorna a lista de bounding boxes.
    """
    print(f" > Iniciando detecção de ícones com YOLO...")
    try:
        model = YOLO(model_path)
        # Confiança 0.6 para filtrar falsos positivos
        results = model(img_path, conf=0.6)
        
        icons_data = []
        for result in results:
            for box in result.boxes:
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
    print(f" > Iniciando extração de texto (OCR)...")
    try:
        image = Image.open(img_path)
        # Tenta extrair em Português e Inglês
        text = pytesseract.image_to_string(image, lang='por+eng')
        print(f" > Texto extraído ({len(text)} caracteres).")
        return text.strip()
    except Exception:
        print(f" > Aviso: OCR local (Tesseract) indisponível. A leitura será feita pela LLM.")
        return ""

def generate_stride_report_content(img_path, icons, text):
    """
    Função 3: Envia a imagem + dados para a LLM gerar o relatório STRIDE.
    Retorna o conteúdo do relatório como string.
    """
    print(f" > Enviando dados para a LLM (OpenRouter)...")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "ERRO: OPENROUTER_API_KEY não encontrada no .env"

    # Codificar imagem em base64 para a LLM
    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    prompt = f"""
    Atue como um Especialista Sênior em Segurança de Aplicações (AppSec).
    
    CONTEXTO:
    Você receberá um Diagrama de Fluxo de Dados (DFD). Sua missão é identificar vulnerabilidades de segurança utilizando a metodologia STRIDE.
    
    DADOS DE ENTRADA (Auxiliares):
    - Texto lido via OCR: {text if text else "Indisponível (Realize a leitura visualmente da imagem)"}
    - Elementos gráficos detectados: {len(icons)} (Use estes boxes apenas como dica de onde olhar, mas identifique o componente visualmente).
    
    DIRETRIZES GERAIS:
    1. Identifique corretamente os limites de confiança (Trust Boundaries).
    2. Analise o fluxo dos dados entre os componentes.
    3. Seja técnico, mas conciso.
    
    FORMATO DE SAÍDA OBRIGATÓRIO (MARKDOWN):
    
    ## 1. Mapeamento do Diagrama
    *Listagem breve do que foi identificado na imagem.*
    * **Componentes**: (Ex: Banco de Dados, Web App, Usuário)
    * **Fluxos de Dados**: (Ex: HTTPS Request, Query SQL)
    * **Limites de Confiança**: (Ex: Internet vs VPC)

    ## 2. Matriz de Ameaças (STRIDE)
    *Gere obrigatoriamente uma tabela com as principais ameaças.*
    
    | Componente | Categoria (STRIDE) | Descrição da Ameaça | Impacto |
    | :--- | :---: | :--- | :--- |
    | (Nome do Componente) | (S/T/R/I/D/E) | (Explicação breve do ataque) | (Ex: Vazamento de dados) |
    *(Adicione quantas linhas forem necessárias para cobrir as ameaças críticas)*

    ## 3. Plano de Mitigação Prioritário
    *Liste as 3 a 5 correções mais urgentes baseadas na matriz acima.*
    1. **[Mitigação para X]**: Descrição da ação corretiva.
    2. ...
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.0-flash-001",
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
            return content
        else:
            return f"Erro na resposta da API: {result}"
            
    except Exception as e:
        return f"Erro na requisição LLM: {e}"

@app.post("/analyze")
def analyze_diagram(file: UploadFile = File(...)):
    temp_filename = None
    try:
        # 1. Salvar arquivo em diretório temporário seguro (evita reload do frontend se estiver assistindo raiz)
        # delete=False pois precisamos passar o caminho para o YOLO/Tesseract
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_filename = tmp.name
        
        # 2. Caminhos
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "Treinamentos", "yolov8n_icons", "weights", "best.pt")
        
        if not os.path.exists(model_path):
            raise HTTPException(status_code=500, detail="Modelo YOLO não encontrado.")

        # 3. Processamento
        icons = extract_icons(temp_filename, model_path)
        text = extract_text(temp_filename)
        report = generate_stride_report_content(temp_filename, icons, text)
        
        return JSONResponse(content={"report": report})
        
    except Exception as e:
        print(f"Erro no processamento: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
        
    finally:
        # 4. Limpeza garantida
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception as cleanup_error:
                print(f"Erro ao remover arquivo temporário: {cleanup_error}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

