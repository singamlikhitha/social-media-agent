# Testing Guide

## Prerequisites

- Python 3.10+
- A Google Gemini API key (get one at https://aistudio.google.com/apikey)
- (Optional) Instagram Graph API credentials
- (Optional) YouTube Data API v3 credentials

## Step 1: Install Dependencies

```bash
cd social-media-agent
pip install -r requirements.txt
```

## Step 2: Configure Environment

### Option A: Use the Setup Wizard (Recommended)

```bash
python -m setup_wizard.wizard
```

This interactive CLI walks you through entering your API keys and saves them to a `.env` file.

### Option B: Manual Configuration

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
TIMEZONE=UTC
DATABASE_URL=sqlite:///./social_media_agent.db
LOG_LEVEL=INFO
```

> Note: Instagram and YouTube credentials are optional. The app works with just a Gemini API key for content generation features.

## Step 3: Start the Server

```bash
python run.py
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

## Step 4: Open API Docs

Open your browser and go to:

```
http://localhost:8000/docs
```

This is the **Swagger UI** — an interactive page where you can test every endpoint directly from the browser.

## Step 5: Test Endpoints

### 5.1 Health Check (no API keys needed)

```bash
curl http://localhost:8000/api/health/
```

Expected response:
```json
{"status": "healthy", "service": "Social Media Content Scheduler"}
```

### 5.2 Check Configuration Status

```bash
curl http://localhost:8000/api/health/config
```

Expected response:
```json
{
  "gemini_configured": true,
  "instagram_configured": false,
  "youtube_configured": false,
  "database_url": "sqlite:///***",
  "timezone": "UTC"
}
```

### 5.3 Check Scheduler Status

```bash
curl http://localhost:8000/api/health/scheduler
```

### 5.4 Generate Content Ideas (requires Gemini API key)

```bash
curl -X POST http://localhost:8000/api/content/generate-ideas \
  -H "Content-Type: application/json" \
  -d '{"platform": "instagram", "niche": "fitness", "count": 3}'
```

This calls Google Gemini to generate 3 Instagram content ideas in the fitness niche.

### 5.5 Suggest Hashtags

```bash
curl -X POST http://localhost:8000/api/content/suggest-hashtags \
  -H "Content-Type: application/json" \
  -d '{"platform": "instagram", "content": "Morning workout routine with resistance bands", "count": 15}'
```

### 5.6 Optimize a Caption

```bash
curl -X POST http://localhost:8000/api/content/optimize-caption \
  -H "Content-Type: application/json" \
  -d '{"platform": "instagram", "draft_caption": "Had a great workout today at the gym"}'
```

### 5.7 Repurpose Content (Instagram to YouTube)

```bash
curl -X POST http://localhost:8000/api/content/repurpose \
  -H "Content-Type: application/json" \
  -d '{
    "source_platform": "instagram",
    "target_platform": "youtube",
    "source_content": "5 morning habits that changed my life. Wake up at 5am, cold shower, journal for 10 mins, workout, read for 30 mins. Start tomorrow! #morningroutine #habits #selfimprovement"
  }'
```

### 5.8 Create a Scheduled Post

```bash
curl -X POST http://localhost:8000/api/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "post_type": "image",
    "content_text": "Morning workout vibes! Start your day right.",
    "hashtags": ["fitness", "workout", "motivation"],
    "scheduled_time": "2026-03-15T10:00:00",
    "media_urls": ["https://example.com/image.jpg"]
  }'
```

### 5.9 List All Posts

```bash
curl http://localhost:8000/api/posts/
```

Filter by platform:
```bash
curl "http://localhost:8000/api/posts/?platform=instagram"
```

Filter by status:
```bash
curl "http://localhost:8000/api/posts/?status=scheduled"
```

### 5.10 Get Optimal Posting Times

```bash
curl http://localhost:8000/api/posts/optimal-times/instagram
```

### 5.11 Get Platform Analytics Overview

```bash
curl "http://localhost:8000/api/analytics/instagram/overview?days=30"
```

### 5.12 List Stored Content Ideas

```bash
curl http://localhost:8000/api/content/ideas
```

### 5.13 Convert an Idea to a Scheduled Post

```bash
curl -X POST "http://localhost:8000/api/content/ideas/1/create-post?scheduled_time=2026-03-20T14:00:00"
```

## Testing with PowerShell (Windows)

If `curl` doesn't work on Windows, use PowerShell:

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/api/health/"

# Generate ideas
$body = @{platform="instagram"; niche="fitness"; count=3} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/content/generate-ideas" -Method Post -Body $body -ContentType "application/json"
```

## What Works Without Instagram/YouTube Credentials

These features work with **only a Gemini API key**:
- Content idea generation
- Caption optimization
- Hashtag suggestions
- Content repurposing (Instagram <-> YouTube)
- Post scheduling (creates DB entries, won't publish without platform credentials)
- Optimal time recommendations (returns defaults until you have engagement data)

## What Requires Platform Credentials

- **Instagram credentials needed for**: Publishing posts, fetching insights/analytics
- **YouTube credentials needed for**: Uploading videos, fetching video stats/channel stats

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `GEMINI_API_KEY not set` | Create `.env` file or run setup wizard |
| `Instagram token expired` | Re-run setup wizard to exchange for new long-lived token |
| `YouTube OAuth token invalid` | Delete `youtube_token.json` and re-run setup wizard |
| Port 8000 in use | Change port in `run.py`: `uvicorn.run(..., port=8001)` |
| `sqlite3.OperationalError` | Delete `social_media_agent.db` and restart (resets data) |
