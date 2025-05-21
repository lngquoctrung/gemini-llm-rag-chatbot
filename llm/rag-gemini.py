from google import genai
from google.genai import types
import pathlib
import os

# Khởi tạo client Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Đường dẫn đến file PDF local
filepath = pathlib.Path('./Untitled 1.pdf')  # Đảm bảo file này có tồn tại trong thư mục hiện tại

# Câu lệnh yêu cầu (prompt)
prompt = "Summarize this document"

# Gửi yêu cầu đến Gemini
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[
        types.Part.from_bytes(
            data=filepath.read_bytes(),
            mime_type='application/pdf',
        ),
        prompt
    ]
)

# In ra kết quả
print(response.text)
