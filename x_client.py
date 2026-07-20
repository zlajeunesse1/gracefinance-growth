import os
from dataclasses import dataclass

import tweepy
from dotenv import load_dotenv


@dataclass(frozen=True)
class XCredentials:
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str

    @classmethod
    def from_environment(cls) -> "XCredentials":
        load_dotenv(".env")

        names = {
            "api_key": "X_API_KEY",
            "api_secret": "X_API_SECRET",
            "access_token": "X_ACCESS_TOKEN",
            "access_token_secret": "X_ACCESS_TOKEN_SECRET",
        }

        values = {field: os.getenv(name) for field, name in names.items()}
        missing = [names[field] for field, value in values.items() if not value]

        if missing:
            raise RuntimeError(
                "Missing required X environment variables: "
                + ", ".join(missing)
            )

        return cls(**values)


def get_x_client() -> tweepy.Client:
    credentials = XCredentials.from_environment()

    return tweepy.Client(
        consumer_key=credentials.api_key,
        consumer_secret=credentials.api_secret,
        access_token=credentials.access_token,
        access_token_secret=credentials.access_token_secret,
        wait_on_rate_limit=True,
    )


def verify_x_connection() -> dict:
    response = get_x_client().get_me(user_auth=True)

    if response.data is None:
        raise RuntimeError("X authenticated but returned no user information.")

    return {
        "id": str(response.data.id),
        "username": response.data.username,
        "name": response.data.name,
    }


def publish_x_post(text: str) -> str:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("X post text cannot be empty.")

    if len(cleaned_text) > 280:
        raise ValueError(
            f"X post is {len(cleaned_text)} characters; maximum is 280."
        )

    response = get_x_client().create_tweet(
        text=cleaned_text,
        user_auth=True,
    )

    if not response.data or "id" not in response.data:
        raise RuntimeError(f"X returned an unexpected response: {response}")

    return str(response.data["id"])
