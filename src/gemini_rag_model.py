import os
import fitz
import hashlib

from typing import List, Dict
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from google.genai import types

class RAGChatbot:
    def __init__(self, config):
        # Configurations
        self.config = config
        
        # Gemini model and embedding
        self.model_name = self.config.MODEL_NAME
        self.embedding_model_name = self.config.EMBEDDING_MODEL_NAME
        self.genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Connect to Qdrant
        qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = self.config.QDRANT_COLLECTION_NAME

        # Text splitter configuration
        # Chunk overlap to keep context
        # Example: Original text [Today is a beautiful day, we will go for a picnic in the suburbs.]
        # Without overlap:
        #   Chunk 1: "Today is a beau"
        #   Chunk 2: "tiful day, we will"
        #   Chunk 3: " go for a picnic in the suburbs."
        # With overlap = 5: Each chunk will have 5 characters overlap from previous chunk
        #   Chunk 1: "Today is a beau"
        #   Chunk 2: " beautiful day, we will"
        #   Chunk 3: "ll go for a picnic in the suburbs."
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.TEXT_SPLITTER_CHUNK_SIZE, 
            chunk_overlap=self.config.TEXT_SPLITTER_CHUNK_OVERLAP, 
            separators=["\n\n", "\n", ". ", " ", ""], 
            length_function=len,
        )

        # Initialize collection
        self._init_collection()

    def _calculate_corpus_hash(self) -> str:
        """Calculate hash of corpus folder to detectect content changes"""
        if not os.path.exists(self.config.CORPUS_PATH):
            return ""
        
        # Initialize hash with MD5 algorithm
        hasher = hashlib.md5()

        # Read content of each file and hash it
        for filename in sorted(os.listdir(self.config.CORPUS_PATH)):
            file_path = os.path.join(self.config.CORPUS_PATH, filename)
            
            if os.path.isfile(file_path) and filename.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())

        # Return hash string in hexadecimal format
        return hasher.hexdigest()

    def _get_stored_hash(self) -> str:
        """Get stored hash from collection metadata"""
        try:
            result =self.qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[0]
            )
            if result:
                return result[0].payload.get("corpus_hash", "")
            else:
                return ""
        except:
            return ""

    def _init_collection(self):
        """Initialize collection and document indexs if not exists"""
        collections = self.qdrant_client.get_collections().collections
        collection_exists = any(c.name == self.collection_name for c in collections)
        
        # Calculate current corpur hash
        current_hash = self._calculate_corpus_hash()
        
        if collection_exists:
            stored_hash = self._get_stored_hash()
            # Check current hash if it changes or not
            if current_hash == stored_hash:
                print(f"Vector database already initialized ({self.qdrant_client.count(self.collection_name).count} chunks)")
                return
            # If corpus changed
            else:
                print("Corpus changed, re-indexing...")
                self.qdrant_client.delete_collection(self.collection_name)

        # Initialize vector database if it does not exist    
        print("Initializing vector database...")
        self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.config.EMBEDDING_DIM,
                distance=Distance.COSINE, # Use cosine distance for similarity search
            )
        )

        # Index all PDFs
        self._index_corpus(current_hash)

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""

            # Read each page of pdf file
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            
            # Close reader
            doc.close()
            return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
        
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Gemini model"""
        try:
            result = self.genai_client.models.embed_content(
                model=self.embedding_model_name,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=self.config.EMBEDDING_DIM) # Only get 768 dimensions
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"Error getting embedding from Gemini model: {e}")
            return None

    def _index_corpus(self, corpus_hash: str):
        """Index all documents into Qdrant with chunking"""
        # Check corpus folder exists
        if not os.path.exists(self.config.CORPUS_PATH):
            print("Corpus folder does not exist")
            return
        
        points = []
        point_id = 1 # Store from index 1, 0 for current hash

        # Get pdf filenames
        pdf_files = sorted([f for f in os.listdir(self.config.CORPUS_PATH) if f.endswith('.pdf')])
        if not pdf_files:
            print("No PDF files found in corpus folder")
            return
        
        print(f"Indexing {len(pdf_files)} PDF files...")
        for filename in pdf_files:
            file_path = os.path.join(self.config.CORPUS_PATH, filename)

            print(f"Processing {filename}...")
            # Extract text
            full_text = self._extract_text_from_pdf(file_path)
            if not full_text.strip():
                print(f"Skipping {filename} because it is empty")
                continue

            # Split into chunks
            chunks = self.text_splitter.split_text(full_text)
            # Create embeddings for each chunk
            for chunk_idx, chunk in enumerate(chunks):
                # Get embedding
                embedding = self._get_embedding(chunk)
                if embedding is None:
                    continue
                # Create point
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "filename": filename, 
                        "chunk_index": chunk_idx, 
                        "total_chunks": len(chunks), 
                        "text": chunk, 
                        "text_length": len(chunk)
                    }
                ))
                point_id += 1

                # Upload in batches of 100
                if len(points) >= 100:
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name, 
                        points=points
                    )
                    print(f"Uploaded {len(points)} points")
                    points = []
        # Upload remaining points
        if points:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        
        # Update corpus hash in collection metadata
        metadata_point = PointStruct(
            id=0,
            vector=[0.0] * self.config.EMBEDDING_DIM, # Dummy vector
            payload={
                "type": "metadata",
                "corpus_hash": corpus_hash,
                "indexed_at": str(datetime.now())
            }
        )
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[metadata_point]
        )

        total_count = self.qdrant_client.count(self.collection_name).count
        print(f"Indexed {total_count} chunks")

    def search_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search top-k relevant chunks from vector database"""
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                return []
            
            # Search
            search_results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                with_payload=True,
            )

            # Format results
            chunks = []
            for result in search_results.points:
                chunks.append({
                    "text": result.payload["text"],
                    "filename": result.payload["filename"],
                    "score": result.score,
                    "chunk_index": result.payload["chunk_index"],
                })
            return chunks
        except Exception as e:
            print(f"Error searching relevant chunks: {e}")
            return []
        
    def generate_response(self, prompt: str) -> str:
        """Generate response with RAG from vector database"""
        system_instruction = """
            Bạn là trợ lý ảo của TechShop, một nền tảng thương mại điện tử.

            NHIỆM VỤ CHÍNH:
            - Trả lời câu hỏi của khách hàng DỰA TRÊN các tài liệu hướng dẫn, FAQ và troubleshooting được cung cấp trong Context
            - Ưu tiên thông tin từ Context, KHÔNG sử dụng kiến thức chung
            - Nếu Context không có thông tin liên quan, hãy trả lời: "Xin lỗi, tôi không tìm thấy thông tin này. Vui lòng liên hệ support@techshop.com"

            PHONG CÁCH:
            - Thân thiện, chuyên nghiệp
            - Câu trả lời ngắn gọn, rõ ràng (2-3 đoạn văn)
            - Sử dụng bullet points khi liệt kê nhiều mục
            - Luôn kết thúc với câu hỏi "Bạn còn thắc mắc gì khác không?"

            QUY TẮC QUAN TRỌNG:
            - CHỈ trả lời dựa trên thông tin trong Context
            - KHÔNG bịa đặt hoặc suy đoán thông tin
            - Nếu không chắc chắn, hãy thừa nhận và đề nghị liên hệ support
        """
        
        try:
            # 1. Search relevant chunks
            relevant_chunks = self.search_relevant_chunks(
                prompt,
                top_k=self.config.TOP_K_SEARCH_RELEVANT_CHUNKS
            )
            
            if not relevant_chunks:
                return "Xin lỗi, tôi đang gặp sự cố kỹ thuật. Vui lòng thử lại sau hoặc liên hệ support@techshop.com"
            
            # 2. Build context from relevant chunks
            context_parts = []
            for idx, chunk in enumerate(relevant_chunks, 1):
                context_parts.append(
                    f"[Document {idx} - {chunk['filename']}]\n{chunk['text']}"
                )
            
            context = "\n\n---\n\n".join(context_parts)
            
            # 3. Build full prompt
            full_prompt = f"""
                Context từ tài liệu TechShop:

                {context}

                ---

                Câu hỏi của khách hàng: {prompt}

                Trả lời dựa trên Context phía trên:
            """
            
            # 4. Generate response
            response = self.genai_client.models.generate_content(
                model=self.model_name,
                contents=[{"role": "user", "parts": [{"text": full_prompt}]}],
                config={
                    "system_instruction": system_instruction,
                    "temperature": self.config.MODEL_TEMPERATURE,
                    "top_p": self.config.MODEL_TOP_P,
                    "top_k": self.config.MODEL_TOP_K,
                    "max_output_tokens": self.config.MODEL_MAX_OUTPUT_TOKENS,
                }
            )
            
            return response.text
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            print(f"Generation error: {error_type} - {error_msg}")
            
            # Handle specific errors
            if "quota" in error_msg.lower() or "429" in error_msg:
                raise Exception("API quota exceeded. Please try again later.")
            elif "timeout" in error_msg.lower():
                raise Exception("Request timeout. Please try again.")
            else:
                raise Exception(f"API error: {error_type}")