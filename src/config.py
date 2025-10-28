from pathlib import Path

# Get root path
root_path = Path(__file__).parent.parent.absolute()

class Config:
    # Model name, embedding model name and Qdrant collection name
    MODEL_NAME = "gemini-2.5-flash-lite"
    MODEL_TEMPERATURE = 0.3
    MODEL_TOP_P = 0.9
    MODEL_TOP_K = 40
    MODEL_MAX_OUTPUT_TOKENS = 1024
    EMBEDDING_MODEL_NAME = "gemini-embedding-001"
    QDRANT_COLLECTION_NAME = "techshop_docs"

    # Text splitter configuration
    TEXT_SPLITTER_CHUNK_SIZE = 800
    TEXT_SPLITTER_CHUNK_OVERLAP = 200

    # Embedding model configuration
    # Gemini text-embedding-004 uses 769 dimension embedding
    EMBEDDING_DIM = 768

    # Corpus path
    CORPUS_PATH = str(root_path / "corpus")

    # Top K search relevant chunks
    TOP_K_SEARCH_RELEVANT_CHUNKS = 5
    