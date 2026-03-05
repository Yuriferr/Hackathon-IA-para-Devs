import os
import shutil
import tempfile

from app.ia.llm.prompt_builder import PromptBuilder
from app.ia.llm.stride_analyzer import StrideAnalyzer
from app.ia.metamodel.metamodel_sevice import MetamodelService
from app.ia.vision.icon_detector import IconDetector

class AnalyzeService:
    def __init__(self):
        self.icon_detector = IconDetector()
        self.prompt_builder = PromptBuilder()
        self.stride_analyzer = StrideAnalyzer()
        self.metamodel_service = MetamodelService()

    def _save_temp_file(self, file):
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            return tmp.name

    def _get_model_path(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "..", "core", "best.pt")
        if not os.path.exists(model_path):
            raise Exception("Modelo YOLO não encontrado.")
        return model_path

    async def analyze(self, file, metamodel):
        try:

            # 0. Processar Metamodelo (se houver)
            metamodel_content = await self.metamodel_service.read_metamodel(metamodel)

            # 1. Preparação
            temp_filename = self._save_temp_file(file)
            model_path = self._get_model_path()

            # 2. Detectar ícones
            icons = self.icon_detector.detect(temp_filename, model_path)

            # 3. Construir prompt otimizado para análise STRIDE
            prompt = self.prompt_builder.build(icons, metamodel_content)

            # 4. Análise completa (OCR + STRIDE + COMPLIANCE)
            report = self.stride_analyzer.analyze(temp_filename, prompt)

            return report
        except Exception as e:
            print(f"Erro: {e}")
            raise

        finally:
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except Exception:
                    pass