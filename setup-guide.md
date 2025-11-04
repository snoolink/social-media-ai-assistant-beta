# Suzy - Social Media Assistant Setup Guide 🌟

## Quick Start

### 1. Install Dependencies

```bash
pip install flask flask-cors pandas
```

### 2. Project Structure

Create this folder structure:

```
suzy-assistant/
├── app.py                    # Flask backend server
├── index.html                # Frontend interface
├── scripts/                  # Python scripts folder
│   ├── creds.py             # Auto-generated (don't create manually)
│   ├── schedule_post.py
│   ├── analyze_stats.py
│   ├── content_ideas.py
│   ├── generate_hashtags.py
│   └── process_csv.py
├── uploads/                  # Auto-created for CSV uploads
├── .gitignore               # IMPORTANT: Include this!
└── README.md
```

### 3. Create Python Script Files

Copy each script from the "Example Python Scripts" artifact into separate files in the `scripts/` folder:

```bash
mkdir scripts
cd scripts

# Create each script file with the content provided
# schedule_post.py, analyze_stats.py, etc.
```

### 4. Start the Backend Server

```bash
python app.py
```

You should see:
```
🌟 Starting Suzy's backend server...
✨ Server running on http://localhost:5000
💬 Ready to help with social media management!
```

### 5. Open the Frontend

Open `index.html` in your web browser, or serve it with:

```bash
# Option 1: Python's built-in server
python -m http.server 8080

# Then visit: http://localhost:8080
```

### 6. First-Time Setup

1. When you first open the app, you'll see a setup modal
2. Enter your Instagram username and password
3. Click "Let's Get Started! 🚀"
4. Your credentials will be saved to `scripts/creds.py`

## How It Works

### Frontend (index.html)
- Beautiful chat interface with Suzy
- Quick action buttons for common tasks
- CSV file upload support
- Mobile-responsive design

### Backend (app.py)
- Flask server running on port 5000
- Handles credential management
- Routes messages to appropriate Python scripts
- Processes CSV uploads
- Returns results to frontend

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Check if server is running |
| `/api/check-credentials` | GET | Check if credentials exist |
| `/api/save-credentials` | POST | Save Instagram credentials |
| `/api/chat` | POST | Process chat messages and files |
| `/api/upload-csv` | POST | Upload CSV files |

## Security Notes ⚠️

### IMPORTANT: The `creds.py` file contains sensitive information!

1. **Never commit `creds.py` to Git**
   - It's already in your `.gitignore`
   - Double-check before pushing to GitHub

2. **Keep your credentials secure**
   - The file is stored locally only
   - Consider using environment variables for production

3. **Production Considerations**
   - Use environment variables instead of storing in files
   - Implement proper authentication
   - Use HTTPS for all communications
   - Hash/encrypt passwords

## Customizing Scripts

Each script in the `scripts/` folder can be customized to:
- Connect to Instagram API
- Perform actual scheduling
- Pull real analytics
- Generate AI-powered content
- Process CSV data for insights

### Example: Enhancing schedule_post.py

```python
import os
import json
from creds import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
from instagrapi import Client  # Example library

params = json.loads(os.environ.get('PARAMS', '{}'))
message = params.get('message', '')

# Your actual Instagram posting logic here
client = Client()
client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

# Schedule or post content
# ...

print("✅ Post scheduled successfully!")
```

## Testing

### Test Backend Health
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Suzy backend is running! 🚀"
}
```

### Test Credentials Check
```bash
curl http://localhost:5000/api/check-credentials
```

## Troubleshooting

### Port Already in Use
If port 5000 is busy:
```python
# In app.py, change the last line:
app.run(debug=True, host='0.0.0.0', port=5001)

# Update frontend API_URL:
const API_URL = 'http://localhost:5001/api';
```

### CORS Errors
Make sure `flask-cors` is installed:
```bash
pip install flask-cors
```

### Scripts Not Running
- Check that scripts have proper Python syntax
- Ensure scripts are in the `scripts/` folder
- Check server console for error messages

### Frontend Can't Connect
- Verify backend is running on port 5000
- Check browser console for errors
- Ensure no firewall blocking localhost

## Adding New Features

### Add a New Command

1. **Create new script**: `scripts/your_script.py`
2. **Update backend**: Add condition in `process_message()` function
3. **Add frontend button**: Add new action chip in chat
4. **Test**: Send message and check response

### Example: Adding "Generate Caption" Feature

**Step 1**: Create `scripts/generate_caption.py`
```python
import os
import json
from creds import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

params = json.loads(os.environ.get('PARAMS', '{}'))
print("✨ Here's a caption for you:")
print("Living my best life! 🌟 #Blessed #GoodVibes")
```

**Step 2**: Update `app.py` in `process_message()`:
```python
elif 'caption' in message_lower:
    return run_script('generate_caption.py', {'message': message})
```

**Step 3**: Add button in `index.html`:
```javascript
<button class="action-chip" onclick="quickAction('caption')">✍️ Caption</button>

// In quickAction function:
'caption': 'Generate a caption for my post'
```

## Environment Variables (Production)

For production, use environment variables instead of `creds.py`:

```python
# Instead of:
from creds import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

# Use:
INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.environ.get('INSTAGRAM_PASSWORD')
```

Set them before running:
```bash
export INSTAGRAM_USERNAME="your_username"
export INSTAGRAM_PASSWORD="your_password"
python app.py
```

## Next Steps

1. ✅ Set up the project structure
2. ✅ Start the backend server
3. ✅ Open frontend and enter credentials
4. ✅ Test chat functionality
5. 🎯 Customize scripts for your needs
6. 🚀 Add real Instagram API integration
7. 💡 Implement advanced features

## Support

If you run into issues:
1. Check the browser console (F12)
2. Check the Flask server terminal output
3. Verify all files are in correct locations
4. Ensure all dependencies are installed

---

Made with 💜 by Suzy - Your friendly Social Media Assistant!
