<<<<<<< HEAD
=======

>>>>>>> 3c90289feb86aa984187265790919d85c490402a
import os
import sys
from dotenv import load_dotenv
import certifi

<<<<<<< HEAD
# Load environment variables
load_dotenv()

# CRITICAL: Fix for SSL checks on Windows
=======
# Load env var
load_dotenv()

# Fix for SSL checks
>>>>>>> 3c90289feb86aa984187265790919d85c490402a
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

<<<<<<< HEAD
print(f"🚀 Initializing Client...")
=======
print(f"🚀 Initializing Client with Key: {api_key[:10]}...")
>>>>>>> 3c90289feb86aa984187265790919d85c490402a
client = genai.Client(api_key=api_key)

try:
    print("🚀 Sending simple request (Model: gemini-2.0-flash)...")
<<<<<<< HEAD
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="How does AI work? (One sentence answer)"
=======
    # Using gemini-2.0-flash as consistent with project config
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents="How does AI work? Verify you are functional in 1 short sentence."
>>>>>>> 3c90289feb86aa984187265790919d85c490402a
    )
    print("\n🎉 SUCCESS! API Response:")
    print("-" * 30)
    print(response.text)
    print("-" * 30)

except Exception as e:
    print(f"\n❌ API Call Failed: {e}")
