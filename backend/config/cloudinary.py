import cloudinary
import cloudinary.uploader
import os

def configure_cloudinary():
    """Configure Cloudinary with environment variables"""
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dacuza9e4"),
        api_key=os.getenv("CLOUDINARY_API_KEY", "858743735668412"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET", "ZL1XhzbD6V_IkfIclP-CPNfBSL4"),
        secure=True
    )

async def upload_to_cloudinary(file_content: bytes, filename: str, folder: str = "vouchers"):
    """
    Upload file to Cloudinary
    
    Args:
        file_content: Binary content of the file
        filename: Original filename
        folder: Cloudinary folder (default: "vouchers")
    
    Returns:
        dict with 'url' and 'public_id'
    """
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            resource_type="auto",
            public_id=filename.rsplit('.', 1)[0] if '.' in filename else filename
        )
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }
    except Exception as e:
        raise Exception(f"Error uploading to Cloudinary: {str(e)}")
