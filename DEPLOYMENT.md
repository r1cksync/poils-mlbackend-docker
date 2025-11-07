# Quick Start Guide - Hindi OCR API

## 🚀 Quick Setup (Local Development)

### Option 1: Python Virtual Environment

```powershell
# Navigate to the directory
cd "backend/docker-python backend"

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker

```powershell
# Build the Docker image
docker build -t hindi-ocr-api .

# Run the container
docker run -p 8000:8000 hindi-ocr-api

# Or use docker-compose
docker-compose up
```

## 📡 Testing the API

Once the server is running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Test with Python Script

```powershell
# Create a test Hindi image (or use your own)
# Then run the test script
python test_api.py
```

### Test with cURL

```powershell
# Upload image file
curl -X POST "http://localhost:8000/api/ocr/extract" `
  -F "image=@test_hindi.jpg"

# From URL
curl -X POST "http://localhost:8000/api/ocr/extract-url" `
  -H "Content-Type: application/json" `
  -d '{\"image_url\": \"https://example.com/hindi.jpg\"}'
```

## 🌐 Deploy to Render

### Step 1: Prepare Repository

```powershell
# Initialize git (if not already)
git init
git add .
git commit -m "Add Hindi OCR API"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Deploy on Render

1. **Go to** [Render Dashboard](https://dashboard.render.com/)

2. **Click** "New +" → "Web Service"

3. **Connect** your GitHub repository

4. **Configure:**
   - **Name**: hindi-ocr-api
   - **Environment**: Docker
   - **Region**: Choose closest to users
   - **Branch**: main
   - **Root Directory**: `backend/docker-python backend`
   - **Docker Build Context**: `.`
   - **Dockerfile Path**: `Dockerfile`

5. **Instance Type**: 
   - **Free**: Limited resources (may be slow)
   - **Starter ($7/month)**: 512MB RAM - Recommended minimum
   - **Standard ($25/month)**: 2GB RAM - Better performance

6. **Add Disk** (Important for model caching):
   - **Name**: model-cache
   - **Mount Path**: `/app/model_cache`
   - **Size**: 5GB

6. **Environment Variables** (optional):
   ```
   MODEL_NAME=microsoft/trocr-base-printed
   DEBUG=False
   ```
   
   **Note:** You can use `microsoft/trocr-large-printed` for better accuracy (but requires more RAM and is slower).

8. **Click** "Create Web Service"

### Step 3: Wait for Deployment

- First deployment takes 5-10 minutes (downloads ML model)
- Subsequent deployments are faster (model is cached)
- Check logs for progress

### Step 4: Test Your Deployment

```powershell
# Replace with your Render URL
$API_URL = "https://your-service-name.onrender.com"

# Test health
curl "$API_URL/health"

# Test OCR
curl -X POST "$API_URL/api/ocr/extract" `
  -F "image=@test_hindi.jpg"
```

## 🔗 Integration with Next.js Backend

### Update Next.js Backend Environment

Add to `backend/nextjs-backend/.env.local`:

```env
# Python Backend URL (after Render deployment)
PYTHON_BACKEND_URL=https://your-service-name.onrender.com
```

### Example Integration Code

```typescript
// backend/nextjs-backend/lib/pythonApi.ts
import axios from 'axios';

const pythonApi = axios.create({
  baseURL: process.env.PYTHON_BACKEND_URL,
  timeout: 60000, // 60 seconds for OCR processing
});

export async function extractHindiText(imageFile: File): Promise<string> {
  const formData = new FormData();
  formData.append('image', imageFile);

  const response = await pythonApi.post('/api/ocr/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });

  return response.data.text;
}

export async function extractFromUrl(imageUrl: string): Promise<string> {
  const response = await pythonApi.post('/api/ocr/extract-url', {
    image_url: imageUrl,
    preprocess: true
  });

  return response.data.text;
}
```

## 📊 Performance Tips

### 1. **Use GPU Instance** (Render doesn't support GPU on free/starter)
   - For GPU support, consider AWS/GCP/Azure
   - CPU inference: 2-5 seconds per image
   - GPU inference: 0.5-1 second per image

### 2. **Optimize Images Before Upload**
   - Resize large images client-side
   - Maximum: 2048x2048 pixels
   - Compress JPEG to 80-90% quality

### 3. **Enable Model Caching**
   - Use persistent disk on Render
   - Model downloads only once
   - Startup time: 30-60 seconds after cache

### 4. **Set Proper Timeouts**
   - Frontend: 60+ seconds
   - Backend: 30+ seconds
   - OCR processing can take time

## 🐛 Troubleshooting

### Issue: Model Download Fails

**Solution**: Increase timeout or pre-download model

```python
# Download model before deploying
from transformers import VisionEncoderDecoderModel, TrOCRProcessor
model = VisionEncoderDecoderModel.from_pretrained('surajp/trocr-base-hindi')
processor = TrOCRProcessor.from_pretrained('surajp/trocr-base-hindi')
```

### Issue: Out of Memory

**Symptoms**: Container crashes, 502 errors

**Solutions**:
- Upgrade to larger instance (2GB+ RAM)
- Reduce `MAX_IMAGE_DIMENSION` in config
- Enable swap memory

### Issue: Slow First Request

**Cause**: Cold start - model loading

**Solution**:
- Keep service active with health check pings
- Use Render's paid plan (no sleep)
- Model stays in memory after first load

### Issue: CORS Errors

**Solution**: Already configured in FastAPI

```python
# Already in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## 📝 Example Usage

### Python Client

```python
import requests

# Upload image
with open('hindi_doc.jpg', 'rb') as f:
    response = requests.post(
        'https://your-api.onrender.com/api/ocr/extract',
        files={'image': f}
    )
    print(response.json()['text'])
```

### JavaScript/TypeScript

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);

const response = await fetch(
  'https://your-api.onrender.com/api/ocr/extract',
  { method: 'POST', body: formData }
);

const data = await response.json();
console.log(data.text);
```

### cURL

```bash
curl -X POST "https://your-api.onrender.com/api/ocr/extract" \
  -F "image=@document.jpg"
```

## 🎯 Next Steps

1. ✅ **Test locally** - Ensure everything works
2. ✅ **Deploy to Render** - Follow deployment guide
3. ✅ **Integrate with Next.js** - Update environment variables
4. ⏭️ **Implement RAG chatbot** - Use extracted text for Q&A
5. ⏭️ **Add batch processing** - Process multiple documents
6. ⏭️ **Improve accuracy** - Fine-tune model on your data

## 📚 Resources

- **Indic-TrOCR Model**: https://huggingface.co/surajp/trocr-base-hindi
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Render Docs**: https://render.com/docs
- **TrOCR Paper**: https://arxiv.org/abs/2109.10282

## 💡 Tips for Production

1. **Environment Variables**: Use Render's secret management
2. **Monitoring**: Set up health check alerts
3. **Logging**: Enable structured logging
4. **Rate Limiting**: Add rate limiting middleware
5. **Authentication**: Add API key authentication
6. **Caching**: Cache results for duplicate images
7. **Queue**: Use Celery/Redis for async processing

Happy OCR! 🚀
