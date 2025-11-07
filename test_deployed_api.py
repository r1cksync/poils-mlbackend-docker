"""
Test script for deployed Hindi OCR API on Vercel
URL: https://poils-mlbackend-docker.vercel.app/
"""
import requests
import json
from pathlib import Path


# API Configuration
API_URL = "https://poils-mlbackend-docker.vercel.app"
IMAGE_PATH = r"C:\Users\user\Downloads\68c1585c325a7ac16aa794f764093f6b.jpg"


def test_health():
    """Test if API is healthy"""
    print("\n" + "="*60)
    print("🔍 Testing API Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ API is healthy!")
            return True
        else:
            print("❌ API health check failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_extract_hindi_text():
    """Extract Hindi text from the downloaded image"""
    print("\n" + "="*60)
    print("📤 Extracting Hindi Text from Image")
    print("="*60)
    
    # Check if image exists
    if not Path(IMAGE_PATH).exists():
        print(f"❌ Image not found at: {IMAGE_PATH}")
        print("Please make sure the image exists at the specified path.")
        return False
    
    print(f"📁 Image: {IMAGE_PATH}")
    print(f"📊 Size: {Path(IMAGE_PATH).stat().st_size / 1024:.2f} KB")
    
    try:
        # Open and send image
        with open(IMAGE_PATH, 'rb') as f:
            files = {'image': ('maxresdefault.jpg', f, 'image/jpeg')}
            
            print("\n⏳ Sending request to API...")
            print(f"URL: {API_URL}/api/ocr/extract")
            
            response = requests.post(
                f"{API_URL}/api/ocr/extract",
                files=files,
                timeout=60  # 60 seconds timeout
            )
        
        print(f"\n📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "="*60)
            print("✅ SUCCESS - Text Extracted!")
            print("="*60)
            
            print(f"\n📝 Extracted Hindi Text:")
            print("-" * 60)
            print(result.get('text', ''))
            print("-" * 60)
            
            print(f"\n📊 Metadata:")
            print(f"  • Confidence: {result.get('confidence', 0):.2%}")
            print(f"  • Processing Time: {result.get('processing_time', 0):.2f} seconds")
            print(f"  • Device: {result.get('device', 'N/A')}")
            
            if 'image_info' in result:
                img_info = result['image_info']
                print(f"\n🖼️  Image Info:")
                print(f"  • Dimensions: {img_info.get('width')}x{img_info.get('height')}")
                print(f"  • Format: {img_info.get('format')}")
                print(f"  • Mode: {img_info.get('mode')}")
            
            # Check if there was an error in the result
            if 'error' in result:
                print(f"\n⚠️  Note: {result['error']}")
            
            return True
            
        elif response.status_code == 503:
            print("\n⏰ Model is loading on Hugging Face...")
            print("This happens on the first request or after inactivity.")
            print("Please wait 20-30 seconds and try again.")
            return False
            
        else:
            print(f"\n❌ Error Response:")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("\n⏱️  Request timed out!")
        print("The API took too long to respond. This might happen if:")
        print("  • The model is loading (first request)")
        print("  • The server is under heavy load")
        print("Please try again in a few moments.")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_model_info():
    """Get information about the OCR model"""
    print("\n" + "="*60)
    print("📋 Getting Model Information")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/api/ocr/model-info", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            info = response.json()
            print("\n🤖 Model Details:")
            print(f"  • Model: {info.get('model_name', 'N/A')}")
            print(f"  • Service: {info.get('service_type', 'N/A')}")
            print(f"  • Status: {'Loaded' if info.get('is_loaded') else 'Not Loaded'}")
            print(f"  • Has API Key: {info.get('has_api_key', False)}")
            print(f"  • Rate Limit: {info.get('rate_limit', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to get model info")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 Hindi OCR API Test Suite")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Image: {IMAGE_PATH}")
    print("="*60)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health()))
    
    # Test 2: Model Info
    results.append(("Model Info", test_model_info()))
    
    # Test 3: Extract Hindi Text (main test)
    results.append(("Hindi Text Extraction", test_extract_hindi_text()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\n🎯 Total: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Your API is working perfectly!")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        if not results[2][1]:  # If Hindi extraction failed
            print("\nℹ️  If this is the first request or model is loading:")
            print("   Wait 20-30 seconds and run this script again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
