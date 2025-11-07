/**
 * Python Backend API Client
 * 
 * This module provides functions to interact with the Python FastAPI backend
 * for Hindi OCR text extraction using Indic-TrOCR model.
 */

import axios, { AxiosInstance } from 'axios';

interface OCRResponse {
  success: boolean;
  text: string;
  confidence: number;
  processing_time: number;
  image_info: {
    width: number;
    height: number;
    mode: string;
    format: string;
  };
  device: string;
}

interface OCRError {
  success: false;
  error: string;
  detail?: string;
}

class PythonBackendClient {
  private client: AxiosInstance;

  constructor(baseURL?: string) {
    this.client = axios.create({
      baseURL: baseURL || process.env.PYTHON_BACKEND_URL || 'http://localhost:8000',
      timeout: 60000, // 60 seconds for OCR processing
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Check if the Python backend is healthy
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.data.status === 'healthy';
    } catch (error) {
      console.error('Python backend health check failed:', error);
      return false;
    }
  }

  /**
   * Extract Hindi text from an image file
   * @param imageFile - File object or Buffer
   * @param filename - Name of the file
   */
  async extractTextFromFile(
    imageFile: File | Buffer,
    filename: string
  ): Promise<OCRResponse> {
    try {
      const formData = new FormData();
      
      if (imageFile instanceof Buffer) {
        // Node.js environment
        const blob = new Blob([imageFile]);
        formData.append('image', blob, filename);
      } else {
        // Browser environment
        formData.append('image', imageFile);
      }

      const response = await this.client.post<OCRResponse>(
        '/api/ocr/extract',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      return response.data;
    } catch (error: any) {
      console.error('OCR extraction failed:', error);
      throw new Error(
        error.response?.data?.detail || 'Failed to extract text from image'
      );
    }
  }

  /**
   * Extract Hindi text from an image URL
   * @param imageUrl - URL of the image
   * @param preprocess - Apply image preprocessing (default: true)
   */
  async extractTextFromUrl(
    imageUrl: string,
    preprocess: boolean = true
  ): Promise<OCRResponse> {
    try {
      const response = await this.client.post<OCRResponse>(
        '/api/ocr/extract-url',
        {
          image_url: imageUrl,
          preprocess,
          max_length: 512,
        }
      );

      return response.data;
    } catch (error: any) {
      console.error('OCR extraction from URL failed:', error);
      throw new Error(
        error.response?.data?.detail || 'Failed to extract text from URL'
      );
    }
  }

  /**
   * Extract Hindi text from a base64 encoded image
   * @param base64Image - Base64 encoded image string
   * @param preprocess - Apply image preprocessing (default: true)
   */
  async extractTextFromBase64(
    base64Image: string,
    preprocess: boolean = true
  ): Promise<OCRResponse> {
    try {
      const response = await this.client.post<OCRResponse>(
        '/api/ocr/extract-base64',
        {
          image_base64: base64Image,
          preprocess,
          max_length: 512,
        }
      );

      return response.data;
    } catch (error: any) {
      console.error('OCR extraction from base64 failed:', error);
      throw new Error(
        error.response?.data?.detail || 'Failed to extract text from base64'
      );
    }
  }

  /**
   * Extract text from S3 URL (convenience method)
   * @param s3Key - S3 object key
   * @param bucketName - S3 bucket name
   */
  async extractTextFromS3(
    s3Key: string,
    bucketName?: string
  ): Promise<OCRResponse> {
    const bucket = bucketName || process.env.AWS_S3_BUCKET_NAME;
    const region = process.env.AWS_REGION || 'us-east-1';
    const s3Url = `https://${bucket}.s3.${region}.amazonaws.com/${s3Key}`;

    return this.extractTextFromUrl(s3Url);
  }

  /**
   * Get model information
   */
  async getModelInfo(): Promise<any> {
    try {
      const response = await this.client.get('/api/ocr/model-info');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get model info:', error);
      throw new Error('Failed to get model information');
    }
  }
}

// Export singleton instance
export const pythonBackend = new PythonBackendClient();

// Export class for custom instances
export default PythonBackendClient;

// Export types
export type { OCRResponse, OCRError };
