import os
import sys
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from pathlib import Path

load_dotenv()

root_dir = str(Path(__file__).parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.gemini_rag_model import RAGChatbot
from src.utils import convert_markdown_to_html

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET_KEY")

chatbot = RAGChatbot()

@app.route("/", methods=["GET"])
def home():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("index.html", chat_history=session["chat_history"])

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    session["chat_history"].append(("user", user_message))
    session.modified = True

    context = ""
    if len(session["chat_history"]) > 1:
        recent_messages = session["chat_history"][-6:-1]
        context = "\n\nLịch sử hội thoại gần đây:\n"
        for role, msg in recent_messages:
            context += f"{'Khách hàng' if role == 'user' else 'Bot'}: {msg}\n"

    prompt = context + "\n\nCâu hỏi hiện tại: " + user_message if context else user_message
    bot_response = chatbot.generate_response(prompt)
    bot_response = convert_markdown_to_html(bot_response)

    session["chat_history"].append(("bot", bot_response))
    session.modified = True

    return jsonify({"bot_response": bot_response})

@app.route("/reset", methods=["POST"])
def reset():
    session.pop("chat_history", None)
    return redirect(url_for("home"))

@app.route("/health-check")
def health_check():
    return "Server is UP", 200

if __name__ == "__main__":
    app.run(port=os.getenv("PORT"), debug=True)
