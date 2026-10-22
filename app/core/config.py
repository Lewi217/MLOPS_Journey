from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "mlops-playground"
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
