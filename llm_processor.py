import os

if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    print("✅ Google Cloud credentials set correctly!")
else:
    print("❌ Credentials not found. Try setting the variable again.")
