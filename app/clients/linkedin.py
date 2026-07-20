from loguru import logger
import httpx

from app.config import get_settings


class LinkedInClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def publish(self, text: str) -> dict:
        if self.settings.dry_run:
            logger.info("DRY RUN LinkedIn post: {}", text)
            return {"status": "dry_run", "platform": "linkedin", "text": text}

        if not self.settings.linkedin_ready:
            raise RuntimeError("LinkedIn credentials are incomplete")

        url = "https://api.linkedin.com/rest/posts"
        headers = {
            "Authorization": f"Bearer {self.settings.linkedin_access_token}",
            "LinkedIn-Version": self.settings.linkedin_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        payload = {
            "author": self.settings.linkedin_author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        post_id = response.headers.get("x-restli-id")
        logger.info("Published LinkedIn post: {}", post_id)
        return {
            "status": "published",
            "platform": "linkedin",
            "post_id": post_id,
        }
