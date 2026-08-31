from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, rides, drivers, ratings, users, payments, admin
from app.websocket.ride_tracking import get_socket_app

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(rides.router, prefix="/api/v1/rides", tags=["Rides"])
app.include_router(drivers.router, prefix="/api/v1/drivers", tags=["Drivers"])
app.include_router(ratings.router, prefix="/api/v1/ratings", tags=["Ratings"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

socket_app = get_socket_app()
app.mount("/ws", socket_app)


@app.get("/")
async def root():
    return {
        "message": "Kanyakumari RideShare API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
