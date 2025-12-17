
import os
import sys
from dotenv import load_dotenv
import certifi

# Load env var
load_dotenv()

# Fix for SSL checks
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

print(f"🚀 Initializing Client with Key: {api_key[:10]}...")
client = genai.Client(api_key=api_key)

try:
    print("🚀 Sending simple request (Model: gemini-2.0-flash)...")
    # Using gemini-2.0-flash as consistent with project config
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents="How does AI work? Verify you are functional in 1 short sentence."
    )
    print("\n🎉 SUCCESS! API Response:")
    print("-" * 30)
    print(response.text)
    print("-" * 30)

except Exception as e:
    print(f"\n❌ API Call Failed: {e}")
