# Architecture

## High-Level Flow
1. **Image Input**: User uploads or selects an image
2. **Embedding Generation**: Convert image to vector using ML model
3. **Vector Retrieval**: Search FAISS for similar vectors
4. **Confidence Check**: Determine if match is confident or unknown
5. **Evidence Retrieval**: Gather supporting documents/metadata
6. **Grounded RAG**: Generate explanation with evidence
7. **API Response**: Return results to frontend

## Component Details

### Frontend (Next.js/TypeScript)
- Image upload interface
- Results display with confidence scores
- Evidence visualization
- Cultural context panels

### Backend (FastAPI/Python)
- REST API endpoints
- Authentication/authorization
- Image processing pipeline
- Vector search coordination
- RAG generation

### ML Pipeline (PyTorch/HuggingFace)
- Image embedding models (CLIP, ViT)
- Confidence estimation
- Unknown detection thresholds

### Vector Store (FAISS)
- Index management
- Similarity search
- Index persistence

### Database (PostgreSQL)
- Image metadata storage
- Evidence documents
- User interactions
- Audit logs

## Data Flow
