import google.generativeai as genai
import base64
import os
import requests
import urllib.parse
import time
import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image

model = genai.GenerativeModel('gemini-pro')

def add_text_to_image(image_path, text, font_size=80):
    # Görüntüyü oku
    img = cv2.imread(image_path)
    if img is None:
        raise Exception(f"Görüntü okunamadı: {image_path}")
    
    # OpenCV görüntüsünü PIL görüntüsüne çevir (Türkçe karakterler için)
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    try:
        # Özel font kullan (Arial veya benzeri bir font)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Eğer font bulunamazsa varsayılan fontu kullan
        font = ImageFont.load_default()
    
    # Görüntü boyutlarını al
    img_width = img.shape[1]
    img_height = img.shape[0]
    
    # Maksimum metin genişliği (görüntü genişliğinin %90'ı)
    max_text_width = int(img_width * 0.9)
    
    # Metni kelimelere böl
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = draw.textlength(word + " ", font=font)
        
        if current_width + word_width <= max_text_width:
            current_line.append(word)
            current_width += word_width
        else:
            if current_line:  # Eğer mevcut satır doluysa
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:  # Tek kelime bile sığmıyorsa
                if font_size > 40:  # Font boyutunu küçült ve tekrar dene
                    return add_text_to_image(image_path, text, font_size - 10)
                else:
                    lines.append(word)  # En küçük boyutta bile sığmıyorsa kelimeyi böl
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Toplam metin yüksekliğini hesapla
    line_height = int(font_size * 1.5)  # Satır aralığını artır
    total_text_height = len(lines) * line_height
    
    # Metni dikey olarak ortala
    text_y = (img_height - total_text_height) // 2
    
    # Yarı saydam siyah arka plan ekle
    overlay = img.copy()
    padding = font_size  # Arka plan padding'i
    cv2.rectangle(overlay, 
                 (0, text_y - padding),
                 (img.shape[1], text_y + total_text_height + padding),
                 (0, 0, 0),
                 -1)
    img = cv2.addWeighted(overlay, 0.7, img, 0.3, 0)  # Arka plan opaklığını artır
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # Her satırı ayrı ayrı yaz
    for i, line in enumerate(lines):
        # Metni ortala
        text_width = draw.textlength(line, font=font)
        text_x = (img_width - text_width) // 2
        y = text_y + i * line_height
        
        # Metni yaz (daha kalın görünmesi için aynı metni biraz kaydırarak iki kez yaz)
        draw.text((text_x-1, y-1), line, font=font, fill=(0, 0, 0))  # Gölge
        draw.text((text_x+1, y+1), line, font=font, fill=(0, 0, 0))  # Gölge
        draw.text((text_x, y), line, font=font, fill=(255, 255, 255))  # Ana metin
    
    # PIL görüntüsünü OpenCV formatına geri çevir ve kaydet
    img_cv2 = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    cv2.imwrite(image_path, img_cv2)

def resize_to_exact(image_path, target_width, target_height):
    # Görüntüyü oku
    img = cv2.imread(image_path)
    if img is None:
        raise Exception(f"Görüntü okunamadı: {image_path}")
    
    # Görüntüyü tam olarak istenen boyuta getir
    resized = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
    
    # Görüntüyü kaydet
    cv2.imwrite(image_path, resized)

def translate_to_english(text):
    prompt = f"""
    Lütfen aşağıdaki Türkçe sahne açıklamasını İngilizce'ye çevir ve daha detaylı, görsel olarak zengin bir şekilde tanımla.
    Sahneyi mümkün olduğunca detaylı ve görsel olarak tanımla, ama kısa tut.
    
    Örnek:
    "Kutay'ın şaşkın yüzü" -> "close up portrait of a young man with a shocked expression, dramatic lighting, detailed face"
    "Uzay gemisinin içi" -> "futuristic spaceship interior, glowing panels, high-tech equipment, sci-fi atmosphere"
    
    Çevrilecek metin:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def create_from_data(data, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_number = 0
    narrator_text = ""
    
    for i, element in enumerate(data):
        if element["type"] == "text" and "Anlatıcı:" in element["content"]:
            # Anlatıcı metnini al (başındaki "Anlatıcı:" kısmını çıkar)
            narrator_text = element["content"].replace("Anlatıcı:", "").strip()
        
        elif element["type"] == "image":
            image_number += 1
            image_name = f"image_{image_number}.png"
            image_path = os.path.join(output_dir, image_name)
            
            # Görüntüyü oluştur
            generate(element["description"], image_path)
            
            # Eğer bir anlatıcı metni varsa, görüntünün üzerine ekle
            if narrator_text:
                add_text_to_image(image_path, narrator_text)
                narrator_text = ""  # Metni kullandıktan sonra temizle

def generate(prompt, output_file, size="1080x1920"):
    # Prompt'u İngilizce'ye çevir
    english_prompt = translate_to_english(prompt)
    print(f"Aranan terim: {english_prompt}")
    
    # Boyutları ayır
    width, height = map(int, size.split('x'))
    
    # Stil parametreleri
    style_params = (
        "vertical composition, portrait orientation, "
        "anime style, stylized illustration, cartoon art, "
        "vibrant colors, clean lines, animation key visual, "
        "Studio Ghibli inspired, detailed background"
    )
    
    # Tam prompt oluştur
    full_prompt = f"{style_params}, {english_prompt}"
    
    # Pollinations.ai API URL'sini oluştur
    image_url = f"https://pollinations.ai/p/{urllib.parse.quote(full_prompt)}?width={width}&height={height}&model=flux&seed=42"
    
    print(f"Oluşturulan URL: {image_url}")
    
    # Görüntüyü indir
    response = requests.get(image_url)
    
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        # Görüntüyü tam boyuta getir
        resize_to_exact(output_file, width, height)
        
        print(f"Görüntü başarıyla indirildi ve yeniden boyutlandırıldı: {output_file}")
        # Pollinations.ai'nin görüntüyü oluşturması için kısa bir bekleme
        time.sleep(2)
    else:
        print(f"API Yanıtı: {response.text}")
        raise Exception(f"Görüntü oluşturulamadı: {response.status_code}")
