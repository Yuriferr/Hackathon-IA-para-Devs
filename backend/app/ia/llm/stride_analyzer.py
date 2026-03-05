import os
import base64
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

class StrideAnalyzer:
       def analyze(self, img_path, prompt):
        """
        Gera a análise STRIDE completa usando a LLM (Multimodal).
        Lê o texto da imagem e correlaciona com os ícones detectados em uma única chamada.
        Se houver metamodelo, usa para verificar conformidade.
        """
        
        print(f" > Enviando dados para análise STRIDE (LLM Ollama via LangChain)...")
        model_name = os.getenv("OLLAMA_MODEL", "gemini-3-flash-preview:latest")

        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        try:
            print(f" > Inferindo com o modelo Ollama local: {model_name}")
            llm = ChatOllama(model=model_name, temperature=0.1)
            
            message = HumanMessage(
                content=[
                    {
                        "type": "text", 
                        "text": prompt
                    },
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