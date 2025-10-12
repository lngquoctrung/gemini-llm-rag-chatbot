from google import genai
import pathlib
import os
import io

class RAGChatbot:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = model
        self.corpus = self._load_corpus()

    def _load_corpus(self):
        corpus_path = os.path.abspath("corpus")
        documents = []

        for filename in os.listdir(corpus_path):
            file_path = os.path.join(corpus_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    content = io.BytesIO(f.read())
                    uploaded_file = self.client.files.upload(
                        file=content,
                        config=dict(mime_type="application/pdf")
                    )
                    documents.append(uploaded_file)

        return documents

    def generate_response(self, prompt):
        system_instruction = """
            Bạn là trợ lý ảo của TechShop, một nền tảng thương mại điện tử.

            NHIỆM VỤ CHÍNH:
            - Trả lời câu hỏi của khách hàng DỰA TRÊN các tài liệu hướng dẫn, FAQ và troubleshooting đã được cung cấp
            - Ưu tiên thông tin từ tài liệu, KHÔNG sử dụng kiến thức chung
            - Nếu tài liệu có thông tin, PHẢI trả lời chi tiết và chính xác
            - Nếu tài liệu KHÔNG có thông tin, hãy nói: "Tôi không tìm thấy thông tin này trong tài liệu. Vui lòng liên hệ support@techshop.com hoặc gọi 1800-TECHSHOP"

            CÁCH TRẢ LỜI:
            - Trả lời bằng tiếng Việt, rõ ràng và thân thiện
            - Trích dẫn thông tin cụ thể từ tài liệu
            - Luôn đảm bảo thông tin chính xác và hữu ích

            QUY TẮC FORMAT QUAN TRỌNG:
            - Nếu hướng dẫn có NHIỀU BƯỚC theo thứ tự, PHẢI sử dụng numbered list (1., 2., 3., 4...)
            - Mỗi bước chính là một numbered item riêng biệt
            - Chi tiết bên trong mỗi bước có thể dùng bullet points (-)
            - VÍ DỤ ĐÚNG:
            1. Bước đầu tiên
            2. Bước thứ hai
            3. Bước thứ ba
            - VÍ DỤ SAI (tránh):
            1. Bước đầu tiên:
            - Chi tiết 1
            - Chi tiết 2 (đây không phải bước riêng nên không được đánh số)
            - Khi tài liệu có danh sách các bước 1, 2, 3, 4... HÃY GIỮ NGUYÊN FORMAT ĐÓ
        """

        formatted_prompt = f"""
            Dựa trên các tài liệu hướng dẫn sử dụng (User Guide), FAQ, và Troubleshooting Guide của TechShop đã được cung cấp ở trên, hãy trả lời câu hỏi sau:

            Câu hỏi: {prompt}

            Lưu ý:
            - Trả lời ngôn ngữ dựa theo ngôn ngữ của user hỏi
            - Nếu tài liệu có các bước được đánh số (1., 2., 3., ...), hãy giữ nguyên format đó trong câu trả lời
            - Mỗi bước chính trong quy trình là một numbered item riêng biệt
            - Tìm kiếm kỹ trong tài liệu trước khi trả lời
            - Không nói dựa theo user guide, FAQ, và troubleshooting guide
            - Không bảo là xem mục 1.2 hoặc bất kỳ mục nào trong câu trả lời
        """

        response = self.client.models.generate_content(
            model=self.model,
            contents=[*self.corpus, formatted_prompt],
            config={
                "system_instruction": system_instruction,
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 20
            }
        )

        return response.text
