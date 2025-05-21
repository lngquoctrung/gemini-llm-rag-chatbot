from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Dịch giup tôi câu này sang tiếng anh, Xin chào, tôi là Trung"
)

print(response.text)