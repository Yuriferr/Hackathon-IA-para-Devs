from ultralytics import YOLO
import cv2

# Carrega o SEU modelo treinado
model = YOLO(r"C:\Projetos\Organizar Icones\Treinamentos\yolov8n_icons\weights\best.pt")

# Caminho da imagem
img_path = r"C:\Projetos\Organizar Icones\diagramas\aws_diagrama.png" 

# Faz a predição filtrando tudo abaixo de 80% (0.8)
# O parâmetro 'conf' define o limiar mínimo de confiança
results = model(img_path, conf=0.75)

# Mostra o resultado
for result in results:
    im_array = result.plot()  # Vai desenhar apenas o que passou no filtro de 0.8
    cv2.imshow("Resultado", im_array)
    cv2.waitKey(0) # Aperte qualquer tecla para fechar
    cv2.destroyAllWindows()