# Dataset Specification

## Purpose
Define the structure and metadata for visual heritage datasets.

## Data Categories
1. **Heritage Images**: Photographs of cultural heritage sites
2. **Metadata**: Location, date, cultural context, conservation status
3. **Evidence Documents**: Historical records, scholarly articles, restoration reports
4. **Annotations**: Bounding boxes, labels, and classifications

## Data Schema

### Images
- `image_id`: Unique identifier
- `filename`: Original file name
- `capture_date`: Date of capture
- `location`: GPS coordinates
- `site_id`: Heritage site identifier
- `cultural_context`: Cultural/historical significance
- `conservation_status`: Current state
- `photographer`: Attribution
- `license`: Usage rights

### Evidence Documents
- `evidence_id`: Unique identifier
- `title`: Document title
- `authors`: List of authors
- `publication_date`: Date published
- `source`: Journal or repository
- `url`: Digital reference
- `content_type`: Article, report, photograph, etc.
- `relevance_score`: Connection to specific heritage elements

## Data Processing Pipeline
1. **Ingestion**: Raw data collection and validation
2. **Preprocessing**: Image normalization, metadata extraction
3. **Annotation**: Expert labeling and classification
4. **Indexing**: Vector embedding generation
5. **Storage**: Structured database and vector index

## Data Governance
- Privacy: No personal data in public images
- Attribution: Proper credit for all sources
- Accessibility: Open access where legally possible
- Versioning: Track dataset changes over time
