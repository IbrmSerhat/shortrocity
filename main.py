#!/usr/bin/env python3

import google.generativeai as genai
import time
import json
import sys
import os

import narration
import images
import video

GEMINI_API_KEY = "AIzaSyA0pskFvbYOPMTPSd7H1bkXfWMBMdK61Ec"
genai.configure(api_key=GEMINI_API_KEY)

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <source_file> [settings_file]")
    sys.exit(1)

with open(sys.argv[1], encoding='utf-8') as f:
    source_material = f.read()

caption_settings = {}
if len(sys.argv) > 2:
    with open(sys.argv[2]) as f:
        caption_settings = json.load(f)

short_id = str(int(time.time()))
output_file = "short.avi"

basedir = os.path.join("shorts", short_id)
if not os.path.exists(basedir):
    os.makedirs(basedir)

print("Generating script...")

# Configure the model
model = genai.GenerativeModel('gemini-pro')

prompt = """Sen bir YouTube shorts anlatıcısısın. 30 saniye ile 1 dakika arasında bir anlatım oluştur. Oluşturduğun shortslar, anlatım devam ederken arka planda bir görüntüden diğerine geçiş yapan bir yapıya sahip.

Shortstaki her cümle için görüntü açıklamaları oluşturman gerekecek. Bunlar bir yapay zeka görüntü oluşturucuya gönderilecek. HİÇBİR KOŞULDA görüntü açıklamalarında ünlü veya kişi isimlerini kullanma. Ünlülerin görüntülerini oluşturmak yasadışıdır. Kişileri sadece isimsiz olarak tanımla. Görüntü açıklamalarında herhangi bir gerçek kişi veya grubu referans gösterme. Görüntülerde kadın figürü veya diğer cinsel içeriklerden bahsetme çünkü bunlara izin verilmiyor.

Ancak anlatımda her türlü içeriği, gerçek isimler dahil kullanabilirsin. Sadece görüntü açıklamaları kısıtlıdır.

Not: Anlatım bir metin-ses dönüştürücüye beslenecek, bu yüzden özel karakterler kullanma.

Aşağıdaki kaynak materyale dayalı bir YouTube shorts anlatımı oluştur:

{source_material}

Yanıtını köşeli parantez içinde bir görüntü açıklaması ve altında bir anlatım olacak şekilde ver. Her ikisi de kendi satırlarında olmalı, aşağıdaki gibi:

[Bir arka plan görüntüsünün açıklaması]
Anlatıcı: "Bir cümlelik anlatım"

[Bir arka plan görüntüsünün açıklaması]
Anlatıcı: "Bir cümlelik anlatım"

[Bir arka plan görüntüsünün açıklaması]
Anlatıcı: "Bir cümlelik anlatım"

Short en fazla 6 cümle olmalı.
"""

response = model.generate_content(prompt.format(source_material=source_material))
response_text = response.text

with open(os.path.join(basedir, "response.txt"), "w") as f:
    f.write(response_text)

data, narrations = narration.parse(response_text)
with open(os.path.join(basedir, "data.json"), "w") as f:
    json.dump(data, f, ensure_ascii=False)

print(f"Generating narration...")
narration.create(data, os.path.join(basedir, "narrations"))

print("Generating images...")
images.create_from_data(data, os.path.join(basedir, "images"))

print("Generating video...")
video.create(narrations, basedir, output_file, caption_settings)

print(f"DONE! Here's your video: {os.path.join(basedir, output_file)}")
