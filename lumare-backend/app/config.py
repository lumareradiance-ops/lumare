from pydantic_settings import BaseSettings


class Settings(BaseSettings):
      database_url: str = "postgresql://user:password@localhost:5432/lumare"

    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 10080
    jwt_algorithm: str = "HS256"

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    shiprocket_email: str = ""
    shiprocket_password: str = ""
    shiprocket_pickup_location: str = "Primary"

    zoho_client_id: str = ""
    zoho_client_secret: str = ""
    zoho_refresh_token: str = ""
    zoho_organization_id: str = ""

    frontend_origin: str = "http://localhost:3000"

    class Config:
              env_file = ".env"


settings = Settings()
