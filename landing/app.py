from flask import Flask, render_template
import os

app = Flask(__name__)

# Configurable app URL: defaults to local Streamlit URL if running locally
STREAMLIT_URL = os.environ.get("STREAMLIT_URL", "http://localhost:8501")

@app.route('/')
def home():
    return render_template('index.html', app_url=STREAMLIT_URL)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
