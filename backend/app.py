from flask import Flask, request, jsonify
from linkedinparser import parse_linkedin_pdf
import os

from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'tmp')

@app.route('/api/parse-linkedin', methods=['POST'])
def parse_linkedin():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    try:
        # Create tmp directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save uploaded file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'linkedin_profile.pdf')
        file.save(temp_path)
        
        # Parse PDF
        result = parse_linkedin_pdf(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)