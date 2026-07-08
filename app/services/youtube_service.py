from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.utils.logger import logger

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


class YouTubeService:
    def __init__(self, credentials: dict | None = None):
        self._service = None
        self._credentials = credentials

    def _get_service(self):
        if self._service:
            return self._service

        if not self._credentials:
            raise RuntimeError(
                "YouTube credentials not provided. Connect your YouTube account via OAuth."
            )

        creds = Credentials(
            token=self._credentials.get("access_token"),
            refresh_token=self._credentials.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._credentials.get("client_id"),
            client_secret=self._credentials.get("client_secret"),
            scopes=SCOPES,
        )

        if not creds.valid and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        self._service = build("youtube", "v3", credentials=creds)
        return self._service

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        category_id: str = "22",
        privacy_status: str = "private",
    ) -> str:
        service = self._get_service()

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
            },
        }

        media = MediaFileUpload(file_path, resumable=True, chunksize=256 * 1024)

        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"YouTube upload progress: {int(status.progress() * 100)}%")

        video_id = response["id"]
        logger.info(f"YouTube video uploaded: {video_id}")
        return video_id

    def update_video_metadata(
        self,
        video_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        service = self._get_service()

        video = service.videos().list(part="snippet", id=video_id).execute()
        if not video["items"]:
            raise ValueError(f"Video not found: {video_id}")

        snippet = video["items"][0]["snippet"]
        if title:
            snippet["title"] = title[:100]
        if description:
            snippet["description"] = description[:5000]
        if tags is not None:
            snippet["tags"] = tags

        response = (
            service.videos()
            .update(part="snippet", body={"id": video_id, "snippet": snippet})
            .execute()
        )

        logger.info(f"YouTube video metadata updated: {video_id}")
        return response

    def get_video_statistics(self, video_id: str) -> dict:
        service = self._get_service()

        response = (
            service.videos().list(part="statistics", id=video_id).execute()
        )

        if not response["items"]:
            raise ValueError(f"Video not found: {video_id}")

        stats = response["items"][0]["statistics"]
        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "favorites": int(stats.get("favoriteCount", 0)),
        }

    def get_channel_statistics(self) -> dict:
        service = self._get_service()

        response = (
            service.channels().list(part="statistics,snippet", mine=True).execute()
        )

        if not response["items"]:
            raise RuntimeError("No channel found for authenticated user")

        item = response["items"][0]
        stats = item["statistics"]
        return {
            "channel_title": item["snippet"]["title"],
            "subscribers": int(stats.get("subscriberCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
        }

    def list_recent_videos(self, max_results: int = 20) -> list[dict]:
        service = self._get_service()

        response = (
            service.search()
            .list(
                part="snippet",
                forMine=True,
                type="video",
                order="date",
                maxResults=max_results,
            )
            .execute()
        )

        videos = []
        for item in response.get("items", []):
            videos.append(
                {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                }
            )

        return videos
