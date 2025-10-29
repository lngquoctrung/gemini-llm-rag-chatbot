import os
import sys
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path

# Setup for the project: load environment variables and add root directory to sys.path
load_dotenv()
root_dir = str(Path(__file__).parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.gemini_rag_model import RAGChatbot
from src.utils import convert_markdown_to_html
from src.config import Config

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET_KEY")

@app.template_filter('markdown_to_html')
def markdown_to_html_filter(text):
    return convert_markdown_to_html(text)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per day", "100 per hour"],
    storage_uri=os.getenv("REDIS_URL", "memory://")
)

# Initialize RAGChatbot
chatbot = RAGChatbot(config=Config)

@app.route("/", methods=["GET"])
def home():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("index.html", chat_history=session["chat_history"])

@app.route("/chat", methods=["POST"])
@limiter.limit("50 per hour")
def chat():
    try:
        # Get user message
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        # Store user's chat history
        if "chat_history" not in session:
            session["chat_history"] = []
        session["chat_history"].append(("user", user_message))
        session.modified = True

        # Create context from chat history
        context = ""
        if len(session["chat_history"]) > 1:
            recent_messages = session["chat_history"][-5:]
            context_parts = []
            for role, msg in recent_messages[:-1]:
                role_name = "Khách hàng" if role == "user" else "Trợ lý"
                context_parts.append(f"{role_name}: {msg}")
            context = "\n".join(context_parts)

        # Create prompt with context
        if context:
            prompt = f"""
                Lịch sử hội thoại gần đây:
                {context}
                Câu hỏi mới nhất: {user_message}
            """
        else:
            prompt = user_message
        
        # Generate response
        bot_response = chatbot.generate_response(prompt)
        bot_response_html = convert_markdown_to_html(bot_response)

        # Store assistant's chat history
        session["chat_history"].append(("assistant", bot_response))
        session.modified = True

        return jsonify({
            "response": bot_response_html,
            "status": "success"
        })
    
    except Exception as e:
        # Log error
        print(f"Error in chat endpoint: {str(e)}")
        
        error_message = """
            **Demo Limit Reached**
            
            This is a portfolio demo with limited API quota. The chatbot is temporarily unavailable.
            
            For questions about this project or to discuss production implementation, please contact me at lngquoctrung.work@gmail.com
        """
        
        return jsonify({
            "response": convert_markdown_to_html(error_message),
            "status": "error"
        }), 200

@app.route("/reset", methods=["POST"])
def reset():
    session["chat_history"] = []
    session.modified = True
    return redirect(url_for("home"))

@app.route("/health", methods=["GET"])
@limiter.exempt
def health():
    """Health check endpoint"""
    try:
        # Check Qdrant connection
        count = chatbot.qdrant_client.count(chatbot.collection_name).count
        
        return jsonify({
            "status": "healthy",
            "vector_db": "connected",
            "indexed_chunks": count
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route("/stats", methods=["GET"])
@limiter.exempt
def stats():
    """Debug endpoint để xem stats của vector database"""
    try:
        collection_info = chatbot.qdrant_client.get_collection(chatbot.collection_name)
        
        return jsonify({
            "collection_name": chatbot.collection_name,
            "total_chunks": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "status": "ready"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("APP_PORT"), debug=False)