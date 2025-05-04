"""URL utilities module."""
import os

# Configuration
PORT = int(os.getenv("PORT", 5002))
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}")

def get_public_download_url(filename):
    """Helper function to generate public download URL"""
    return f"{BASE_URL}/public/download/{filename}"