import os
import requests

API_KEY = "AIzaSyC2y_FKbvA4CV4Au2jh62i16zvjhv9XPsI"
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

payload = {
    "contents": [
        {"parts": [{"text": "用一句话解释什么是机器学习。"}]}
    ]
}

headers = {
    "x-goog-api-key": API_KEY,
    "Content-Type": "application/json",
}

r = requests.post(URL, headers=headers, json=payload, timeout=30)
r.raise_for_status()

data = r.json()
print(data["candidates"][0]["content"]["parts"][0]["text"])

