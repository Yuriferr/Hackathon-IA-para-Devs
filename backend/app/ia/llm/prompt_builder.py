import json

class PromptBuilder:
    def build(self, icons, metamodel_content=None):
        """"
        Constrói um prompt otimizado para análise STRIDE usando os ícones detectados e o metamodelo (se houver).
        O prompt é estruturado para guiar a LLM a identificar os fluxos entre os componentes, analisar a conformidade com o metamodelo e gerar um relatório de ameaças STRIDE
        """

        print(f" > Construindo prompt para análise STRIDE...")
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
        Atue como Especialista em AppSec.

        VERIFICAÇÃO INICIAL:

        Antes de qualquer coisa, valide se a imagem anexa corresponde a um diagrama de arquitetura de software, diagrama de rede, modelo de ameaças ou Diagrama de Fluxo de Dados (DFD).
        Se a imagem NÃO for um diagrama válido (por exemplo: foto de pessoas, animais, paisagem, meme, objetos, tela em branco ou texto aleatório), interrompa a análise, não gere nenhum relatório e responda APENAS com a seguinte mensagem:

        "⚠️ **Aviso:** A imagem fornecida não parece ser um diagrama de arquitetura ou de fluxo estruturado reconhecível. Por favor, envie um diagrama válido para a análise."

        Caso a imagem seja um diagrama ou desenho de arquitetura válido, prossiga com a análise a seguir:

        Analise a imagem do Diagrama de Fluxo de Dados (DFD).

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

        return prompt