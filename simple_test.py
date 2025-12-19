import os
import sys
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# CRITICAL: Fix for SSL checks on Windows
os.environ['SSL_CERT_FILE'] = certifi.where()

try:
    from google import genai
except ImportError:
    print("❌ google-genai library not found. Please install with: pip install google-genai")
    sys.exit(1)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY not found in environment.")
    sys.exit(1)

print(f"🚀 Initializing Client...")
client = genai.Client(api_key=api_key)

try:
    print("🚀 Sending simple request (Model: gemini-2.0-flash)...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="How does AI work? (One sentence answer)"
    )
    print("\n🎉 SUCCESS! API Response:")
    print("-" * 30)
    print(response.text)
    print("-" * 30)

except Exception as e:
    print(f"\n❌ API Call Failed: {e}")
