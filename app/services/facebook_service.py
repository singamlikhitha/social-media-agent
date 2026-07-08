import httpx
from app.utils.logger import logger

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class FacebookService:
    def __init__(self, access_token: str, page_id: str):
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = GRAPH_API_BASE

    async def create_text_post(self, message: str) -> str:
        url = f"{self.base_url}/{self.page_id}/feed"
        params = {
            "message": message,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        post_id = data["id"]
        logger.info(f"Facebook text post created: {post_id}")
        return post_id

    async def create_photo_post(self, photo_url: str, caption: str = "") -> str:
        url = f"{self.base_url}/{self.page_id}/photos"
        params = {
            "url": photo_url,
            "caption": caption,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        post_id = data.get("post_id", data.get("id"))
        logger.info(f"Facebook photo post created: {post_id}")
        return post_id

    async def create_video_post(self, video_url: str, description: str = "", title: str = "") -> str:
        url = f"{self.base_url}/{self.page_id}/videos"
        params = {
            "file_url": video_url,
            "description": description,
            "title": title,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        video_id = data["id"]
        logger.info(f"Facebook video post created: {video_id}")
        return video_id

    async def create_link_post(self, link: str, message: str = "") -> str:
        url = f"{self.base_url}/{self.page_id}/feed"
        params = {
            "link": link,
            "message": message,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        post_id = data["id"]
        logger.info(f"Facebook link post created: {post_id}")
        return post_id

    async def get_page_insights(self, metric: str = "page_impressions,page_engaged_users", period: str = "day") -> dict:
        url = f"{self.base_url}/{self.page_id}/insights"
        params = {
            "metric": metric,
            "period": period,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        return data.get("data", [])

    async def get_post_insights(self, post_id: str) -> dict:
        url = f"{self.base_url}/{post_id}/insights"
        params = {
            "metric": "post_impressions,post_engaged_users,post_reactions_by_type_total",
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        metrics = {}
        for item in data.get("data", []):
            metrics[item["name"]] = item["values"][0]["value"] if item.get("values") else 0

        return metrics

    async def get_page_info(self) -> dict:
        url = f"{self.base_url}/{self.page_id}"
        params = {
            "fields": "name,fan_count,followers_count,category,about",
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        return data

    def _handle_error(self, error: dict):
        code = error.get("code")
        message = error.get("message", "Unknown error")

        if code == 190:
            raise PermissionError(f"Facebook token expired or invalid: {message}")
        if code == 4:
            raise RuntimeError(f"Facebook rate limit exceeded: {message}")

        raise RuntimeError(f"Facebook API error ({code}): {message}")
