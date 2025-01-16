import google.generativeai as genai
import os
from gtts import gTTS

GEMINI_API_KEY = "AIzaSyA0pskFvbYOPMTPSd7H1bkXfWMBMdK61Ec"
genai.configure(api_key=GEMINI_API_KEY)

def parse(narration):
    data = []
    narrations = []
    lines = narration.split("\n")
    for line in lines:
        if line.startswith('Anlatıcı: '):
            text = line.replace('Anlatıcı: ', '')
            data.append({
                "type": "text",
                "content": text.strip('"'),
            })
            narrations.append(text.strip('"'))
        elif line.startswith('['):
            background = line.strip('[]')
            data.append({
                "type": "image",
                "description": background,
            })
    return data, narrations

def create(data, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    n = 0
    for element in data:
        if element["type"] != "text":
            continue

        n += 1
        output_file = os.path.join(output_folder, f"narration_{n}.mp3")
        
        # Using gTTS for text-to-speech
        tts = gTTS(text=element["content"], lang='tr')
        tts.save(output_file)
