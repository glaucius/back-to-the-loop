import os
import io
import uuid
from minio import Minio
from minio.error import S3Error
from PIL import Image
import magic
from werkzeug.utils import secure_filename

class ImageService:
    def __init__(self):
        # MinIO configuration
        self.minio_endpoint = os.environ.get('MINIO_ENDPOINT', 'minio:9000')
        self.minio_access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
        self.minio_secret_key = os.environ.get('MINIO_SECRET_KEY', 'minioadmin123')
        self.bucket_name = os.environ.get('MINIO_BUCKET', 'btl-images')
        self.minio_secure = os.environ.get('MINIO_SECURE', 'False').lower() == 'true'
        
        # Initialize MinIO client
        self.client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=self.minio_secure
        )
        
        # For URL generation, use public endpoint if provided, otherwise use configured endpoint
        self.public_endpoint = os.environ.get('MINIO_PUBLIC_ENDPOINT', self.minio_endpoint)
        
        # Allowed file extensions and MIME types
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        self.allowed_mime_types = {
            'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'
        }
        
        # Maximum file size (5MB)
        self.max_file_size = 5 * 1024 * 1024
        
        # Image size limits
        self.max_dimensions = {
            'profile_picture': (1200, 800),  # Main backyard photo
            'logo': (400, 400)  # Logo
        }
    
    
    def validate_image(self, file):
        """Validate uploaded image file"""
        errors = []
        
        if not file or not file.filename:
            errors.append("No file selected")
            return errors
        
        # Check file extension
        filename = secure_filename(file.filename)
        if '.' not in filename:
            errors.append("File must have an extension")
            return errors
        
        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in self.allowed_extensions:
            errors.append(f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}")
        
        # Read file content for validation
        file.seek(0)
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Check file size
        if len(file_content) > self.max_file_size:
            errors.append(f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB")
        
        # Check MIME type using python-magic
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type not in self.allowed_mime_types:
                errors.append(f"Invalid file type: {mime_type}")
        except Exception as e:
            errors.append("Could not determine file type")
        
        return errors
    
    def resize_image(self, file_content, image_type='profile_picture'):
        """Resize image to appropriate dimensions"""
        max_width, max_height = self.max_dimensions.get(image_type, (800, 600))
        
        try:
            # Open image
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Calculate new dimensions maintaining aspect ratio
            width, height = image.size
            aspect_ratio = width / height
            
            if width > max_width or height > max_height:
                if width > height:
                    new_width = max_width
                    new_height = int(max_width / aspect_ratio)
                else:
                    new_height = max_height
                    new_width = int(max_height * aspect_ratio)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            return output.getvalue()
        
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")
    
    def upload_image_data(self, image_data, filename, image_type='profile_picture', folder='backyards'):
        """Upload image data directly to MinIO"""
        try:
            # Generate unique filename
            extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4().hex}.{extension}"
            
            # Create object name with folder structure
            object_name = f"{folder}/{image_type}/{unique_filename}"
            
            # Upload to MinIO
            self.client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(image_data),
                length=len(image_data),
                content_type='image/jpeg'
            )
            
            # Use public endpoint for URL generation
            protocol = 'https' if self.minio_secure else 'http'
            return {
                'success': True,
                'file_path': object_name,
                'file_url': f"{protocol}://{self.public_endpoint}/{self.bucket_name}/{object_name}"
            }
        
        except Exception as e:
            return {'success': False, 'errors': [f"Upload failed: {str(e)}"]}

    def upload_image(self, file, image_type='profile_picture', folder='backyards'):
        """Upload image to MinIO"""
        # Validate image
        errors = self.validate_image(file)
        if errors:
            return {'success': False, 'errors': errors}
        
        try:
            # Read file content
            file.seek(0)
            file_content = file.read()
            
            # Resize image
            resized_content = self.resize_image(file_content, image_type)
            
            # Generate unique filename
            filename = secure_filename(file.filename)
            extension = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{extension}"
            
            # Create object name with folder structure
            object_name = f"{folder}/{image_type}/{unique_filename}"
            
            # Upload to MinIO
            self.client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(resized_content),
                length=len(resized_content),
                content_type='image/jpeg'
            )
            
            # Use public endpoint for URL generation
            protocol = 'https' if self.minio_secure else 'http'
            return {
                'success': True,
                'file_path': object_name,
                'file_url': f"{protocol}://{self.public_endpoint}/{self.bucket_name}/{object_name}"
            }
        
        except Exception as e:
            return {'success': False, 'errors': [f"Upload failed: {str(e)}"]}
    
    def delete_image(self, file_path):
        """Delete image from MinIO"""
        try:
            self.client.remove_object(self.bucket_name, file_path)
            return True
        except Exception as e:
            print(f"Error deleting image: {e}")
            return False
    
    def get_image_url(self, file_path, expiry=3600):
        """Get public URL for image (bucket is public)"""
        try:
            if not file_path:
                return None
            
            # Since bucket is public, we can use direct URLs
            protocol = 'https' if self.minio_secure else 'http'
            public_url = f"{protocol}://{self.public_endpoint}/{self.bucket_name}/{file_path}"
            return public_url
        except Exception as e:
            print(f"Error getting image URL: {e}")
            return None
    
    def get_public_url(self, file_path):
        """Get public URL for image (if bucket is public)"""
        if not file_path:
            return None
        protocol = 'https' if self.minio_secure else 'http'
        return f"{protocol}://{self.public_endpoint}/{self.bucket_name}/{file_path}"
