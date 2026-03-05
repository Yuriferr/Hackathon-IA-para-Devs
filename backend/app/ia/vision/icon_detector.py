from ultralytics import YOLO

class IconDetector:
    def detect(self, img_path, model_path):
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