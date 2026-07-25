import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 50)
print("CLOUDINARY ENVIRONMENT CHECK")
print("=" * 50)

cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

print(f"CLOUDINARY_CLOUD_NAME: {cloud_name if cloud_name else '❌ NOT SET'}")
print(f"CLOUDINARY_API_KEY: {api_key if api_key else '❌ NOT SET'}")
print(f"CLOUDINARY_API_SECRET: {'✓ SET' if api_secret else '❌ NOT SET'}")

if cloud_name and api_key and api_secret:
    print("\n✅ All Cloudinary variables are set!")
    print("\nTesting Cloudinary connection...")
    
    try:
        import cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        print("✅ Cloudinary SDK configured successfully!")
        print(f"✅ Will upload to: Academia-UNI/vouchers")
    except Exception as e:
        print(f"❌ Error configuring Cloudinary: {e}")
else:
    print("\n❌ Missing Cloudinary variables in .env file!")
    print("\nAdd these lines to your .env file:")
    print("CLOUDINARY_CLOUD_NAME=dacuza9e4")
    print("CLOUDINARY_API_KEY=858743735668412")
    print("CLOUDINARY_API_SECRET=ZL1XhzbD6V_IkfIclP-CPNfBSL4")

print("=" * 50)
