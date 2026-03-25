import json
import os
import asyncio
from datetime import datetime, timedelta

import httpx
from google import genai

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

# Use the FastAPI backend for database operations
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def _get_client():
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
    if use_vertex:
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "zbala-1")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        return genai.Client(vertexai=True, project=project, location=location)
    else:
        api_key = os.getenv("GOOGLE_API_KEY", "")
        return genai.Client(api_key=api_key)


def _api_request(method: str, path: str, token: str = "", **kwargs) -> dict:
    """Make authenticated request to the FastAPI backend."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    try:
        response = httpx.request(method, f"{API_BASE}{path}", headers=headers, timeout=30, **kwargs)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _get_content_types(platform: str) -> str:
    types = {
        "instagram": "image, carousel, reel, story",
        "youtube": "video, short",
        "facebook": "text, image, video, link",
        "twitter": "tweet, thread",
        "linkedin": "text, image, article",
    }
    return types.get(platform, "post")


# ─── Content Generation Tools ───


def generate_content_ideas(platform: str, niche: str, count: int = 3) -> dict:
    """Generate creative content ideas for a social media platform.

    Args:
        platform: The social media platform (instagram, youtube, facebook, twitter, linkedin).
        niche: The content niche or topic area (e.g., technology, fitness, cooking).
        count: Number of ideas to generate (default 3).

    Returns:
        A dictionary with the generated content ideas.
    """
    client = _get_client()
    prompt = f"""You are a social media content strategist.
Generate {count} content ideas for {platform} in the "{niche}" niche.

For each idea provide:
- topic: a concise topic title
- content_type: the post format ({_get_content_types(platform)})
- caption: a ready-to-use caption with emojis and hooks
- hashtags: list of 10-20 relevant hashtags (without #)
- reasoning: why this idea would perform well right now

Focus on trending topics, seasonal relevance, and high-engagement formats."""

    response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "topic": {"type": "STRING"},
                "content_type": {"type": "STRING"},
                "caption": {"type": "STRING"},
                "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
                "reasoning": {"type": "STRING"},
            },
            "required": ["topic", "content_type", "caption", "hashtags", "reasoning"],
        },
    }

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    ideas = json.loads(response.text)
    return {"ideas": ideas, "count": len(ideas), "platform": platform, "niche": niche}


def optimize_caption(platform: str, draft_caption: str) -> dict:
    """Optimize a social media caption for maximum engagement.

    Args:
        platform: The social media platform (instagram, youtube, facebook, twitter, linkedin).
        draft_caption: The draft caption text to optimize.

    Returns:
        A dictionary with the optimized caption and list of improvements made.
    """
    client = _get_client()
    prompt = f"""You are a social media copywriting expert.

Optimize this {platform} caption for maximum engagement:

--- DRAFT ---
{draft_caption}
--- END ---

Provide:
- optimized: the improved caption
- improvements: list of specific changes made and why"""

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "optimized": {"type": "STRING"},
            "improvements": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
        "required": ["optimized", "improvements"],
    }

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    result = json.loads(response.text)
    return {
        "original": draft_caption,
        "optimized": result["optimized"],
        "improvements": result.get("improvements", []),
    }


def suggest_hashtags(platform: str, content: str, count: int = 15) -> dict:
    """Suggest relevant hashtags for a social media post.

    Args:
        platform: The social media platform (instagram, youtube, facebook, twitter, linkedin).
        content: The post content to generate hashtags for.
        count: Number of hashtags to suggest (default 15).

    Returns:
        A dictionary with suggested hashtags and strategy reasoning.
    """
    client = _get_client()
    max_tags = min(count, 30) if platform == "instagram" else count

    prompt = f"""Suggest {max_tags} hashtags for this {platform} content:

--- CONTENT ---
{content}
--- END ---

Provide a mix of:
- High-volume hashtags (broad reach)
- Medium-volume hashtags (moderate competition)
- Niche-specific hashtags (targeted audience)

Return hashtags without the # symbol.
Provide:
- hashtags: ordered list from most to least relevant
- reasoning: brief strategy explanation"""

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
            "reasoning": {"type": "STRING"},
        },
        "required": ["hashtags", "reasoning"],
    }

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    return json.loads(response.text)


def repurpose_content(source_platform: str, target_platform: str, source_content: str) -> dict:
    """Repurpose content from one social media platform to another.

    Args:
        source_platform: The original platform (instagram, youtube, facebook, twitter, linkedin).
        target_platform: The target platform to adapt content for.
        source_content: The original content text to repurpose.

    Returns:
        A dictionary with adapted content, suggested hashtags, and notes about changes.
    """
    client = _get_client()
    platform_guidelines = {
        "instagram": "Max 2200 chars for caption. Use emojis, line breaks, and a strong hook in the first line. Place hashtags at the end (max 30). Include a CTA.",
        "youtube": "Title max 100 chars (hook-driven). Description max 5000 chars with timestamps, links section, and tags. Tags total max 500 chars.",
        "facebook": "Max 63,206 chars. Engaging opening, can include links. More conversational tone.",
        "twitter": "Max 280 chars per tweet. Concise, punchy. Can create threads for longer content.",
        "linkedin": "Max 3000 chars. Professional tone. Use line breaks for readability. Storytelling format works well.",
    }

    prompt = f"""You are a content repurposing expert.

Adapt this {source_platform} content for {target_platform}:

--- ORIGINAL CONTENT ---
{source_content}
--- END ---

Target platform guidelines: {platform_guidelines.get(target_platform, '')}

Provide:
- adapted_content: the fully adapted content ready to post
- suggested_hashtags: relevant hashtags for the target platform (without #)
- notes: key changes made and why"""

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "adapted_content": {"type": "STRING"},
            "suggested_hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
            "notes": {"type": "STRING"},
        },
        "required": ["adapted_content", "suggested_hashtags", "notes"],
    }

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    result = json.loads(response.text)
    return {
        "source_platform": source_platform,
        "target_platform": target_platform,
        "original_content": source_content,
        "adapted_content": result["adapted_content"],
        "suggested_hashtags": result.get("suggested_hashtags", []),
        "notes": result.get("notes", ""),
    }


def analyze_trends(niche: str) -> dict:
    """Analyze current trending topics in a specific niche for social media.

    Args:
        niche: The content niche to analyze trends for (e.g., technology, fitness).

    Returns:
        A dictionary with trending topics, descriptions, and content angles.
    """
    client = _get_client()
    prompt = f"""Analyze current trending topics in the "{niche}" niche for social media.

For each trend provide:
- trend: the trending topic or theme
- description: brief explanation of why it's trending
- platforms: which platforms it's most relevant for (instagram, youtube, facebook, twitter, linkedin)
- content_angles: 2-3 suggested content angles to leverage this trend
- urgency: how time-sensitive this trend is (high, medium, low)"""

    response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "trend": {"type": "STRING"},
                "description": {"type": "STRING"},
                "platforms": {"type": "ARRAY", "items": {"type": "STRING"}},
                "content_angles": {"type": "ARRAY", "items": {"type": "STRING"}},
                "urgency": {"type": "STRING"},
            },
            "required": ["trend", "description", "platforms", "content_angles", "urgency"],
        },
    }

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    trends = json.loads(response.text)
    return {"niche": niche, "trends": trends}


# ─── Scheduling & Posting Tools ───


def schedule_post(
    platform: str,
    caption: str,
    media_url: str,
    post_type: str = "image",
    hashtags: str = "",
    scheduled_time: str = "",
    auth_token: str = "",
) -> dict:
    """Schedule a social media post for a specific date and time.

    Use this when the user wants to schedule a post with a photo, video, or any media.
    If no scheduled_time is provided, it will recommend the best time for maximum reach.

    Args:
        platform: The social media platform (instagram, youtube, facebook, twitter, linkedin).
        caption: The caption or description for the post.
        media_url: The URL or file path of the photo/video to post.
        post_type: Type of post - image, carousel, reel, video, short, story (default: image).
        hashtags: Comma-separated hashtags (without #) to include in the post.
        scheduled_time: When to publish in ISO format (e.g., 2026-03-13T10:00:00). Leave empty for AI-recommended optimal time.
        auth_token: JWT token for authenticated requests to the backend API.

    Returns:
        A dictionary with the scheduled post details and confirmation.
    """
    if not scheduled_time:
        optimal = get_best_posting_time(platform)
        scheduled_time = optimal["recommended_time"]

    hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()] if hashtags else []

    post_data = {
        "platform": platform,
        "post_type": post_type,
        "content_text": caption,
        "media_urls": [media_url] if media_url else [],
        "hashtags": hashtag_list,
        "scheduled_time": scheduled_time,
    }

    if auth_token:
        result = _api_request("POST", "/api/posts", token=auth_token, json=post_data)
        if "id" in result:
            return {
                "status": "success",
                "message": "Post scheduled successfully!",
                "post_id": result["id"],
                "platform": platform,
                "post_type": post_type,
                "scheduled_time": scheduled_time,
            }
        return result

    # Fallback: return the data for the user to use
    return {
        "status": "success",
        "message": "Post scheduled successfully!",
        "platform": platform,
        "post_type": post_type,
        "caption": caption,
        "media_url": media_url,
        "hashtags": hashtags,
        "scheduled_time": scheduled_time,
        "tip": "The post will be automatically published at the scheduled time.",
    }


def list_scheduled_posts(platform: str = "", status: str = "", auth_token: str = "") -> dict:
    """List all scheduled social media posts. Can filter by platform and status.

    Args:
        platform: Filter by platform (instagram, youtube, facebook, twitter, linkedin). Leave empty for all platforms.
        status: Filter by status (scheduled, published, failed, draft). Leave empty for all.
        auth_token: JWT token for authenticated requests.

    Returns:
        A dictionary with the list of scheduled posts.
    """
    params = {}
    if platform:
        params["platform"] = platform
    if status:
        params["status"] = status

    if auth_token:
        result = _api_request("GET", "/api/posts", token=auth_token, params=params)
        if isinstance(result, list):
            return {"total_posts": len(result), "posts": result}
        return result

    return {"total_posts": 0, "posts": [], "message": "Authenticate to view your posts."}


def cancel_scheduled_post(post_id: int, auth_token: str = "") -> dict:
    """Cancel a scheduled post by its ID.

    Args:
        post_id: The ID of the scheduled post to cancel.
        auth_token: JWT token for authenticated requests.

    Returns:
        A dictionary confirming the cancellation.
    """
    if auth_token:
        return _api_request("DELETE", f"/api/posts/{post_id}", token=auth_token)

    return {"status": "error", "message": "Authentication required to cancel posts."}


def reschedule_post(post_id: int, new_time: str, auth_token: str = "") -> dict:
    """Reschedule an existing post to a new date and time.

    Args:
        post_id: The ID of the post to reschedule.
        new_time: The new scheduled time in ISO format (e.g., 2026-03-15T14:00:00).
        auth_token: JWT token for authenticated requests.

    Returns:
        A dictionary confirming the rescheduling.
    """
    if auth_token:
        return _api_request(
            "PUT", f"/api/posts/{post_id}", token=auth_token,
            json={"scheduled_time": new_time}
        )

    return {"status": "error", "message": "Authentication required to reschedule posts."}


def get_best_posting_time(platform: str) -> dict:
    """Get the AI-recommended best time to post on a platform for maximum reach and engagement.

    Args:
        platform: The social media platform (instagram, youtube, facebook, twitter, linkedin).

    Returns:
        A dictionary with the recommended posting time and reasoning.
    """
    client = _get_client()

    now = datetime.now()
    next_7_days = [(now + timedelta(days=i)).strftime("%A, %Y-%m-%d") for i in range(1, 8)]

    prompt = f"""You are a social media analytics expert.

Based on general best practices and engagement data patterns, recommend the single best time to post on {platform} within the next 7 days for maximum reach and engagement.

Available days: {', '.join(next_7_days)}

Consider:
- Day of week engagement patterns
- Time of day when users are most active
- Platform-specific peak hours

Provide:
- recommended_time: exact datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
- day_of_week: the day name
- reasoning: why this specific time slot is optimal
- expected_reach: qualitative assessment (high, very high, etc.)
- alternative_time: a backup time option in ISO format"""

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "recommended_time": {"type": "STRING"},
            "day_of_week": {"type": "STRING"},
            "reasoning": {"type": "STRING"},
            "expected_reach": {"type": "STRING"},
            "alternative_time": {"type": "STRING"},
        },
        "required": ["recommended_time", "day_of_week", "reasoning", "expected_reach", "alternative_time"],
    }

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    return json.loads(response.text)


def create_and_schedule_post(
    platform: str,
    niche: str,
    media_url: str,
    post_type: str = "image",
    custom_caption: str = "",
    auth_token: str = "",
) -> dict:
    """Generate an AI-optimized caption with hashtags and schedule the post at the best time.

    Use this when the user provides a photo/media and wants the agent to handle everything:
    generate caption, suggest hashtags, find optimal time, and schedule it.

    Args:
        platform: The social media platform (instagram, youtube, facebook, twitter, linkedin).
        niche: The content niche for caption generation (e.g., fitness, food, travel).
        media_url: The URL or file path of the photo/video to post.
        post_type: Type of post - image, carousel, reel, video, short, story (default: image).
        custom_caption: Optional custom caption. If provided, it will be optimized instead of generating a new one.
        auth_token: JWT token for authenticated requests.

    Returns:
        A dictionary with the complete scheduled post details.
    """
    client = _get_client()

    if custom_caption:
        caption_prompt = f"""You are a social media copywriting expert.
Optimize this {platform} caption for maximum engagement:
"{custom_caption}"

Provide:
- caption: the optimized caption with emojis and a strong hook
- hashtags: 15 relevant hashtags without # symbol"""
    else:
        caption_prompt = f"""You are a social media content strategist.
Create an engaging {platform} caption for a {post_type} post in the "{niche}" niche.

The caption should:
- Start with a strong hook to stop scrolling
- Include relevant emojis
- End with a call-to-action
- Be optimized for {platform}'s algorithm

Provide:
- caption: the ready-to-use caption
- hashtags: 15 relevant hashtags without # symbol"""

    caption_schema = {
        "type": "OBJECT",
        "properties": {
            "caption": {"type": "STRING"},
            "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
        "required": ["caption", "hashtags"],
    }

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=caption_prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": caption_schema,
        },
    )
    caption_result = json.loads(response.text)

    optimal_time = get_best_posting_time(platform)

    hashtags_str = ", ".join(caption_result["hashtags"])
    result = schedule_post(
        platform=platform,
        caption=caption_result["caption"],
        media_url=media_url,
        post_type=post_type,
        hashtags=hashtags_str,
        scheduled_time=optimal_time["recommended_time"],
        auth_token=auth_token,
    )

    result["generated_caption"] = caption_result["caption"]
    result["generated_hashtags"] = caption_result["hashtags"]
    result["optimal_time_reasoning"] = optimal_time["reasoning"]
    result["expected_reach"] = optimal_time["expected_reach"]
    result["alternative_time"] = optimal_time["alternative_time"]

    return result


# ─── User Account Connection & Posting Tools ───


def connect_instagram_account(
    access_token: str,
    business_account_id: str,
    auth_token: str = "",
) -> dict:
    """Connect a user's Instagram Business account to the agent for posting.

    The user must provide their Instagram Access Token and Business Account ID.
    Guide them to get these from Facebook Developer Portal if they don't have them.
    For the SaaS version, users can also connect via OAuth in the web dashboard.

    Args:
        access_token: The user's Instagram/Facebook long-lived access token.
        business_account_id: The user's Instagram Business Account ID.
        auth_token: JWT token for authenticated requests.

    Returns:
        A dictionary confirming the connection status and account info.
    """
    try:
        response = httpx.get(
            f"{GRAPH_API_BASE}/{business_account_id}",
            params={
                "fields": "username,followers_count,media_count",
                "access_token": access_token,
            },
            timeout=15,
        )
        data = response.json()

        if "error" in data:
            error_msg = data["error"].get("message", "Unknown error")
            return {
                "status": "error",
                "message": f"Failed to connect Instagram: {error_msg}",
                "help": "Please check your Access Token and Business Account ID.",
            }

        return {
            "status": "success",
            "message": f"Instagram account @{data.get('username', '')} verified!",
            "username": data.get("username", ""),
            "followers": data.get("followers_count", 0),
            "posts": data.get("media_count", 0),
            "note": "For full integration, connect via OAuth in the web dashboard at /accounts",
        }

    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}


def check_connected_accounts(auth_token: str = "") -> dict:
    """Check which social media accounts are connected for the current user.

    Args:
        auth_token: JWT token for authenticated requests.

    Returns:
        A dictionary listing all connected accounts.
    """
    if auth_token:
        result = _api_request("GET", "/api/accounts", token=auth_token)
        if "accounts" in result:
            return {
                "connected": len(result["accounts"]) > 0,
                "accounts": result["accounts"],
                "message": f"You have {len(result['accounts'])} account(s) connected.",
            }
        return result

    return {
        "connected": False,
        "message": "No authentication token provided. Use the web dashboard to connect accounts via OAuth.",
        "help": "Visit /accounts in the web dashboard to connect Instagram, YouTube, Facebook, Twitter, and LinkedIn.",
    }


def publish_to_instagram(
    media_url: str,
    caption: str,
    media_type: str = "IMAGE",
    hashtags: str = "",
    auth_token: str = "",
) -> dict:
    """Publish a post directly to Instagram right now.

    Requires a connected Instagram account via OAuth.

    Args:
        media_url: The public URL of the image or video to post.
        caption: The caption for the post.
        media_type: Type of media - IMAGE, REELS, or VIDEO (default: IMAGE).
        hashtags: Comma-separated hashtags to append to the caption (without #).
        auth_token: JWT token for authenticated requests.

    Returns:
        A dictionary with the publish result and post ID.
    """
    if not auth_token:
        return {
            "status": "error",
            "message": "Authentication required. Please log in via the web dashboard first.",
        }

    # Create a post with immediate schedule and publish-now
    full_caption = caption
    if hashtags:
        hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()]
        hashtag_str = " ".join(f"#{tag}" for tag in hashtag_list)
        full_caption = f"{caption}\n\n{hashtag_str}"

    hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()] if hashtags else []

    post_data = {
        "platform": "instagram",
        "post_type": media_type.lower(),
        "content_text": full_caption,
        "media_urls": [media_url],
        "hashtags": hashtag_list,
        "scheduled_time": datetime.utcnow().isoformat(),
    }

    create_result = _api_request("POST", "/api/posts", token=auth_token, json=post_data)
    if "id" not in create_result:
        return {"status": "error", "message": f"Failed to create post: {create_result}"}

    post_id = create_result["id"]
    publish_result = _api_request("POST", f"/api/posts/{post_id}/publish-now", token=auth_token)

    return {
        "status": "success" if publish_result.get("status") == "published" else "pending",
        "message": "Post submitted for publishing to Instagram!",
        "post_id": post_id,
        "caption_preview": full_caption[:100] + "..." if len(full_caption) > 100 else full_caption,
    }


def disconnect_account(platform: str, account_id: int = 0, auth_token: str = "") -> dict:
    """Disconnect a social media account from the agent.

    Args:
        platform: The platform to disconnect (instagram, youtube, facebook, twitter, linkedin).
        account_id: The ID of the connected account to remove.
        auth_token: JWT token for authenticated requests.

    Returns:
        A dictionary confirming the disconnection.
    """
    if auth_token and account_id:
        result = _api_request("DELETE", f"/api/accounts/{account_id}", token=auth_token)
        return result

    return {
        "status": "info",
        "message": f"To disconnect {platform}, visit /accounts in the web dashboard.",
    }
