from flask import Flask, request
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)  # ✅ Enables CORS for all routes

@app.route('/save_urls', methods=['POST'])
def save_urls():
    data = request.json

    if 'urls' not in data:
        return {'error': 'No URLs provided'}, 400

    # ✅ Get dynamic filename or fallback to 'profile_urls'
    filename = data.get('filename', 'profile_urls')
    filepath = f"{filename}.json"

    # ✅ Load existing URLs if file exists
    existing_urls = set()
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            try:
                existing_urls = set(json.load(f))
            except json.JSONDecodeError:
                existing_urls = set()

    # ✅ Merge new URLs
    new_urls = set(data['urls'])
    all_urls = list(existing_urls.union(new_urls))

    # ✅ Save merged URLs
    with open(filepath, 'w') as f:
        json.dump(all_urls, f, indent=2)

    print(f"✅ Saved to {filepath} — {len(new_urls - existing_urls)} new URLs, total: {len(all_urls)}")
    return {'status': 'success'}

if __name__ == '__main__':
    app.run(port=5000)
