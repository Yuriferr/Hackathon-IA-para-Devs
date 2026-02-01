# Automatic Threat Modeling (STRIDE)

Este projeto automatiza a criação de relatórios de modelagem de ameaças (Threat Modeling) usando a metodologia **STRIDE**. 

O sistema analisa imagens de Diagramas de Fluxo de Dados (DFD), detecta elementos visualmente e gera um relatório profissional de segurança.

## 🚀 Funcionalidades

- **Detecção de Ícones**: Utiliza um modelo **YOLOv8** treinado para localizar nós e componentes na imagem.
- **Extração de Texto (OCR)**: Utiliza **Tesseract** para ler rótulos e anotações do diagrama.
- **Análise com IA**: Envia os dados visuais + texto para uma LLM (via **OpenRouter**) que interpreta a arquitetura e gera o relatório STRIDE em Português.

## 📋 Pré-requisitos

- Python 3.8+
- [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado no sistema (Windows).
- Uma chave de API do [OpenRouter](https://openrouter.ai/).

## 🛠️ Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-projeto.git
   cd seu-projeto
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure o arquivo `.env`:
   Crie um arquivo `.env` na raiz e adicione sua chave.
   ```env
   OPENROUTER_API_KEY=sua_chave_aqui
   ```

## ⚙️ Como Usar

1. Coloque a imagem do seu diagrama na pasta `diagramas/` (ou ajuste o caminho no `main.py`).
2. Execute o script principal:
   ```bash
   python main.py
   ```
3. O relatório será gerado na raiz do projeto com o nome `Relatorio_STRIDE.txt`.

## 📂 Estrutura do Projeto

- `main.py`: Script principal contendo toda a lógica (YOLO, OCR, LLM).
- `Treinamentos/`: Contém os pesos do modelo YOLO (`best.pt`).
- `diagramas/`: Pasta para armazenar as imagens a serem analisadas.
- `requirements.txt`: Lista de dependências Python.

## 📝 Licença

Este projeto é de código aberto e está disponível sob a licença [MIT](LICENSE).
