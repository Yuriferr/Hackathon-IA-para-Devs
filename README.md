# 🛡️ Modelagem de Ameaças Utilizando IA

Este projeto foi desenvolvido como **desafio da pós-graduação** para a **FIAP IA para Devs**. O objetivo principal é validar a viabilidade de uma nova funcionalidade corporativa: otimizar a análise de vulnerabilidades em arquiteturas de sistemas utilizando Inteligência Artificial.

## 📋 Resumo

O projeto consiste no desenvolvimento de um **MVP (Produto Mínimo Viável)** corporativo robusto para detecção supervisionada de ameaças em arquiteturas. O sistema atua recebendo um diagrama de arquitetura de software (imagem) e executa automaticamente as seguintes etapas:
1. **Interpretação Automática do Diagrama**: Identifica de maneira visual os componentes de arquitetura presentes (usuários, servidores, bancos de dados, APIs, provedores Cloud, etc.) utilizando nosso modelo de Visão Computacional de detecção de objetos.
2. **Análise de Fluxos e Vulnerabilidades**: O sistema analisa visualmente as conexões (setas) para mapear o fluxo de dados, interpretando como cada componente interage e em qual direção.
3. **Relatório STRIDE**: Gera automaticamente um Relatório de Modelagem de Ameaças fundamentado na metodologia STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege), listando riscos de segurança para cada componente e as contramedidas específicas sugeridas para mitigação.

Nós cobrimos todo o ciclo do desafio: **Buscamos as imagens**, **Anotamos o Dataset**, **Treinamos um modelo de visão**, e **Integramos tudo a um sistema com LLM para gerar as respostas**.

## 🌟 Diferenciais do Projeto

Além de cumprir de forma integral os requisitos propostos no desafio, nós projetamos funcionalidades avançadas visando cenários do mundo real de engenharia DevSecOps:

*   **Validação via Metamodelo (Compliance) 🍒**: Em vez de apenas gerar ameaças genéricas, nosso sistema permite o envio de um *Metamodelo* da sua organização. O sistema cruza as diretrizes desse metamodelo (ex: regras de compliance em JSON ou TXT) com o diagrama analisado. Se a sua arquitetura apontar um banco de dados diretamente para a internet violando a regra corporativa, nossa IA irá alertar essa falha de compliance de forma direcionada.
*   **Treinamento Otimizado com YOLOv8 via Arquitetura CUDA 🚀**: Diferente de abordagens mais lentas, todo o script de treinamento de Machine Learning do YOLO foi executado com GPU. Utilizamos uma máquina equipada com CUDA, aplicando estratégias robustas de augmentação e visão (`mosaic`, `mixup`, etc.) configurado automaticamente se houver aceleração de hardware. Isso resultou num tempo de treinamento minúsculo na classificação dos mais diversos ícones de arquiteturas (AWS, Azure, GCP).
*   **Privacidade com LLM Locais e Pipeline LangChain 🔒**: Sabemos que diagramas e sistemas são sigilosos. Fizemos um upgrade na arquitetura para não depender de APIs externas públicas. O projeto foi arquitetado usando **LangChain** orquestrado com **Ollama**. Isso permite o processamento LLM Multimodal usando infraestrutura fechada (Ex: rodando Llama 3 ou LLaVA localmente), impedindo vazamento da topologia do sistema de quem está usando a plataforma.
*   **Back-end Próprio Desacoplado**: Usamos **FastAPI** provendo modularidade para fácil integração com esteiras CI/CD.

## 🛠️ Como Instalar e Usar

**Atenção:** Como nosso projeto mistura dois pilares – o uso do Sistema (Back-end/API/LLM) e a parte de Machine Learning (Treinamento do Dataset YOLO) – **é altamente recomendado configurar ambientes virtuais separados** para evitar gargalos de bibliotecas entre a API rodando em produção e o laboratório de dados.

### Pré-requisitos Gerais
*   **Python 3.8+** instalado.
*   **[Ollama](https://ollama.com/)** rodando na sua máquina. Antes de iniciar, baixe o modelo pelo terminal (ex: `ollama run gemini-3-flash-preview` que é o nosso padrão adotado).

---

### 1. Configurando o Back-end da API REST (Para Uso)

Este é o ambiente principal para inicializar o MVP e a Interface Frontend.

1. **Abra um terminal**, navegue até a pasta `backend` e crie o ambiente virtual:
   ```bash
   cd backend
   python -m venv venv
   ```

2. **Ative o ambiente:**
   * **Windows:** 
      ```bash
      venv\Scripts\activate
      ```
   * **Linux/Mac:** 
      ```
      source venv/bin/activate
      ```

3. **Instale os requisitos da API:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Executar o Ollama:**
   ```bash
   ollama run gemini-3-flash-preview
   ```

5. **Iniciando a API:**
   O projeto já está padronizado para utilizar o modelo `gemini-3-flash-preview`. Inicie a aplicação utilizando o comando:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
---

### 2. Gerando o Dataset de Treinamento (YOLO)

No diretório `ml/database/icons` estão armazenados os ícones de arquitetura das plataformas **AWS** e **Azure**.

A partir desses ícones, um script gera automaticamente um **dataset sintético de treinamento**, criando diversas imagens com composições aleatórias de ícones, conexões, textos e variações visuais. Esse dataset é utilizado posteriormente para o treinamento do modelo de detecção baseado em **YOLO**.

Este repositório já inclui um dataset previamente gerado. Entretanto, caso deseje gerar um novo dataset, siga os passos abaixo:

1. **Abra um novo terminal**, navegue até a pasta `ml` e crie o ambiente virtual:
   ```bash
   cd ml
   python -m venv venv
   ```

2. **Ative o ambiente:**
   * **Windows:** 
      ```bash
      venv\Scripts\activate
      ```
   * **Linux/Mac:** 
      ```
      source venv/bin/activate
      ```

3. **Instale os requisitos pesados:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Rodando o script para criação do dataset:**
   Execute o script para a geração da base conforme descrito abaixo.
   ```bash
   cd database
   python gerar_dataset.py
   ```

   O script criará automaticamente o dataset no formato esperado pelo YOLO, incluindo:
   ```bash
   dataset_yolo/
   ├── images/
   │   ├── train
   │   └── val
   └── labels/
   │  ├── train
   │  └── val
   └── data.yaml
   ```
---

### 3. Configurando o Ambiente de Machine Learning (Para Treinamento)

Caso você queira reavaliar ou aumentar o dataset anotado e realizar um novo treinamento via YOLOv8, monte este outro ambiente virtual. *(Desnecessário se você quiser apenas rodar e usar a IA)*.

1. **Abra um novo terminal**, navegue até a pasta `ml` e crie o ambiente virtual:
   ```bash
   cd ml
   python -m venv venv
   ```

2. **Ative o ambiente:**
   * **Windows:** 
      ```bash
      venv\Scripts\activate
      ```
   * **Linux/Mac:** 
      ```
      source venv/bin/activate
      ```

3. **Instale os requisitos pesados:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Rodando o Treino no PyTorch/YOLO:**
   O processo procurará automaticamente por núcleos CUDA para disparar o treinamento rápido, senão rodará via processador.
   ```bash
   cd training
   python train.py
   ```

---

### 4. Acessando a Solução Visual (Frontend)

Com a API rodando com sucesso no Passo 1:
1. Abra em seu navegador o local host na porta 8000, de preferência a rota criada automaticamente: **[http://localhost:8000/](http://localhost:8000/)** (se estiver acessando pela URL virtual do app default) OU simplesmente abra o arquivo local da pasta `frontend/index.html` em seu navegador web.
2. **Faça o Upload**: Arraste ou selecione seu fluxograma/diagrama de Arquitetura de Software.
3. **Anexe as Regras (Diferencial)**: Envie o JSON do Metamodelo da empresa clicando no botão no canto direito ou deixe em branco se não possuir!
4. Clique em enviar. A Visão computacional escaneará em instantes as bounding boxes e a LLM formulará e imprimirá o **Relatório STRIDE**.

## 🎥 Entregáveis Finais

*   **Link do Github do projeto**: **[Hackathon-IA-para-Devs](https://github.com/Yuriferr/Hackathon-IA-para-Devs.git)**
*   **Documentação**: Você está lendo nela! Todos os passos de solução propostos foram sanados e organizados nas ramificações `/backend`, `/front` e `/ml`.
*   **Vídeo do Pitch (até 15min)**: [Inserir o Link no YouTube/Drive do Pitch final]