from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from retriever import question_answer
from app_config import AppConfig

app = Flask(__name__, template_folder=AppConfig.TEMPLATE_DIR)
CORS(app)  # Enable cross-origin requests

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():  
    data = request.json
    query = data.get('query', '')
    
    if not query.strip():
        return jsonify({'error': 'Empty query'})
    
    sql, answer = question_answer(query)   
            
    result ={
        'sql': sql,
        'answer': answer,
    }

    print ("result",sql, answer)
        
    ret_val=jsonify({
        'query': query,
        'result': result
    })

    print("retval",ret_val)
    return ret_val

def run_ssl():
    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    from pathlib import Path
    cert_path = Path(AppConfig.CERT_DIR)
    # Generate self-signed certificate if needed
    cert_path.mkdir(exist_ok=True)
    
    cert_file = cert_path / 'cert.pem'
    key_file = cert_path / 'key.pem'
    
    if not cert_file.exists() or not key_file.exists():
        print("Generating self-signed certificate...")
        from subprocess import run
        run(['openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-nodes',
             '-out', str(cert_file), '-keyout', str(key_file),
             '-days', '365', '-subj', '/CN=localhost'], check=True)
    
    context.load_cert_chain(str(cert_file), str(key_file))
    
    # Run with HTTPS
    app.run(host='0.0.0.0', port=7860, ssl_context=context, debug=True)

if __name__ == '__main__':
    if AppConfig.LOCAL:
        run_ssl()
    else:
        app.run(host='0.0.0.0', port=7860)