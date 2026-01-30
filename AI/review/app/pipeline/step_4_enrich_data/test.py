from google import genai

API_KEY = ""  # 지금 쓰는 키 그대로

client = genai.Client(api_key=API_KEY)
print([m.name for m in client.models.list()][:5])
