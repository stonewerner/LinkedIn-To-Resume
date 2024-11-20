from flask import Flask, request, jsonify, send_file
from linkedinparser import parse_linkedin_pdf, generate_resume, retrieve_profile
from latexgenerator import ResumeGenerator, ResumeTheme
import os
import shutil

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
        
        # Parse PDF and get profile ID
        profile_id, result = parse_linkedin_pdf(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({
            'profile_id': profile_id,
            'profile_data': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-resume/<profile_id>', methods=['POST'])
def generate_resume_endpoint(profile_id):
    try:
        # Get theme options from request
        theme_options = request.json or {}
        theme = ResumeTheme(
            primary_color=theme_options.get('primary_color', 'black'),
            accent_color=theme_options.get('accent_color', '0.5,0.5,0.5'),
            font_family=theme_options.get('font_family', 'helvetica'),
            section_style=theme_options.get('section_style', 'basic'),
            layout=theme_options.get('layout', 'traditional'),
            font_size=theme_options.get('font_size', '11pt')
        )

        # Retrieve profile from Pinecone
        profile_data = retrieve_profile(profile_id)
        if not profile_data:
            return jsonify({'error': 'Profile not found'}), 404

        # Create output directory if it doesn't exist
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate resume PDF with theme
        output_path = os.path.join(output_dir, f'resume_{profile_id}')
        generator = ResumeGenerator(profile_data, theme)
        pdf_path = generator.generate(output_path)
        
        # Return PDF file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'resume_{profile_id}.pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)