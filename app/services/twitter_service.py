import httpx
from app.utils.logger import logger

TWITTER_API_BASE = "https://api.twitter.com/2"


class TwitterService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = TWITTER_API_BASE
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def create_tweet(self, text: str, media_urls: list[str] | None = None, reply_to: str | None = None) -> str:
        url = f"{self.base_url}/tweets"

        payload = {"text": text[:280]}

        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}

        if media_urls:
            media_ids = []
            for media_url in media_urls:
                media_id = await self._upload_media(media_url)
                if media_id:
                    media_ids.append(media_id)
            if media_ids:
                payload["media"] = {"media_ids": media_ids}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=self._headers)
            data = response.json()

        if "errors" in data:
            raise RuntimeError(f"Twitter API error: {data['errors']}")

        tweet_id = data["data"]["id"]
        logger.info(f"Tweet created: {tweet_id}")
        return tweet_id

    async def create_thread(self, tweets: list[str]) -> list[str]:
        tweet_ids = []
        reply_to = None

        for text in tweets:
            tweet_id = await self.create_tweet(text, reply_to=reply_to)
            tweet_ids.append(tweet_id)
            reply_to = tweet_id

        logger.info(f"Thread created with {len(tweet_ids)} tweets")
        return tweet_ids

    async def delete_tweet(self, tweet_id: str) -> bool:
        url = f"{self.base_url}/tweets/{tweet_id}"

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.delete(url, headers=self._headers)
            data = response.json()

        return data.get("data", {}).get("deleted", False)

    async def get_tweet(self, tweet_id: str) -> dict:
        url = f"{self.base_url}/tweets/{tweet_id}"
        params = {
            "tweet.fields": "public_metrics,created_at",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params, headers=self._headers)
            data = response.json()

        if "errors" in data:
            raise RuntimeError(f"Twitter API error: {data['errors']}")

        return data.get("data", {})

    async def get_tweet_metrics(self, tweet_id: str) -> dict:
        tweet = await self.get_tweet(tweet_id)
        metrics = tweet.get("public_metrics", {})
        return {
            "likes": metrics.get("like_count", 0),
            "retweets": metrics.get("retweet_count", 0),
            "replies": metrics.get("reply_count", 0),
            "quotes": metrics.get("quote_count", 0),
            "impressions": metrics.get("impression_count", 0),
            "bookmarks": metrics.get("bookmark_count", 0),
        }

    async def get_user_me(self) -> dict:
        url = f"{self.base_url}/users/me"
        params = {
            "user.fields": "public_metrics,profile_image_url,description",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params, headers=self._headers)
            data = response.json()

        return data.get("data", {})

    async def _upload_media(self, media_url: str) -> str | None:
        """Upload media via Twitter v1.1 media upload endpoint."""
        upload_url = "https://upload.twitter.com/1.1/media/upload.json"

        try:
            # Download the media first
            async with httpx.AsyncClient(timeout=30) as client:
                media_resp = await client.get(media_url)
                media_data = media_resp.content

            # Upload to Twitter
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    upload_url,
                    files={"media_data": media_data},
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                data = response.json()

            return data.get("media_id_string")
        except Exception as e:
            logger.error(f"Twitter media upload failed: {e}")
            return None
