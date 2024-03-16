from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import List

# CORS_ALLOW_ALL_ORIGINS = True
# CORS_ORIGIN_ALLOW = True

# allow all origins


class Settings(BaseSettings):
    
    VERSION: str = "0.1.0"
    
    API_V1_STR: str = f"/api/v{VERSION}"
    
    # ALGORITHM: str = "HS256"

    # 60 minutes * 24 hours * 8 days = 8 days
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        # "http://localhost:3000",
        "http://localhost",
        "http://133.186.171.5",
    ]