import asyncio
import httpx
from app.utils.logger import logger

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class InstagramService:
    def __init__(self, access_token: str | None = None, account_id: str | None = None):
        self.access_token = access_token
        self.account_id = account_id
        self.base_url = GRAPH_API_BASE

    def _check_configured(self):
        if not self.access_token or not self.account_id:
            raise RuntimeError(
                "Instagram credentials not provided. Connect your Instagram account via OAuth."
            )

    async def create_media_container(
        self,
        image_url: str,
        caption: str,
        media_type: str = "IMAGE",
        is_carousel_item: bool = False,
    ) -> str:
        self._check_configured()
        url = f"{self.base_url}/{self.account_id}/media"

        params = {
            "access_token": self.access_token,
            "caption": caption,
        }

        if media_type == "REELS":
            params["media_type"] = "REELS"
            params["video_url"] = image_url
        elif media_type == "VIDEO":
            params["media_type"] = "VIDEO"
            params["video_url"] = image_url
        else:
            params["image_url"] = image_url

        if is_carousel_item:
            params["is_carousel_item"] = "true"
            params.pop("caption", None)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        logger.info(f"Created media container: {data['id']}")
        return data["id"]

    async def check_container_status(self, container_id: str) -> str:
        self._check_configured()
        url = f"{self.base_url}/{container_id}"
        params = {
            "fields": "status_code",
            "access_token": self.access_token,
        }

        max_attempts = 30
        delay = 2

        for attempt in range(max_attempts):
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url, params=params)
                data = response.json()

            status = data.get("status_code")
            if status == "FINISHED":
                return status
            if status == "ERROR":
                raise RuntimeError(f"Media container failed: {data}")

            await asyncio.sleep(min(delay * (1.5 ** attempt), 30))

        raise TimeoutError("Media container processing timed out")

    async def publish_container(self, container_id: str) -> str:
        self._check_configured()
        url = f"{self.base_url}/{self.account_id}/media_publish"
        params = {
            "creation_id": container_id,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        logger.info(f"Published media: {data['id']}")
        return data["id"]

    async def create_carousel(self, items: list[dict], caption: str) -> str:
        self._check_configured()
        child_ids = []
        for item in items:
            container_id = await self.create_media_container(
                image_url=item["url"],
                caption="",
                media_type=item.get("type", "IMAGE"),
                is_carousel_item=True,
            )
            await self.check_container_status(container_id)
            child_ids.append(container_id)

        url = f"{self.base_url}/{self.account_id}/media"
        params = {
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        await self.check_container_status(data["id"])
        return await self.publish_container(data["id"])

    async def get_media_insights(self, media_id: str) -> dict:
        self._check_configured()
        url = f"{self.base_url}/{media_id}/insights"
        params = {
            "metric": "impressions,reach,saved,likes,comments,shares",
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        metrics = {}
        for item in data.get("data", []):
            metrics[item["name"]] = item["values"][0]["value"]

        return metrics

    async def get_account_insights(self, period: str = "day", days: int = 30) -> dict:
        self._check_configured()
        url = f"{self.base_url}/{self.account_id}/insights"
        params = {
            "metric": "impressions,reach,profile_views,follower_count",
            "period": period,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            data = response.json()

        if "error" in data:
            self._handle_error(data["error"])

        return data.get("data", [])

    async def get_account_info(self) -> dict:
        self._check_configured()
        url = f"{self.base_url}/{self.account_id}"
        params = {
            "fields": "username,followers_count,media_count,biography",
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
            raise PermissionError(f"Instagram token expired or invalid: {message}")
        if code == 4:
            raise RuntimeError(f"Instagram rate limit exceeded: {message}")

        raise RuntimeError(f"Instagram API error ({code}): {message}")
