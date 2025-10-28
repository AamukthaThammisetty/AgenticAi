# check.py
import os
from dotenv import load_dotenv
import google.generativeai as genai
# List available models

genai.configure(api_key="AIzaSyD4xUf0CWo-Lgan_vnYvQHc-TTxfCmVpfg")

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
