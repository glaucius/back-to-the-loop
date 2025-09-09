#!/usr/bin/env python3

import os
import sys
import time
import json
import io
from minio import Minio
from minio.error import S3Error

def init_minio():
    """Initialize MinIO with bucket and public policy"""
    
    # MinIO configuration
    minio_endpoint = os.environ.get('MINIO_ENDPOINT', 'minio:9000')
    minio_access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    minio_secret_key = os.environ.get('MINIO_SECRET_KEY', 'minioadmin123')
    bucket_name = os.environ.get('MINIO_BUCKET', 'btl-images')
    
    print(f"Initializing MinIO...")
    print(f"Endpoint: {minio_endpoint}")
    print(f"Bucket: {bucket_name}")
    
    # Wait for MinIO to be ready
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Initialize MinIO client
            client = Minio(
                minio_endpoint,
                access_key=minio_access_key,
                secret_key=minio_secret_key,
                secure=False
            )
            
            # Test connection
            client.list_buckets()
            print("✅ MinIO connection successful!")
            break
            
        except Exception as e:
            retry_count += 1
            print(f"⏳ Waiting for MinIO... (attempt {retry_count}/{max_retries})")
            if retry_count >= max_retries:
                print(f"❌ Failed to connect to MinIO after {max_retries} attempts: {e}")
                return False
            time.sleep(2)
    
    try:
        # Create bucket if it doesn't exist
        if not client.bucket_exists(bucket_name):
            print(f"📦 Creating bucket: {bucket_name}")
            client.make_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' created successfully!")
        else:
            print(f"✅ Bucket '{bucket_name}' already exists!")
        
        # Set public read policy for the bucket
        print(f"🔓 Setting public read policy for bucket: {bucket_name}")
        
        # Public read policy JSON
        public_read_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        # Convert policy to JSON string
        policy_json = json.dumps(public_read_policy)
        
        # Set bucket policy
        client.set_bucket_policy(bucket_name, policy_json)
        print(f"✅ Public read policy set for bucket: {bucket_name}")
        
        # Create folder structure
        folders = [
            "backyards/profile_picture/",
            "backyards/logo/",
            "atletas/profile_picture/",
            "organizacoes/logo/"
        ]
        
        print("📁 Creating folder structure...")
        for folder in folders:
            try:
                # Create a placeholder file to ensure folder exists
                placeholder_content = "# BTL Image Folder"
                placeholder_bytes = placeholder_content.encode('utf-8')
                client.put_object(
                    bucket_name,
                    f"{folder}.gitkeep",
                    data=io.BytesIO(placeholder_bytes),
                    length=len(placeholder_bytes),
                    content_type="text/plain"
                )
                print(f"   ✅ Created folder: {folder}")
            except Exception as e:
                print(f"   ⚠️  Folder {folder} may already exist: {e}")
        
        print("🎉 MinIO initialization completed successfully!")
        
        # Test public access
        test_url = f"http://localhost:9000/{bucket_name}/backyards/profile_picture/.gitkeep"
        print(f"🔍 Test public URL: {test_url}")
        
        return True
        
    except S3Error as e:
        print(f"❌ MinIO S3 Error: {e}")
        return False
    except Exception as e:
        print(f"❌ MinIO initialization error: {e}")
        return False

if __name__ == '__main__':
    success = init_minio()
    if not success:
        sys.exit(1)
    print("✅ MinIO setup completed!")
