/**
 * Example Next.js API Route for OCR Processing
 * 
 * Path: backend/nextjs-backend/app/api/documents/ocr/route.ts
 * 
 * This route accepts document uploads, stores them in S3,
 * sends to Python backend for OCR, and saves results to MongoDB.
 */

import { NextRequest, NextResponse } from 'next/server';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import connectDB from '@/lib/db';
import Document from '@/models/Document';
import { verifyToken } from '@/middleware/auth';
import axios from 'axios';

// Initialize S3 client
const s3Client = new S3Client({
  region: process.env.AWS_REGION!,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Verify authentication
    const token = request.cookies.get('token')?.value;
    if (!token) {
      return NextResponse.json(
        { success: false, message: 'Unauthorized' },
        { status: 401 }
      );
    }

    const decoded = await verifyToken(token);
    const userId = decoded.userId;

    // Parse form data
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json(
        { success: false, message: 'No file provided' },
        { status: 400 }
      );
    }

    console.log(`Processing document: ${file.name} for user: ${userId}`);

    // Connect to MongoDB
    await connectDB();

    // Generate unique S3 key
    const timestamp = Date.now();
    const s3Key = `documents/${userId}/${timestamp}-${file.name}`;

    // Upload to S3
    const fileBuffer = Buffer.from(await file.arrayBuffer());
    
    await s3Client.send(
      new PutObjectCommand({
        Bucket: process.env.AWS_S3_BUCKET_NAME!,
        Key: s3Key,
        Body: fileBuffer,
        ContentType: file.type,
      })
    );

    console.log(`File uploaded to S3: ${s3Key}`);

    // Create document record in MongoDB
    const document = await Document.create({
      userId,
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      s3Key,
      status: 'processing',
    });

    // Send to Python backend for OCR
    try {
      const ocrFormData = new FormData();
      ocrFormData.append('image', file);

      const ocrResponse = await axios.post(
        `${PYTHON_BACKEND_URL}/api/ocr/extract`,
        ocrFormData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 60000, // 60 seconds
        }
      );

      const { text, confidence, processing_time } = ocrResponse.data;

      console.log(`OCR completed in ${processing_time}s with confidence ${confidence}`);

      // Update document with OCR results
      document.ocrText = text;
      document.ocrConfidence = confidence;
      document.status = 'completed';
      await document.save();

      return NextResponse.json({
        success: true,
        message: 'Document processed successfully',
        document: {
          id: document._id,
          fileName: document.fileName,
          ocrText: text,
          confidence,
          processingTime: processing_time,
        },
      });

    } catch (ocrError: any) {
      console.error('OCR processing failed:', ocrError);

      // Update document status to failed
      document.status = 'failed';
      document.error = ocrError.message;
      await document.save();

      return NextResponse.json(
        {
          success: false,
          message: 'OCR processing failed',
          error: ocrError.message,
          documentId: document._id,
        },
        { status: 500 }
      );
    }

  } catch (error: any) {
    console.error('Document processing error:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Internal server error',
        error: error.message,
      },
      { status: 500 }
    );
  }
}

/**
 * GET endpoint to retrieve document OCR results
 */
export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('token')?.value;
    if (!token) {
      return NextResponse.json(
        { success: false, message: 'Unauthorized' },
        { status: 401 }
      );
    }

    const decoded = await verifyToken(token);
    const userId = decoded.userId;

    await connectDB();

    // Get all documents for user
    const documents = await Document.find({ userId })
      .sort({ createdAt: -1 })
      .select('fileName fileSize status ocrText ocrConfidence createdAt');

    return NextResponse.json({
      success: true,
      documents,
    });

  } catch (error: any) {
    console.error('Error fetching documents:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Failed to fetch documents',
        error: error.message,
      },
      { status: 500 }
    );
  }
}
