# Complete S3 debug script - add this to a Django management command or view

import boto3
import json
from django.conf import settings
from botocore.exceptions import ClientError, NoCredentialsError
from django.core.management.base import BaseCommand

def comprehensive_s3_debug():
    """Complete S3 debugging to identify the exact issue"""
    
    print("=" * 50)
    print("COMPREHENSIVE S3 DEBUG")
    print("=" * 50)
    
    # 1. Check configuration
    print("\n1. CONFIGURATION CHECK:")
    print(f"   Bucket Name: {settings.AWS_STORAGE_BUCKET_NAME}")
    print(f"   Region: {settings.AWS_S3_REGION_NAME}")
    print(f"   Access Key: {settings.AWS_ACCESS_KEY_ID[:8]}***" if settings.AWS_ACCESS_KEY_ID else "NOT SET")
    print(f"   Secret Key: {'SET' if settings.AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
    
    try:
        # Create S3 client with explicit configuration
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name='us-east-1',  # Force us-east-1 for global endpoint
        )
        
        # 2. Test basic connectivity
        print("\n2. BASIC CONNECTIVITY TEST:")
        try:
            # Get caller identity to verify credentials
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name='us-east-1'
            )
            identity = sts_client.get_caller_identity()
            print(f"   ✅ Valid credentials for User ARN: {identity.get('Arn', 'Unknown')}")
            print(f"   ✅ Account ID: {identity.get('Account', 'Unknown')}")
            
        except Exception as e:
            print(f"   ❌ Credential validation failed: {e}")
            return
        
        # 3. Test bucket access
        print("\n3. BUCKET ACCESS TEST:")
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        # Test HeadBucket (check if bucket exists and is accessible)
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"   ✅ Bucket '{bucket_name}' exists and is accessible")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"   ❌ HeadBucket failed: {error_code}")
            if error_code == '403':
                print("      - This means the bucket exists but you don't have permission")
            elif error_code == '404':
                print("      - This means the bucket doesn't exist or you can't see it")
            return
        
        # 4. Test ListObjects permission
        print("\n4. LIST OBJECTS TEST:")
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            object_count = response.get('KeyCount', 0)
            print(f"   ✅ Can list objects. Found {object_count} objects")
            
            if object_count > 0:
                print("   📁 Sample objects:")
                for obj in response.get('Contents', [])[:3]:
                    print(f"      - {obj['Key']}")
                    
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"   ❌ ListObjects failed: {error_code}")
            print("      - You need 's3:ListBucket' permission")
        
        # 5. Test PutObject permission
        print("\n5. PUT OBJECT TEST:")
        test_key = 'debug-test-file.txt'
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b'This is a test file for debugging S3 permissions',
                ContentType='text/plain'
            )
            print(f"   ✅ Successfully uploaded test file: {test_key}")
            
            # Test GetObject
            try:
                response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
                print(f"   ✅ Successfully downloaded test file")
                
                # Clean up
                s3_client.delete_object(Bucket=bucket_name, Key=test_key)
                print(f"   ✅ Successfully deleted test file")
                
            except ClientError as e:
                print(f"   ❌ GetObject failed: {e.response['Error']['Code']}")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"   ❌ PutObject failed: {error_code}")
            if error_code == 'AccessDenied':
                print("      - You need 's3:PutObject' permission")
                print("      - Check if bucket has a restrictive bucket policy")
        
        # 6. Check bucket policy
        print("\n6. BUCKET POLICY CHECK:")
        try:
            policy_response = s3_client.get_bucket_policy(Bucket=bucket_name)
            policy = json.loads(policy_response['Policy'])
            print("   📋 Bucket has a policy:")
            print(json.dumps(policy, indent=2)[:500] + "..." if len(str(policy)) > 500 else json.dumps(policy, indent=2))
            
            # Check for restrictive policies
            for statement in policy.get('Statement', []):
                if statement.get('Effect') == 'Deny':
                    print("   ⚠️  WARNING: Found DENY statements in bucket policy")
                    
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                print("   ✅ No bucket policy (using IAM permissions only)")
            else:
                print(f"   ❌ Cannot read bucket policy: {e.response['Error']['Code']}")
        
        # 7. Check bucket location
        print("\n7. BUCKET LOCATION:")
        try:
            location_response = s3_client.get_bucket_location(Bucket=bucket_name)
            location = location_response['LocationConstraint']
            actual_region = location if location else 'us-east-1'
            print(f"   📍 Bucket is actually in region: {actual_region}")
            
            if actual_region != settings.AWS_S3_REGION_NAME:
                print(f"   ⚠️  WARNING: Configured region ({settings.AWS_S3_REGION_NAME}) doesn't match actual region ({actual_region})")
                
        except ClientError as e:
            print(f"   ❌ Cannot get bucket location: {e.response['Error']['Code']}")
            
    except NoCredentialsError:
        print("\n❌ ERROR: No AWS credentials found")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")
    print("=" * 50)
class Command(BaseCommand):
    help = "Run comprehensive S3 debug checks"

    def handle(self, *args, **options):
        comprehensive_s3_debug()
# Instructions for running this debug:
# 1. Add this to a Django management command
# 2. Or add it to a view and call comprehensive_s3_debug()
# 3. Check the output to see exactly what permissions are missing