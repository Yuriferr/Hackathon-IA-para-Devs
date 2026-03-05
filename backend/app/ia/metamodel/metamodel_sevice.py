class MetamodelService:
    async def read_metamodel(self, metamodel):
        """"
        Lê o conteúdo do metamodelo enviado e retorna como string.
        Se houver erro na leitura, lança exceção para ser tratada no serviço principal.
        Se não houver metamodelo, retorna None."""

        print(" > Processando metamodelo (se fornecido)...")
        metamodel_content = None
        
        try:
            if metamodel:
                content = await metamodel.read()
                metamodel_content = content.decode("utf-8")
                
                return metamodel_content
        except Exception as e:
            print(f" > Erro ao ler metamodelo: {e}")
            raise