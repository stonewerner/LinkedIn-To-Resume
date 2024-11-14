from flask import Flask, request, jsonify
from flask_cors import CORS
from linkedinparser import parse_linkedin_pdf
import os


app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'tmp')

@app.route('/api/parse-linkedin', methods=['POST'])
def parse_linkedin():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    try:
        # Save uploaded file temporarily
        temp_path = '/tmp/linkedin_profile.pdf'
        # file.save(temp_path)
        
        # Parse PDF
        result = parse_linkedin_pdf(temp_path)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)