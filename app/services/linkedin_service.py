import httpx
from app.utils.logger import logger

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
LINKEDIN_REST_BASE = "https://api.linkedin.com/rest"


class LinkedInService:
    def __init__(self, access_token: str, person_id: str):
        self.access_token = access_token
        self.person_id = person_id
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401",
        }

    async def create_text_post(self, text: str) -> str:
        url = f"{LINKEDIN_REST_BASE}/posts"

        payload = {
            "author": f"urn:li:person:{self.person_id}",
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=self._headers)

        if response.status_code not in (200, 201):
            raise RuntimeError(f"LinkedIn post failed ({response.status_code}): {response.text}")

        # LinkedIn returns the post URN in the x-restli-id header
        post_id = response.headers.get("x-restli-id", "unknown")
        logger.info(f"LinkedIn text post created: {post_id}")
        return post_id

    async def create_image_post(self, text: str, image_url: str) -> str:
        # Step 1: Initialize upload
        init_url = f"{LINKEDIN_REST_BASE}/images?action=initializeUpload"
        init_payload = {
            "initializeUploadRequest": {
                "owner": f"urn:li:person:{self.person_id}",
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            init_resp = await client.post(init_url, json=init_payload, headers=self._headers)
            init_data = init_resp.json()

        upload_url = init_data["value"]["uploadUrl"]
        image_urn = init_data["value"]["image"]

        # Step 2: Download image and upload to LinkedIn
        async with httpx.AsyncClient(timeout=60) as client:
            img_resp = await client.get(image_url)
            img_data = img_resp.content

            await client.put(
                upload_url,
                content=img_data,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/octet-stream",
                },
            )

        # Step 3: Create post with image
        post_url = f"{LINKEDIN_REST_BASE}/posts"
        payload = {
            "author": f"urn:li:person:{self.person_id}",
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "title": "Image",
                    "id": image_urn,
                }
            },
            "lifecycleState": "PUBLISHED",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(post_url, json=payload, headers=self._headers)

        if response.status_code not in (200, 201):
            raise RuntimeError(f"LinkedIn image post failed ({response.status_code}): {response.text}")

        post_id = response.headers.get("x-restli-id", "unknown")
        logger.info(f"LinkedIn image post created: {post_id}")
        return post_id

    async def create_article_post(self, text: str, article_url: str, title: str = "") -> str:
        url = f"{LINKEDIN_REST_BASE}/posts"

        payload = {
            "author": f"urn:li:person:{self.person_id}",
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "article": {
                    "source": article_url,
                    "title": title,
                }
            },
            "lifecycleState": "PUBLISHED",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=self._headers)

        if response.status_code not in (200, 201):
            raise RuntimeError(f"LinkedIn article post failed ({response.status_code}): {response.text}")

        post_id = response.headers.get("x-restli-id", "unknown")
        logger.info(f"LinkedIn article post created: {post_id}")
        return post_id

    async def get_profile(self) -> dict:
        url = f"{LINKEDIN_API_BASE}/userinfo"

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=self._headers)
            data = response.json()

        return data

    async def get_post_stats(self, post_urn: str) -> dict:
        url = f"{LINKEDIN_REST_BASE}/socialMetadata/{post_urn}"

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=self._headers)

        if response.status_code != 200:
            return {}

        data = response.json()
        return {
            "likes": data.get("totalShareStatistics", {}).get("likeCount", 0),
            "comments": data.get("totalShareStatistics", {}).get("commentCount", 0),
            "shares": data.get("totalShareStatistics", {}).get("shareCount", 0),
            "impressions": data.get("totalShareStatistics", {}).get("impressionCount", 0),
        }
