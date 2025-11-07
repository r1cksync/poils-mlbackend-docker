"""
Test script for Hindi OCR API
"""
import requests
import base64
import json
from pathlib import Path


# API Base URL
BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_upload_image(image_path: str):
    """Test image upload endpoint"""
    print(f"\n📤 Testing image upload: {image_path}")
    
    if not Path(image_path).exists():
        print(f"❌ File not found: {image_path}")
        return False
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(f"{BASE_URL}/api/ocr/extract", files=files)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Extracted Text: {data['text']}")
        print(f"⏱️ Processing Time: {data['processing_time']}s")
        print(f"📊 Confidence: {data['confidence']}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_url_image(image_url: str):
    """Test URL endpoint"""
    print(f"\n🌐 Testing URL extraction: {image_url}")
    
    payload = {
        "image_url": image_url,
        "preprocess": True,
        "max_length": 512
    }
    
    response = requests.post(
        f"{BASE_URL}/api/ocr/extract-url",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Extracted Text: {data['text']}")
        print(f"⏱️ Processing Time: {data['processing_time']}s")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_base64_image(image_path: str):
    """Test base64 endpoint"""
    print(f"\n🔤 Testing base64 extraction: {image_path}")
    
    if not Path(image_path).exists():
        print(f"❌ File not found: {image_path}")
        return False
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    payload = {
        "image_base64": f"data:image/jpeg;base64,{image_base64}",
        "preprocess": True,
        "max_length": 512
    }
    
    response = requests.post(
        f"{BASE_URL}/api/ocr/extract-base64",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Extracted Text: {data['text']}")
        print(f"⏱️ Processing Time: {data['processing_time']}s")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_model_info():
    """Test model info endpoint"""
    print("\n📋 Testing model info endpoint...")
    response = requests.get(f"{BASE_URL}/api/ocr/model-info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Hindi OCR API Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    # Test 2: Model info
    results.append(("Model Info", test_model_info()))
    
    # Test 3: Image upload (if test image exists)
    test_image = "test_hindi.jpg"
    if Path(test_image).exists():
        results.append(("Upload Image", test_upload_image(test_image)))
    else:
        print(f"\n⚠️ Skipping upload test - {test_image} not found")
        print(f"Create a test Hindi text image as '{test_image}' to test upload")
    
    # Test 4: URL extraction (example)
    # Uncomment and add a valid image URL to test
    # test_url = "https://example.com/hindi_text.jpg"
    # results.append(("URL Image", test_url_image(test_url)))
    
    # Test 5: Base64 extraction
    if Path(test_image).exists():
        results.append(("Base64 Image", test_base64_image(test_image)))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    print(f"\n🎯 Total: {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print(f"Make sure the server is running at {BASE_URL}")
        print("\nStart the server with:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
