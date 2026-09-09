import os
import sys

# Menambahkan root project ke sys.path agar package 'web' dapat di-import
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from web.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("\n" + "=" * 60)
    print("KarirLake Intelligence Web Server Starting...")
    print(f"Local Access: http://127.0.0.1:{port} or http://localhost:{port}")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True)
