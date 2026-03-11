# Social Media Content Scheduler

AI-powered content scheduler for Instagram and YouTube. Uses Google Gemini to generate post ideas, optimize content, and repurpose across platforms.

## Features

- **AI Content Generation** - Generate post ideas based on trending topics using Gemini
- **Cross-Platform Repurposing** - Adapt Instagram content for YouTube and vice versa
- **Smart Scheduling** - Optimize posting times based on engagement analytics
- **Caption Optimization** - AI-powered caption and hashtag suggestions
- **Analytics Dashboard** - Track engagement metrics across both platforms
- **Automated Publishing** - Schedule and auto-publish posts at optimal times

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run setup wizard

```bash
python -m setup_wizard.wizard
```

This guides you through configuring:
- Google Gemini API key
- Instagram Graph API credentials
- YouTube Data API v3 OAuth

### 3. Start the server

```bash
python run.py
```

The API runs at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## API Endpoints

### Content Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/content/generate-ideas` | Generate AI content ideas |
| GET | `/api/content/ideas` | List stored ideas |
| POST | `/api/content/repurpose` | Adapt content across platforms |
| POST | `/api/content/optimize-caption` | Improve a caption with AI |
| POST | `/api/content/suggest-hashtags` | Generate hashtag suggestions |

### Post Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/posts/` | Create a scheduled post |
| GET | `/api/posts/` | List all posts |
| PUT | `/api/posts/{id}` | Update a post |
| DELETE | `/api/posts/{id}` | Delete a post |
| POST | `/api/posts/{id}/publish-now` | Publish immediately |
| GET | `/api/posts/optimal-times/{platform}` | Get best posting times |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/posts/{id}` | Get post metrics |
| GET | `/api/analytics/{platform}/overview` | Platform summary |
| POST | `/api/analytics/sync` | Trigger analytics sync |
| GET | `/api/analytics/{platform}/top-posts` | Top performing posts |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | Health check |
| GET | `/api/health/config` | Configuration status |
| GET | `/api/health/scheduler` | Scheduler status |

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Environment configuration
├── database.py          # SQLAlchemy setup
├── models/              # Database models
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic
│   ├── gemini_service.py      # AI content generation
│   ├── instagram_service.py   # Instagram API client
│   ├── youtube_service.py     # YouTube API client
│   ├── content_service.py     # Content orchestration
│   ├── analytics_service.py   # Analytics aggregation
│   ├── scheduler_service.py   # Post scheduling
│   └── posting_service.py     # Publishing dispatcher
├── routers/             # API endpoint definitions
└── utils/               # Helpers (templates, time optimizer)
setup_wizard/            # Interactive API setup CLI
```

## Tech Stack

- **Python** + **FastAPI** - REST API framework
- **Google Gemini** - AI content generation
- **Instagram Graph API** - Instagram publishing and insights
- **YouTube Data API v3** - YouTube uploads and analytics
- **SQLAlchemy** + **SQLite** - Database
- **APScheduler** - Background task scheduling
