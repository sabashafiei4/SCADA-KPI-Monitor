from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

FASTAPI_URL = "http://127.0.0.1:8000/api/calculate-kpi"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    frontend_data = request.json
    
    try:
        response = requests.post(FASTAPI_URL, json=frontend_data)
        response.raise_for_status() 
        
        kpi_results = response.json()
        return jsonify(kpi_results)
        
    except requests.exceptions.ConnectionError:
        return jsonify({"status": "error", "message": "سرور پردازشی FastAPI خاموش است."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)