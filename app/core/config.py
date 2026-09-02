from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Kanyakumari RideShare"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google Maps
    GOOGLE_MAPS_API_KEY: str
    
    # Razorpay
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    
    # Firebase
    FCM_SERVER_KEY: str
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"
    
    # SMS
    SMS_API_KEY: str
    SMS_SENDER_ID: str = "RIDESH"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    
    # Service area: Kolachel–Poovar coast + Marthandam–Chirayankeezhu surroundings
    SERVICE_AREA_BOUNDARY: str = (
        '[[76.948,8.238],[77.265,8.238],[77.265,8.425],[76.948,8.425],[76.948,8.238]]'
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def geofence_coordinates(self) -> List[List[float]]:
        return json.loads(self.SERVICE_AREA_BOUNDARY)


settings = Settings()
