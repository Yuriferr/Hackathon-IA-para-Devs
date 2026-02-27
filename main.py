import os
import base64
import json
import shutil
import tempfile
import uvicorn
from ultralytics import YOLO
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

# Carrega variáveis de ambiente (.env)
load_dotenv()

app = FastAPI(title="Diagram Analysis API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_icons(img_path, model_path):
    """
    Extrai ícones usando o modelo YOLO local.
    """
    print(f" > Iniciando detecção de ícones com YOLO...")
    try:
        model = YOLO(model_path)
        results = model(img_path, conf=0.6)
        
        icons_data = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                icons_data.append({
                    "object_type": class_name,
                    "box": box.xyxy[0].tolist(),
                    "confidence": float(box.conf[0])
                })
        print(f" > {len(icons_data)} ícones detectados.")
        return icons_data
    except Exception as e:
        print(f"Erro no YOLO: {e}")
        return []

def generate_stride_analysis(img_path, icons, metamodel_content=None):
    """
    Gera a análise STRIDE completa usando a LLM (Multimodal).
    Lê o texto da imagem e correlaciona com os ícones detectados em uma única chamada.
    Se houver metamodelo, usa para verificar conformidade.
    """
    print(f" > Enviando dados para análise STRIDE (LLM Ollama via LangChain)...")
    
    model_name = os.getenv("OLLAMA_MODEL", "gemini-3-flash-preview")

    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    icons_json = json.dumps(icons, indent=2)

    # Construção Dinâmica do Prompt
    metamodel_context = ""
    compliance_task = ""
    compliance_output_section = ""

    if metamodel_content:
        metamodel_context = f"""
        ### METAMODELO DE REFERÊNCIA (CONFORMIDADE):
        O usuário forneceu um padrão (Metamodelo) que deve ser seguido.
        
        CONTEÚDO DO METAMODELO:
        ---
        {metamodel_content}
        ---
        
        DIRETRIZES DE CONFORMIDADE:
        1. Compare o diagrama atual com o Metamodelo acima.
        2. Destaque o que está EM CONFORMIDADE (segue as regras).
        3. Aponte claramente desvios ou violações do metamodelo.
        """
        compliance_task = "- Analise a CONFORMIDADE com o Metamodelo fornecido."
        compliance_output_section = """
    ## Análise de Conformidade (Metamodelo)
    *Se houver metamodelo, cite o que está correto e o que desvia.*
    * **Em Conformidade**: ...
    * **Desvios/Atenção**: ...
    """

    # Prompt Otimizado
    prompt = f"""
    Atue como Especialista em AppSec. Analise a imagem do Diagrama de Fluxo de Dados (DFD).

    DADOS TÉCNICOS:
    - Ícones detectados (Bounding Boxes): {icons_json}
    - A imagem anexa contém as conexões visuais (setas/linhas) entre estes ícones.
    {metamodel_context}

    TAREFA:
    - Analise visualmente as setas para identificar os FLUXOS E RELACIONAMENTOS entre os componentes.
    - Identifique a direção do fluxo (Origem -> Destino) ou se é bidirecional (<->).
    {compliance_task}
    - Gere um relatório de ameaças STRIDE baseado nesses fluxos.

    SAÍDA OBRIGATÓRIA (Markdown sem numeração nos títulos):
    
    ## Mapeamento de Relacionamentos (Fluxos)
    Liste EXPLICITAMENTE as conexões no formato "ElementoA -> ElementoB":
    * **Fluxo**: [Tipo] NomeOrigem -> [Tipo] NomeDestino
    * ...

    {compliance_output_section}

    ## Matriz de Ameaças (STRIDE)
    | Componente/Fluxo | STRIDE | Ameaça Identificada | Impacto |
    | :--- | :---: | :--- | :--- |
    | ... | ... | ... | ... |

    ## Plano de Mitigação
    Liste as 3-5 correções prioritárias.
    """

    try:
        print(f" > Inferindo com o modelo Ollama local: {model_name}")
        llm = ChatOllama(model=model_name, temperature=0.1)
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{encoded_string}"}
                }
            ]
        )
        
        response = llm.invoke([message])
        return response.content
            
    except Exception as e:
        return f"Erro na requisição LLM (Ollama): {e}"

@app.post("/analyze")
async def analyze_diagram(file: UploadFile = File(...), metamodel: UploadFile = File(None)):
    temp_filename = None
    try:
        # 0. Processar Metamodelo (se houver)
        metamodel_content = None
        if metamodel:
            try:
                content = await metamodel.read()
                metamodel_content = content.decode("utf-8")
                print(" > Metamodelo recebido e lido.")
            except Exception as e:
                print(f" > Erro ao ler metamodelo: {e}")
                # Segue sem metamodelo se der erro na leitura

        # 1. Salvar arquivo temporário
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_filename = tmp.name
        
        # 2. Configuração
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "Treinamentos", "yolov8n_icons", "weights", "best.pt")
        
        if not os.path.exists(model_path):
            raise HTTPException(status_code=500, detail="Modelo YOLO não encontrado.")

        # 3. Execução Otimizada
        # A: Detectar ícones localmente
        icons = extract_icons(temp_filename, model_path)
        
        # B: Análise completa (OCR + STRIDE + COMPLIANCE)
        report = generate_stride_analysis(temp_filename, icons, metamodel_content)
        
        return JSONResponse(content={"report": report})
        
    except Exception as e:
        print(f"Erro: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
        
    finally:
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
