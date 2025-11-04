from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Paths
SCRIPTS_DIR = 'scripts'
CREDS_FILE = os.path.join(SCRIPTS_DIR, 'creds.py')
UPLOAD_FOLDER = 'uploads'

# Create necessary directories
os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/api/check-credentials', methods=['GET'])
def check_credentials():
    """Check if credentials file exists and has content"""
    try:
        if os.path.exists(CREDS_FILE):
            with open(CREDS_FILE, 'r') as f:
                content = f.read()
                # Check if file has actual credentials
                if 'INSTAGRAM_USERNAME' in content and 'INSTAGRAM_PASSWORD' in content:
                    return jsonify({'exists': True})
        return jsonify({'exists': False})
    except Exception as e:
        return jsonify({'exists': False, 'error': str(e)})


@app.route('/api/save-credentials', methods=['POST'])
def save_credentials():
    """Save Instagram credentials to creds.py"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Create creds.py content
        creds_content = f'''# Instagram Credentials
# WARNING: Keep this file secure and never commit to version control

INSTAGRAM_USERNAME = "{username}"
INSTAGRAM_PASSWORD = "{password}"
'''
        
        # Write to file
        with open(CREDS_FILE, 'w') as f:
            f.write(creds_content)
        
        return jsonify({
            'success': True,
            'message': 'Credentials saved successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and execute appropriate scripts"""
    try:
        message = request.form.get('message', '')
        files = request.files.getlist('files')
        
        # Save uploaded files
        uploaded_file_paths = []
        if files:
            for file in files:
                if file.filename.endswith('.csv'):
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)
                    uploaded_file_paths.append(filepath)
        
        # Process message and determine which script to run
        response = process_message(message, uploaded_file_paths)
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'response': f"Oops! Something went wrong: {str(e)}",
            'error': str(e)
        }), 500


def process_message(message, file_paths):
    """Process user message and execute appropriate Python scripts"""
    message_lower = message.lower()
    
    # Determine which script to run based on message content
    if 'schedule' in message_lower or 'post' in message_lower:
        return run_script('schedule_post.py', {'message': message})
    
    elif 'analyze' in message_lower or 'stats' in message_lower or 'analytics' in message_lower:
        return run_script('analyze_stats.py', {'message': message, 'files': file_paths})
    
    elif 'idea' in message_lower or 'content' in message_lower:
        return run_script('content_ideas.py', {'message': message})
    
    elif 'hashtag' in message_lower:
        return run_script('generate_hashtags.py', {'message': message})
    
    elif file_paths:
        # If files are uploaded without specific command
        return run_script('process_csv.py', {'files': file_paths})
    
    else:
        # Default friendly response
        return {
            'response': "I'm here to help! I can schedule posts, analyze stats, generate content ideas, create hashtags, or process CSV files. What would you like to do? 😊"
        }


def run_script(script_name, params=None):
    """Execute a Python script and return results"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    
    # Check if script exists
    if not os.path.exists(script_path):
        return {
            'response': f"I'm ready to help with that, but the script '{script_name}' hasn't been created yet. Let me know what you'd like it to do! 🛠️",
            'script_needed': script_name
        }
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'PARAMS': json.dumps(params) if params else '{}'}
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            return {
                'response': output if output else f"Script {script_name} executed successfully! ✅",
                'success': True
            }
        else:
            error = result.stderr.strip()
            return {
                'response': f"I ran into an issue: {error[:200]}",
                'error': error,
                'success': False
            }
    
    except subprocess.TimeoutExpired:
        return {
            'response': "The task is taking longer than expected. Let me keep working on it! ⏳",
            'error': 'timeout'
        }
    except Exception as e:
        return {
            'response': f"I encountered an error: {str(e)}",
            'error': str(e),
            'success': False
        }


@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Handle CSV file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            return jsonify({
                'success': True,
                'message': f'File {file.filename} uploaded successfully',
                'filepath': filepath
            })
        else:
            return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Suzy backend is running! 🚀'
    })


if __name__ == '__main__':
    print("🌟 Starting Suzy's backend server...")
    print("📁 Scripts directory:", os.path.abspath(SCRIPTS_DIR))
    print("📤 Upload folder:", os.path.abspath(UPLOAD_FOLDER))
    print("🔑 Credentials file:", os.path.abspath(CREDS_FILE))
    print("\n✨ Server running on http://localhost:5000")
    print("💬 Ready to help with social media management!\n")
    
    app.run(debug=True, host='0.0.0.0', port=5050)