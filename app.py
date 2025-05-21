from flask import Flask, request, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health-check")
def health_check():
    return "Server is UP", 200

if __name__ == "__main__":
    app.run(debug=True)