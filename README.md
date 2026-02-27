# 🛡️ Automated Threat Modeling with AI (STRIDE)

Este projeto foi desenvolvido como um MVP para a **FIAP Software Security**, visando otimizar a análise de vulnerabilidades em arquiteturas de sistemas utilizando Inteligência Artificial.

## 🎯 Objetivo do Desafio

A empresa tem como objetivo validar a viabilidade de uma nova funcionalidade: **realizar automaticamente a modelagem de ameaças baseada na metodologia STRIDE a partir de um diagrama de arquitetura de software (imagem).**

### Metas Alcançadas:
*   ✅ **Interpretação Automática**: IA capaz de identificar componentes arquiteturais (usuários, servidores, bancos de dados, APIs, etc) em imagens.
*   ✅ **Relatório STRIDE**: Geração automática de um relatório de ameaças categorizado.
*   ✅ **Dataset & Treinamento**: Construção e anotação de um dataset próprio para treinar um modelo supervisionado (YOLO) focado em ícones de diagramas.
*   ✅ **Sistema de Detecção**: API integrada que une Visão Computacional e LLMs para apontar vulnerabilidades e contramedidas.

---

## 🚀 Diferenciais do Projeto (Extras)

Além dos requisitos básicos, este projeto implementou funcionalidades avançadas pensando no uso corporativo real:

### 1. Modelo YOLO Customizado para Ícones
Desenvolvemos e treinamos um modelo **YOLOv8** específico para detectar ícones de arquitetura (AWS, Azure, GCP, Kubernetes, etc). 
*   *Vantagem*: Este modelo é modular e pode ser reutilizado em outros projetos de análise de diagramas, independente da geração de relatórios de segurança.

### 2. Validação via Metamodelo (Compliance) 🍒
Implementamos um recurso de "Cereja do Bolo": a capacidade de validar o diagrama contra um **Metamodelo Corporativo**.
*   *Como funciona*: O usuário pode fazer upload de um arquivo de regras (ex: `politica_seguranca.json`).
*   *Resultado*: A IA não apenas gera o STRIDE, mas cruza o diagrama com as regras da empresa, apontando conformidades e violações (ex: "Banco de dados exposto diretamente à internet viola a regra X").

### 3. Execução de Modelos LLM Locais (Ollama + LangChain) 🔒
Com foco na privacidade e segurança corporativa, o sistema foi migrado para utilizar o ecossistema **LangChain** executando modelos locais (via **Ollama**).
*   *Vantagem*: Os diagramas de arquitetura da empresa não precisam ser enviados para nuvens públicas ou APIs externas (como OpenAI ou Google). Todo o processamento OCR e análise de ameaças ocorre em infraestrutura própria, preservando a confidencialidade dos dados sensíveis.

### 4. API Simples e Direta (FastAPI)
Uma arquitetura leve utilizando **FastAPI**, focada em ser fácil de implantar e integrar com outros sistemas de CI/CD ou dashboards de segurança existentes.

---

## 🛠️ Como Usar

### Pré-requisitos
*   Python 3.8+
*   [Ollama](https://ollama.com/) instalado e rodando com um modelo multimodal (ex: `llava`, `llama3`).

### 1. Instalação e Configuração

Clone o repositório e instale as dependências:

```bash
# Clone o projeto
git clone [URL_DO_REPOSITORIO]
cd "Organizar Icones"

# Instale os requisitos
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto contendo o modelo do Ollama que você irá utilizar:

```env
OLLAMA_MODEL=gemini-3-flash-preview
```
*(Nota: Certifique-se de que o modelo especificado tenha sido puxado localmente rodando `ollama run <nome_do_modelo>`)*

### 2. Executando a Aplicação

Inicie o servidor da API:

```bash
python main.py
```
*O servidor iniciará em `http://localhost:8001`*

### 3. Utilizando o Frontend

1.  Abra o arquivo `frontend/index.html` em seu navegador.
2.  **Upload do Diagrama**: Clique no botão de imagem e selecione seu DFD/Diagrama.
3.  **Metamodelo (Opcional)**: Clique no botão flutuante (canto inferior direito) para anexar um arquivo de regras corporativas (ex: `exemplos/metamodelos/exemplo_metamodelo.json`).
4.  **Enviar**: Clique em enviar para receber a análise completa.

---

## 📂 Estrutura do Projeto

*   `main.py`: Core da aplicação (API FastAPI + Orquestração YOLO e LangChain).
*   `Treinamentos/`: Pesos do modelo YOLO treinado.
*   `frontend/`: Interface gráfica simples para interação.
*   `exemplos/`:
    *   `diagramas/`: Imagens de exemplo para teste.
    *   `metamodelos/`: Arquivos JSON/Txt com regras de exemplo para testes de conformidade.

---

## 🧠 Tecnologias Utilizadas

*   **YOLOv8 (Ultralytics)**: Detecção de Objetos (Ícones de arquitetura).
*   **LangChain & Ollama**: Orquestração do raciocínio de segurança e inferência na LLM local (garantindo privacidade).
*   **FastAPI**: Backend ágil para servir a IA.
*   **HTML/JS**: Frontend amigável e focado.

