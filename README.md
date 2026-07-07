# Social Media Agent

AI-powered multi-platform social media content management platform. Uses Google Gemini for content generation, supports Instagram, Facebook, YouTube, Twitter/X, and LinkedIn with OAuth integrations, smart scheduling, and engagement analytics.

## Features

- **AI Content Generation** — Generate post ideas, captions, hashtags, images, and videos using Google Gemini
- **Multi-Platform Publishing** — Post to Instagram, Facebook, YouTube, Twitter/X, and LinkedIn
- **Cross-Platform Repurposing** — Adapt content across platforms automatically
- **Smart Scheduling** — Schedule posts with optimal timing based on engagement data
- **Analytics Dashboard** — Track impressions, reach, likes, comments, shares across all platforms
- **OAuth Account Management** — Securely connect accounts with encrypted token storage (AES-256-GCM)
- **AI Image & Video Generation** — Generate media with Together.ai, Pollinations.ai, Google Veo, and more
- **Background Processing** — Celery workers for async publishing and analytics sync
- **Plan Tiers** — Free (2 accounts, 10 posts/month), Pro (10 accounts, 100 posts/month), Enterprise

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic 2.0 |
| **Frontend** | Next.js (TypeScript), Tailwind CSS |
| **AI** | Google Gemini 2.5 Flash |
| **Database** | PostgreSQL (production) / SQLite (development) |
| **Queue** | Celery + Redis |
| **Scheduler** | APScheduler |
| **Container** | Docker, Docker Compose, Cloud Run |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials (see [Environment Variables](#environment-variables) below).

### 3. Start the server

```bash
python run.py
```

API runs at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### 4. Start with Docker (full stack)

```bash
docker-compose up
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## Meta (Instagram & Facebook) Integration

### Step 1: Create a Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click **My Apps** > **Create App**
3. Select **Business** type > **Next**
4. Enter app name (e.g., "Social Media Agent") and contact email
5. Click **Create App**

### Step 2: Configure Instagram Basic Display & Graph API

1. In your Meta App Dashboard, go to **Add Products**
2. Add **Instagram Basic Display** — click **Set Up**
3. Add **Instagram Graph API** — click **Set Up**
4. Add **Facebook Login** — click **Set Up**

### Step 3: Configure OAuth Settings

1. Go to **Facebook Login** > **Settings**
2. Under **Valid OAuth Redirect URIs**, add:
   ```
   http://localhost:8080/api/oauth/meta/callback
   ```
   For production, add your Cloud Run URL:
   ```
   https://your-service-url.run.app/api/oauth/meta/callback
   ```
3. Go to **App Settings** > **Basic**
4. Copy your **App ID** and **App Secret**

### Step 4: Set Required Permissions

In **App Review** > **Permissions and Features**, request these permissions:

| Permission | Purpose |
|-----------|---------|
| `instagram_basic` | Read Instagram profile info |
| `instagram_content_publish` | Publish posts, reels, carousels to Instagram |
| `instagram_manage_insights` | Read post and account analytics |
| `pages_show_list` | List Facebook Pages |
| `pages_read_engagement` | Read page engagement metrics |
| `pages_manage_posts` | Publish posts to Facebook Pages |

> **Note:** For development/testing, you can use these permissions in **Development Mode** with test users. For production, submit for **App Review**.

### Step 5: Set Up Instagram Business Account

1. You need an **Instagram Business** or **Creator** account (not Personal)
2. Connect it to a **Facebook Page**:
   - Go to Instagram > Settings > Account > Switch to Professional Account
   - Link to a Facebook Page you manage

### Step 6: Update Environment Variables

Add to your `.env`:

```env
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_REDIRECT_URI=http://localhost:8080/api/oauth/meta/callback
```

### Step 7: Connect Your Account

1. Start the server: `python run.py`
2. Register/login at `http://localhost:3000`
3. Navigate to **Accounts** > **Connect Instagram**
4. The OAuth flow redirects to Meta for authorization
5. After approval, the access token is encrypted and stored

### How It Works

```
User clicks "Connect Instagram"
    │
    ▼
GET /api/oauth/meta/authorize
    │  Generates state token, redirects to Meta
    ▼
Meta OAuth consent screen
    │  User approves permissions
    ▼
GET /api/oauth/meta/callback?code=xxx&state=yyy
    │  Exchanges code for short-lived token
    │  Converts to long-lived token (60-day expiry)
    │  Encrypts and stores token
    ▼
Account connected — ready to publish!
```

### Instagram Publishing Flow

```
POST /api/posts/ (with media_url + caption)
    │
    ▼
create_media_container() → Instagram Graph API
    │  Uploads image/video/reel
    ▼
check_container_status() → Polls until ready
    │  Up to 30 retries with exponential backoff
    ▼
publish_container() → Publishes to feed
    │
    ▼
Post live on Instagram!
```

### Supported Instagram Content Types

| Type | Description | API Method |
|------|------------|-----------|
| **Image** | Single photo post | `create_media_container(type="IMAGE")` |
| **Video** | Video post (MP4) | `create_media_container(type="VIDEO")` |
| **Reel** | Short-form video | `create_media_container(type="REELS")` |
| **Carousel** | Multi-image post | `create_carousel()` |

### Instagram Analytics Available

| Metric | Description |
|--------|------------|
| `impressions` | Number of times content was displayed |
| `reach` | Unique accounts that saw the content |
| `saved` | Number of saves |
| `likes` | Number of likes |
| `comments` | Number of comments |
| `shares` | Number of shares |
| `profile_views` | Profile visits (account-level) |
| `follower_count` | Total followers (account-level) |

---

## YouTube Integration

### Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **YouTube Data API v3**
3. Create **OAuth 2.0 credentials** (Web Application)
4. Add redirect URI: `http://localhost:8080/api/oauth/google/callback`
5. Update `.env`:

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/api/oauth/google/callback
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET` | Yes | Secret for JWT token signing |
| `TOKEN_ENCRYPTION_KEY` | Yes | Base64-encoded 32-byte key for token encryption |
| `META_APP_ID` | For Instagram/FB | Meta App ID from developers.facebook.com |
| `META_APP_SECRET` | For Instagram/FB | Meta App Secret |
| `META_REDIRECT_URI` | For Instagram/FB | OAuth callback URL |
| `GOOGLE_CLIENT_ID` | For YouTube | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | For YouTube | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | For YouTube | Google OAuth callback URL |
| `REDIS_URL` | For Celery | Redis connection URL |
| `TOGETHER_API_KEY` | Optional | Together.ai API key for image generation |
| `REPLICATE_API_TOKEN` | Optional | Replicate API key for video generation |
| `LOG_FORMAT` | Optional | `text` (default) or `json` for structured logs |
| `OTEL_ENABLED` | Optional | `true` to export OpenTelemetry traces/metrics/logs (default `false`) |
| `OTEL_SERVICE_NAME` | Optional | Service name reported to the OTLP backend |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | For telemetry | OTLP collector endpoint (e.g. `http://localhost:4318`) |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Optional | `http/protobuf` (default) or `grpc` |
| `OTEL_EXPORTER_OTLP_HEADERS` | Optional | Comma-separated auth headers for the OTLP backend |

---

## Observability / Telemetry

The backend and Celery worker are instrumented with **OpenTelemetry** and export
**traces, metrics, and logs over OTLP** to any compatible collector (Grafana/Tempo,
Jaeger, Honeycomb, Google Cloud, etc.). Telemetry is **off by default** and fully
no-op unless `OTEL_ENABLED=true`, so local development is unaffected.

### Enable it

```env
OTEL_ENABLED=true
OTEL_SERVICE_NAME=social-media-backend
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318   # your collector
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf           # or grpc (port 4317)
LOG_FORMAT=json                                      # structured, trace-correlated logs
```

Spin up a local collector to try it:

```bash
# Jaeger all-in-one (OTLP http on 4318, UI on 16686)
docker run --rm -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one:latest
```

### What's instrumented

| Signal | Coverage |
|--------|----------|
| **Traces** | FastAPI requests, SQLAlchemy queries, outbound HTTPX calls (social + Gemini APIs), Redis, and Celery tasks — plus custom spans `post.publish` and `gemini.*` |
| **Metrics** | HTTP server RED metrics (auto), plus business counters/histograms (see below) |
| **Logs** | JSON logs with `trace_id`/`span_id` correlation; optionally shipped via OTLP (`OTEL_EXPORT_LOGS`) |

### Business metrics

| Metric | Type | Attributes |
|--------|------|-----------|
| `smm.posts.published` | counter | `platform`, `status` |
| `smm.posts.publish.duration` | histogram (ms) | `platform`, `status` |
| `smm.content.generated` | counter | `operation`, `platform` |
| `smm.gemini.requests` | counter | `operation`, `model`, `status` |
| `smm.gemini.duration` | histogram (ms) | `operation`, `model` |
| `smm.media.generated` | counter | `kind`, `source`, `status` |
| `smm.oauth.token_refresh` | counter | `platform`, `status` |

In production, `deploy.yml` sets these via GitHub secrets/vars
(`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`,
`OTEL_EXPORTER_OTLP_PROTOCOL`) with `OTEL_ENABLED=true` and `LOG_FORMAT=json`.

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login (returns JWT) |
| POST | `/api/auth/refresh` | Refresh token |

### Content Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/content/generate-ideas` | Generate AI content ideas |
| GET | `/api/content/ideas` | List stored ideas |
| POST | `/api/content/repurpose` | Adapt content across platforms |
| POST | `/api/content/optimize-caption` | Improve a caption with AI |
| POST | `/api/content/suggest-hashtags` | Generate hashtag suggestions |
| POST | `/api/content/create-content` | Full AI content creation |
| POST | `/api/content/modify-content` | Rewrite content with instructions |
| POST | `/api/content/generate-image` | AI image generation |
| POST | `/api/content/generate-video` | AI video generation |

### Post Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/posts/` | Create a scheduled post |
| GET | `/api/posts/` | List all posts |
| GET | `/api/posts/{id}` | Get post details |
| PUT | `/api/posts/{id}` | Update a post |
| DELETE | `/api/posts/{id}` | Delete a post |
| POST | `/api/posts/{id}/publish-now` | Publish immediately |
| GET | `/api/posts/optimal-times/{platform}` | Get best posting times |

### OAuth & Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/oauth/meta/authorize` | Connect Instagram/Facebook |
| GET | `/api/oauth/google/authorize` | Connect YouTube |
| GET | `/api/oauth/twitter/authorize` | Connect Twitter/X |
| GET | `/api/oauth/linkedin/authorize` | Connect LinkedIn |
| GET | `/api/accounts/` | List connected accounts |
| DELETE | `/api/accounts/{id}` | Disconnect account |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/posts/{id}` | Get post metrics |
| GET | `/api/analytics/{platform}/overview` | Platform summary (30 days) |
| POST | `/api/analytics/sync` | Trigger analytics sync |
| GET | `/api/analytics/{platform}/top-posts` | Top performing posts |

### Media & Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/media/upload` | Upload file (max 100MB) |
| POST | `/api/media/upload-multiple` | Bulk upload |
| GET | `/api/health/` | Health check |
| GET | `/api/health/config` | Configuration status |
| GET | `/api/health/scheduler` | Scheduler status |

---

## Project Structure

```
app/
├── main.py                    # FastAPI app entry point
├── config.py                  # Environment configuration
├── database.py                # SQLAlchemy setup
├── celery_app.py              # Celery configuration
│
├── auth/                      # Authentication
│   ├── models.py              # User model
│   ├── router.py              # Login, register endpoints
│   ├── service.py             # Password hashing, JWT
│   └── dependencies.py        # Auth middleware
│
├── oauth/                     # OAuth integrations
│   ├── meta_oauth.py          # Instagram/Facebook OAuth (Graph API v21.0)
│   ├── google_oauth.py        # YouTube OAuth
│   ├── twitter_oauth.py       # Twitter/X OAuth
│   ├── linkedin_oauth.py      # LinkedIn OAuth
│   ├── token_manager.py       # AES-256-GCM token encryption
│   └── router.py              # Account management
│
├── services/                  # Business logic
│   ├── gemini_service.py      # AI content generation (text, images, video)
│   ├── instagram_service.py   # Instagram Graph API client
│   ├── youtube_service.py     # YouTube Data API v3 client
│   ├── facebook_service.py    # Facebook page posting
│   ├── twitter_service.py     # Twitter/X API
│   ├── linkedin_service.py    # LinkedIn API
│   ├── content_service.py     # Content orchestration
│   ├── posting_service.py     # Publishing dispatcher
│   ├── scheduler_service.py   # APScheduler management
│   └── analytics_service.py   # Metrics aggregation
│
├── models/                    # Database models
├── schemas/                   # Pydantic request/response DTOs
├── routers/                   # API route definitions
├── middleware/                 # CORS, rate limiting, plan enforcement
├── tasks/                     # Celery async tasks
└── utils/                     # Helpers (templates, time optimizer)

frontend/                      # Next.js React app
setup_wizard/                  # Interactive CLI setup
```

---

## Deployment

### Docker Compose (Development)

```bash
docker-compose up
```

### Cloud Run (Production)

```bash
# Build and deploy backend
gcloud builds submit --tag gcr.io/PROJECT_ID/social-media-agent
gcloud run deploy social-media-agent \
  --image gcr.io/PROJECT_ID/social-media-agent \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="META_APP_ID=xxx,META_APP_SECRET=xxx,..."
```

Update your Meta OAuth redirect URI to match the Cloud Run service URL.

---

## Troubleshooting

### Meta/Instagram Issues

| Issue | Solution |
|-------|---------|
| "Invalid OAuth redirect URI" | Ensure redirect URI in Meta App matches `META_REDIRECT_URI` in `.env` exactly |
| "Instagram account not found" | Account must be Business/Creator type, linked to a Facebook Page |
| "Permissions not granted" | Check App Review status; in dev mode, add test users under Roles |
| "Media container stuck processing" | Videos may take up to 5 minutes; the app retries 30 times with backoff |
| "Token expired" | Long-lived tokens last 60 days; reconnect the account to refresh |

### General Issues

| Issue | Solution |
|-------|---------|
| "Module not found" | Run `pip install -r requirements.txt` |
| "Database error" | Check `DATABASE_URL` in `.env`; for SQLite, it creates automatically |
| "Scheduler not running" | Check `GET /api/health/scheduler` for status |
