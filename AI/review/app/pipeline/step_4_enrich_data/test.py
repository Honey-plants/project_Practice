from google import genai



client = genai.Client(api_key=API_KEY)
print([m.name for m in client.models.list()][:5])
