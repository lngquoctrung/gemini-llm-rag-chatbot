# Gemini RAG Chatbot Assistant

**Gemini RAG Chatbot Assistant** is a production-ready web-based chatbot that uses advanced Retrieval-Augmented Generation (RAG) with vector database technology and Google's Gemini AI to provide accurate, context-aware responses based on your documents.

## 1. Key Features

### Core Capabilities

- **Advanced RAG Architecture**: Local vector database with semantic search using Qdrant for fast and accurate document retrieval
- **Smart Document Processing**: Automatic text chunking with overlap to preserve context across chunks
- **Conversational Memory**: Maintains last 5 messages for contextual conversations
- **Auto-Reindexing**: Detects corpus changes via MD5 hashing and automatically rebuilds vector index
- **Production-Ready**: Rate limiting, health checks, and multi-container orchestration

### Technical Features

- **Vector Similarity Search**: Qdrant with cosine distance for semantic matching
- **Text Embedding**: Gemini embedding model with 768-dimensional vectors
- **Document Chunking**: RecursiveCharacterTextSplitter with 800 character chunks and 200 character overlap
- **Rate Limiting**: Flask-Limiter with Redis backend (300/day, 100/hour, 50/hour for chat)
- **Enhanced Formatting**: Support for bold, lists, headers, code blocks, and inline code
- **Security**: HTML sanitization with bleach to prevent XSS attacks

## 2. Architecture

### System Components

The application consists of three Docker containers orchestrated via Docker Compose :

1. **Web Application** (Flask + Gunicorn)
   - Handles HTTP requests and user interactions
   - Manages RAG pipeline and Gemini AI integration
   - Port: Configurable via environment variable

2. **Qdrant Vector Database** (v1.15)
   - Stores document embeddings and enables semantic search
   - Persistent storage with Docker volumes
   - Internal network communication only

3. **Redis** (Alpine)
   - Rate limiting storage
   - Session caching
   - Configured with 256MB memory limit and LRU eviction policy

### RAG Pipeline

**Indexing Phase** (runs at startup):

1. Scans `corpus/` folder for PDF files
2. Extracts text using PyMuPDF (fitz)
3. Splits text into 800-character chunks with 200-character overlap
4. Generates 768-dimensional embeddings via Gemini
5. Stores vectors in Qdrant with metadata (filename, chunk_index, text_length)
6. Saves corpus hash to detect future changes

**Query Phase** (for each user message):

1. User sends a message via the web interface
2. System embeds the query using Gemini embedding model
3. Performs semantic search in Qdrant to find top-5 relevant chunks
4. Builds context by combining relevant chunks with chat history
5. Sends prompt + context to Gemini 2.5 Flash Lite
6. Returns formatted response to user

## 3. Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Google AI API key (Gemini)

### Get Your Gemini API Key

1. Visit: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API key"**
4. Copy and save the key

### Running with Docker Compose (Recommended)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/lngquoctrung/gemini-rag-bot-app.git
   cd gemini-rag-bot-app
   ```

2. **Create `.env` file** in the project root:

   ```env
   # Application
   APP_PORT=5000
   SESSION_SECRET_KEY=your-secret-key-here
   
   # Google AI
   GOOGLE_API_KEY=your-gemini-api-key-here
   
   # Qdrant
   QDRANT_URL=http://qdrant:6333
   
   # Redis
   REDIS_URL=redis://redis:6379
   
   # Docker Hub (for building)
   DOCKERHUB_USERNAME=your-dockerhub-username
   ```

3. **Add your PDF documents** to the `corpus/` folder:

   ```bash
   corpus/
   ├── techshop-faq.pdf
   ├── techshop-troubleshooting-guide.pdf
   └── techshop-user-guide.pdf
   ```

4. **Start the application**:

   ```bash
   docker-compose up -d
   ```

5. **Access the chatbot**:
   Open your browser and navigate to `http://localhost:5000`

6. **Check health status**:

   ```bash
   curl http://localhost:5000/health
   ```

### Running with Docker (Standalone)

If you prefer to run only the web application container:

```bash
docker run -d \
  --name chatbot \
  -p 5000:5000 \
  -e PORT=5000 \
  -e GOOGLE_API_KEY=your-gemini-api-key \
  -e SESSION_SECRET_KEY=your-secret-key \
  -e QDRANT_URL=http://your-qdrant-host:6333 \
  -e REDIS_URL=redis://your-redis-host:6379 \
  qctrung/gemini-rag-bot-app:latest
```

**Note**: You'll need to provide external Qdrant and Redis instances.

## 4. Project Structure

```bash
├── app.py                          # Flask application with routes
├── config.py                       # Centralized configuration (moved to src/)
├── Dockerfile                      # Multi-stage Docker build
├── docker-compose.yml              # Multi-container orchestration
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create this)
├── corpus/                        # PDF documents for RAG
│   ├── techshop-faq.pdf
│   ├── techshop-troubleshooting-guide.pdf
│   └── techshop-user-guide.pdf
├── src/
│   ├── __init__.py
│   ├── config.py                  # Model and RAG configuration
│   ├── gemini_rag_model.py        # RAG chatbot implementation
│   └── utils.py                   # Markdown to HTML converter
├── static/
│   ├── script.js                  # Frontend JavaScript
│   └── style.css                  # UI styling
└── templates/
    └── index.html                 # Chat interface template
```

## 5. Configuration

All configurable parameters are centralized in `src/config.py` :

```python
# Model Configuration
MODEL_NAME = "gemini-2.5-flash-lite"
MODEL_TEMPERATURE = 0.3
MODEL_TOP_P = 0.9
MODEL_TOP_K = 40
MODEL_MAX_OUTPUT_TOKENS = 1024

# Embedding Configuration
EMBEDDING_MODEL_NAME = "gemini-embedding-001"
EMBEDDING_DIM = 768

# Text Splitting
TEXT_SPLITTER_CHUNK_SIZE = 800
TEXT_SPLITTER_CHUNK_OVERLAP = 200

# RAG Search
TOP_K_SEARCH_RELEVANT_CHUNKS = 5

# Database
QDRANT_COLLECTION_NAME = "techshop_docs"
```

## 6. API Endpoints

### Main Endpoints

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/` | GET | Home page with chat interface | 100/hour |
| `/chat` | POST | Send message and get response | 50/hour |
| `/reset` | POST | Clear chat history | 100/hour |
| `/health` | GET | Health check (Qdrant connection) | None |
| `/stats` | GET | Vector database statistics | None |

### Health Check Response Example

```json
{
  "status": "healthy",
  "vector_db": "connected",
  "indexed_chunks": 342
}
```

### Stats Response Example

```json
{
  "collection_name": "techshop_docs",
  "total_chunks": 342,
  "vector_size": 768,
  "status": "ready"
}
```

## 7. How It Works

### Document Indexing

When the application starts, it:

1. **Checks for existing index**: Compares MD5 hash of corpus folder with stored hash
2. **Re-indexes if needed**: Automatically rebuilds if documents changed
3. **Extracts text**: Uses PyMuPDF to extract text from each PDF page
4. **Chunks text**: Splits into overlapping segments to preserve context
5. **Generates embeddings**: Creates 768-dimensional vectors using Gemini
6. **Stores in Qdrant**: Uploads in batches of 100 with metadata
7. **Saves hash**: Stores corpus hash for future change detection

**Chunking Strategy** :

Without overlap:

```text
Chunk 1: "Today is a beau"
Chunk 2: "tiful day, we will"
Chunk 3: " go for a picnic in the suburbs."
```

With 200-character overlap:

```text
Chunk 1: "Today is a beau"
Chunk 2: "a beautiful day, we will"  ← overlaps with chunk 1
Chunk 3: "we will go for a picnic in the suburbs."  ← overlaps with chunk 2
```

### Query Processing

For each user message:

1. **Context Building**: Combines last 5 messages from chat history
2. **Query Embedding**: Converts user query to 768-dimensional vector
3. **Semantic Search**: Finds top-5 most relevant chunks using cosine similarity
4. **Context Assembly**: Formats chunks with document names as context
5. **Prompt Construction**: Combines context + chat history + current query
6. **AI Generation**: Sends to Gemini 2.5 Flash Lite with system instructions
7. **Response Formatting**: Converts Markdown to HTML with sanitization

### System Prompt

The chatbot follows these instructions:

- Answer questions based ONLY on provided documents
- Use friendly, professional tone
- Keep responses concise (2-3 paragraphs)
- Use bullet points for lists
- End with "Bạn còn thắc mắc gì khác không?" (Any other questions?)
- If information not found, suggest contacting <support@techshop.com>

## 8. Development

### Local Development Setup

1. **Install dependencies**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set environment variables**:

   ```bash
   export GOOGLE_API_KEY=your-key
   export SESSION_SECRET_KEY=your-secret
   export QDRANT_URL=http://localhost:6333
   export REDIS_URL=redis://localhost:6379
   export PORT=5000
   ```

3. **Run Qdrant and Redis locally**:

   ```bash
   docker run -d -p 6333:6333 qdrant/qdrant:v1.15
   docker run -d -p 6379:6379 redis:alpine
   ```

4. **Start Flask app**:

   ```bash
   python app.py
   ```

### Building Docker Image

```bash
docker build -t your-username/gemini-rag-bot-app:latest .
docker push your-username/gemini-rag-bot-app:latest
```

## 9. Performance & Scalability

### Resource Usage

- **Web Container**: ~200-300MB RAM
- **Qdrant**: ~100-200MB RAM (depends on corpus size)
- **Redis**: Max 256MB RAM (configured with LRU eviction)

### Optimization Features

- **Multi-stage Docker build**: Reduces image size by separating build and runtime
- **Batch uploads**: Processes 100 vectors at a time for efficiency
- **Virtual environment**: Isolated dependencies with minimal overhead
- **Gunicorn**: Production-grade WSGI server

### Rate Limits

- Global: 300 requests/day, 100 requests/hour
- Chat endpoint: 50 requests/hour per IP
- Health/Stats: Unlimited

## 10. Security Features

1. **HTML Sanitization**: Prevents XSS attacks using bleach library
2. **Rate Limiting**: Protects against abuse with Redis-backed limiter
3. **Input Validation**: Rejects empty messages and sanitizes input
4. **Environment Variables**: Sensitive data stored in .env, not in code
5. **Network Isolation**: Docker containers communicate via private network

## 11. Troubleshooting

### Chatbot Returns Errors

**"API quota exceeded"** :

- Check your Gemini API quota limits
- Wait for quota reset or upgrade plan

**"Vector database not connected"** :

- Verify Qdrant container is running: `docker ps`
- Check logs: `docker logs rag-chat-app-qdrant`
- Ensure QDRANT_URL is correct in .env

**"Empty corpus"** :

- Add PDF files to `corpus/` folder
- Restart application: `docker-compose restart web`

### Re-indexing Documents

To force re-indexing after updating PDFs:

```bash
# Restart the web container
docker-compose restart web

# Or delete the Qdrant volume and restart
docker-compose down
docker volume rm rag-chat-app-qdrant-storage
docker-compose up -d
```

### View Logs

```bash
# Web application
docker logs -f gemini-rag-bot-app

# Qdrant
docker logs -f rag-chat-app-qdrant

# Redis
docker logs -f rag-chat-app-redis
```

## 12. Contact

**Developer**: @lngquoctrung  
**Email**: <lngquoctrung.work@gmail.com>  
**GitHub**: [https://github.com/lngquoctrung/gemini-rag-bot-app](https://github.com/lngquoctrung/gemini-rag-bot-app)

For production implementation questions or custom deployment assistance, please reach out via email.
