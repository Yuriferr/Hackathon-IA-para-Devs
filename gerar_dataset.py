import os
import random
import glob
import shutil
import yaml
import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tqdm import tqdm

# ==========================================
#        CONFIGURAÇÕES AJUSTADAS
# ==========================================

ICONS_PATH = "icons"
OUTPUT_PATH = "dataset_yolo"

# META DE COBERTURA: Garante repetição matemática
MIN_REPEATS_PER_ICON = 50  

# [AJUSTE 1] Aumentei o mínimo para evitar imagens "vazias" ou com pouca variação
ICONS_PER_IMAGE = (25, 55) 

# Tamanho
ICON_SIZE_RANGE = (20, 90)

# --- PROBABILIDADES ---
CLONE_PROBABILITY = 0.5     
CLONE_COUNT = (2, 4)        

# [AJUSTE 2] Probabilidade de ter texto perto do ícone (Não será mais 100%)
TEXT_LABEL_PROB = 0.5       

# [AJUSTE 3] Probabilidade de conexão (Linhas). Reduzi para não bagunçar.
CONNECTION_DENSITY = 0.3    

GLOBAL_BLUR_PROB = 0.20     
ICON_BLUR_PROB = 0.15       
GRAYSCALE_PROB = 0.20       

# Cores
BG_COLORS_LIGHT = ["#F8F9FA", "#FFFFFF", "#F0F0F0", "#FCFCFC"] # Mais brancos/limpos
BG_COLORS_DARK = ["#1E1E1E", "#2D2D2D", "#000000"]
BORDER_COLORS = ["#555555", "#232F3E", "#007ACC", "#E76F00"]

# Cores de linhas mais claras para não confundir com ícones
LINE_COLORS_LIGHT = ["#DDDDDD", "#CCCCCC", "#BBBBBB"] 
LINE_COLORS_DARK = ["#444444", "#555555"]

def setup_directories():
    if os.path.exists(OUTPUT_PATH): shutil.rmtree(OUTPUT_PATH)
    dirs = [f"{OUTPUT_PATH}/images/train", f"{OUTPUT_PATH}/images/val",
            f"{OUTPUT_PATH}/labels/train", f"{OUTPUT_PATH}/labels/val"]
    for d in dirs: os.makedirs(d, exist_ok=True)

def load_icons(path):
    files = []
    for ext in ['*.png', '*.PNG', '*.jpg', '*.jpeg']:
        files.extend(glob.glob(os.path.join(path, '**', ext), recursive=True))
    unique_files = list(set(files))
    if not unique_files:
        sys.exit(f"❌ ERRO: Nenhum ícone encontrado em '{path}'")
    
    icons = []
    print(f"⏳ Carregando {len(unique_files)} ícones...")
    for f in tqdm(unique_files):
        try:
            img = Image.open(f).convert("RGBA")
            if img.getbbox(): img = img.crop(img.getbbox())
            icons.append(img)
        except: pass
    return icons

def get_yolo_bbox(img_w, img_h, box):
    xmin, ymin, xmax, ymax = box
    dw, dh = 1. / img_w, 1. / img_h
    return ((xmin + xmax)/2.0 * dw, (ymin + ymax)/2.0 * dh, (xmax - xmin) * dw, (ymax - ymin) * dh)

def check_overlap(new_box, existing_boxes, buffer=0):
    nx1, ny1, nx2, ny2 = new_box
    for bx1, by1, bx2, by2 in existing_boxes:
        if not (nx2 < bx1 - buffer or nx1 > bx2 + buffer or ny2 < by1 - buffer or ny1 > by2 + buffer):
            return True
    return False

# ==========================================
#      GERADORES DE FUNDO E LINHAS
# ==========================================

def draw_structural_background(draw, w, h, is_dark_mode, force_gray=False):
    """Desenha caixas de VPC/Subnet."""
    if force_gray:
        palette = ["#F5F5F5", "#E0E0E0"]
        outline = "#333333"
    else:
        palette = BG_COLORS_DARK if is_dark_mode else BG_COLORS_LIGHT
        outline = "#FFFFFF" if is_dark_mode else "#DDDDDD" # Borda mais sutil

    # Reduzi a quantidade de caixas de fundo para limpar a imagem
    if random.random() > 0.4: # Nem sempre desenha estrutura
        for _ in range(random.randint(1, 2)):
            bx = random.randint(10, 50)
            by = random.randint(10, 50)
            bw = w - random.randint(20, 100)
            bh = h - random.randint(20, 100)
            
            if bw > 150 and bh > 150:
                draw.rectangle([bx, by, bx+bw, by+bh], fill=random.choice(palette), outline=outline, width=2)

def draw_connections(draw, boxes, is_dark_mode):
    """
    [AJUSTE] Desenha linhas mais claras e em menor quantidade.
    """
    if len(boxes) < 2: return

    # Escolhe cores que não briguem com os ícones (cinza claro)
    line_color = random.choice(LINE_COLORS_DARK) if is_dark_mode else random.choice(LINE_COLORS_LIGHT)
    
    # Conecta apenas 30% dos ícones (menos bagunça)
    num_lines = int(len(boxes) * CONNECTION_DENSITY)
    
    # Garante que não desenhe linhas demais
    if num_lines > 15: num_lines = 15

    for _ in range(num_lines):
        # Tenta conectar ícones próximos para simular fluxo real
        b1 = random.choice(boxes)
        # Tenta achar um b2 que não seja o mesmo e não esteja muito longe
        candidates = [b for b in boxes if b != b1]
        if not candidates: continue
        b2 = random.choice(candidates)
        
        x1, y1 = (b1[0]+b1[2])//2, (b1[1]+b1[3])//2
        x2, y2 = (b2[0]+b2[2])//2, (b2[1]+b2[3])//2
        
        # Linha fina (width=1)
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=1)

def draw_distractors(draw, w, h, is_dark_mode):
    """Formas geométricas simples no fundo."""
    for _ in range(random.randint(1, 4)): # Menos distratores
        sz = random.randint(20, 50)
        x, y = random.randint(0, w - sz), random.randint(0, h - sz)
        color = "#333333" if is_dark_mode else "#E0E0E0" # Cor muito suave
        
        if random.random() > 0.5:
            draw.rectangle([x, y, x+sz, y+sz], outline=color, width=1)
        else:
            draw.ellipse([x, y, x+sz, y+sz], outline=color, width=1)

# ==========================================
#           CORE: GERAÇÃO DA CENA
# ==========================================

def generate_scene_from_batch(icon_batch, img_id, subset):
    W, H = 800, 800 
    
    is_grayscale = random.random() < GRAYSCALE_PROB
    
    if is_grayscale:
        bg_color = random.choice(["#FFFFFF", "#F0F0F0"]) # Fundo sempre claro no PB para contraste
        is_dark_mode = False
    else:
        is_dark_mode = random.random() > 0.7 # 30% Dark Mode
        bg_color = "#121212" if is_dark_mode else "#FFFFFF"
    
    bg = Image.new('RGB', (W, H), bg_color)
    draw = ImageDraw.Draw(bg)
    
    # 1. Desenha Estrutura de Fundo
    draw_structural_background(draw, W, H, is_dark_mode, force_gray=is_grayscale)
    
    # 2. Desenha Distratores (Fundo)
    draw_distractors(draw, W, H, is_dark_mode)

    yolo_labels = []
    
    # Planejamento de Ícones
    pending_icons = icon_batch.copy()
    
    # Lista temporária para guardar posições ANTES de colar
    # Precisamos saber onde eles vão ficar para desenhar as linhas POR BAIXO
    planned_boxes = [] 
    icons_to_paste = [] # Tuplas (imagem, x, y, w, h, tem_texto)
    
    count_fails = 0
    
    while pending_icons and count_fails < 100:
        icon_master = pending_icons.pop(0)
        
        if random.random() < CLONE_PROBABILITY:
            reps = random.randint(*CLONE_COUNT)
        else:
            reps = 1
            
        for _ in range(reps):
            size = random.randint(*ICON_SIZE_RANGE)
            aspect = icon_master.width / icon_master.height
            w_icon, h_icon = size, int(size / aspect)
            
            # Tenta posicionar
            placed = False
            tries = 0
            while not placed and tries < 50:
                x = random.randint(10, W - w_icon - 10)
                y = random.randint(10, H - h_icon - 20) # Margem maior embaixo p/ texto
                new_box = (x, y, x + w_icon, y + h_icon)
                
                # Check overlap com buffer maior para evitar bagunça
                if not check_overlap(new_box, planned_boxes, buffer=5):
                    planned_boxes.append(new_box)
                    
                    # Prepara ícone
                    icon_resized = icon_master.resize((w_icon, h_icon), Image.Resampling.LANCZOS)
                    if is_grayscale:
                        icon_resized = icon_resized.convert("LA").convert("RGBA")
                    if random.random() < ICON_BLUR_PROB:
                        icon_resized = icon_resized.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 0.8)))
                    
                    # Decide se vai ter texto
                    has_text = random.random() < TEXT_LABEL_PROB
                    
                    icons_to_paste.append({
                        "img": icon_resized,
                        "box": new_box,
                        "has_text": has_text
                    })
                    
                    # Gera Label YOLO agora (a posição é final)
                    ybbox = get_yolo_bbox(W, H, new_box)
                    yolo_labels.append(f"0 {ybbox[0]:.6f} {ybbox[1]:.6f} {ybbox[2]:.6f} {ybbox[3]:.6f}")
                    
                    placed = True
                else:
                    tries += 1
            
            if not placed:
                pass # Segue o baile se não couber

    # 3. [AJUSTE] Desenha Linhas AGORA (Antes de colar os ícones)
    # Assim as linhas ficam no fundo e não rabiscam o ícone
    draw_connections(draw, planned_boxes, is_dark_mode)

    # 4. Cola os Ícones e Textos
    for item in icons_to_paste:
        img = item["img"]
        x, y, x2, y2 = item["box"]
        
        bg.paste(img, (x, y), img)
        
        if item["has_text"]:
            lbl_color = "#AAAAAA" if is_dark_mode else "#444444" # Texto cinza para não chamar tanta atenção
            # [AJUSTE] Texto afastado 5px para não encostar na borda do ícone
            draw.text((x, y2 + 5), "Component", fill=lbl_color)

    # 5. Blur Global Suave
    if random.random() < GLOBAL_BLUR_PROB:
        bg = bg.filter(ImageFilter.GaussianBlur(radius=0.5))

    # Salva
    fname = f"{subset}_{img_id:05d}"
    final_img = bg.convert("RGB")
    final_img.save(os.path.join(OUTPUT_PATH, "images", subset, fname + ".jpg"), "JPEG", quality=85, optimize=True)
    
    with open(os.path.join(OUTPUT_PATH, "labels", subset, fname + ".txt"), "w") as f:
        f.write("\n".join(yolo_labels))

def main():
    icons = load_icons(ICONS_PATH)
    unique_count = len(icons)
    setup_directories()
    
    print(f"\n🎯 MODO LIMPEZA & PRECISÃO")
    print(f"   - Ícones únicos: {unique_count}")
    print(f"   - Meta: ~{MIN_REPEATS_PER_ICON} repetições por ícone.")
    print(f"   - Linhas desenhadas no fundo (menos confusão).")
    print(f"   - Textos espaçados e opcionais.")
    
    # 1. BARALHO
    full_deck = []
    for icon in icons:
        full_deck.extend([icon] * MIN_REPEATS_PER_ICON)
    random.shuffle(full_deck)
    
    # 2. SPLIT
    split_idx = int(len(full_deck) * 0.8)
    train_deck = full_deck[:split_idx]
    val_deck = full_deck[split_idx:]
    
    # 3. GERAÇÃO
    def generate_from_deck(deck, subset_name):
        batch_size_min, batch_size_max = ICONS_PER_IMAGE
        current_idx = 0
        img_id = 0
        pbar = tqdm(total=len(deck), desc=f"Gerando {subset_name}")
        
        while current_idx < len(deck):
            this_batch_size = random.randint(batch_size_min, batch_size_max)
            batch = deck[current_idx : current_idx + this_batch_size]
            current_idx += this_batch_size
            
            if not batch: break
            
            generate_scene_from_batch(batch, img_id, subset_name)
            img_id += 1
            pbar.update(len(batch))
        pbar.close()
        return img_id

    print("\n🚀 Iniciando geração...")
    total_train = generate_from_deck(train_deck, "train")
    total_val = generate_from_deck(val_deck, "val")
    
    # YAML
    yaml_content = {
        'path': os.path.abspath(OUTPUT_PATH), 
        'train': 'images/train', 
        'val': 'images/val', 
        'names': {0: 'icon'}
    }
    with open(os.path.join(OUTPUT_PATH, "data.yaml"), "w") as f: yaml.dump(yaml_content, f)
    
    print("\n✅ Dataset Limpo Gerado!")

if __name__ == "__main__":
    main()