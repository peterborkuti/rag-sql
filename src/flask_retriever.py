from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from retriever import question_answer
from app_config import AppConfig

app = Flask(__name__,
            template_folder=AppConfig.TEMPLATE_DIR)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)