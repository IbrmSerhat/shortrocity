import subprocess
import sys
import io

# Set console output encoding to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Input text for the story parameters
story_input = """
**Ana Karakterler:** Serhat
**Mekan:** uzay aracı
**Mood:** Macera dolu
**Tema:** Dostluk
"""

try:
    # Run Ollama command
    process = subprocess.Popen(
        ["ollama", "run", "hf.co/Kutay07/HikayeLLM8B"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',
        universal_newlines=True
    )
    
    # Send input and get output
    output, error = process.communicate(input=story_input)
    
    # Check for errors
    if error:
        print(f"Error occurred: {error}")
    
    # Write output to source.txt
    with open('source.txt', 'w', encoding='utf-8') as file:
        file.write(output)
    
    print("Story has been generated and saved to source.txt")
    print("Generated content:", output)  # Print the output to verify

except Exception as e:
    print(f"An error occurred: {e}")