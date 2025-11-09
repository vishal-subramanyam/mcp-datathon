"""
Main entry point for the Canvas MPC Backend API.
Production-ready FastAPI application with monitoring, health checks, and proper configuration.
"""
import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from backend.api.routes import router as api_router
from backend.utils.config import get_settings
from backend.utils.monitoring import request_metrics, log_system_metrics
from backend.services.mcp_service import health_check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    logger.info(f"Starting Canvas MPC API in {settings.environment} mode")
    logger.info(f"Allowed origins: {settings.allowed_origins}")
    
    # Start background tasks
    metrics_task = asyncio.create_task(log_system_metrics())
    
    yield
    
    # Cleanup
    logger.info("Shutting down Canvas MPC API")
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="Canvas MPC API",
    description="Production-ready backend API for Canvas MPC with integrated MCP servers",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,  # Disable docs in production
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Trusted host middleware (production only)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure based on your needs
    )


# ==========================================
# MIDDLEWARE
# ==========================================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time header and track metrics."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Process-Time"] = str(process_time)
        
        # Track metrics
        request_metrics.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=process_time
        )
        
        return response
    
    except Exception as e:
        process_time = time.time() - start_time
        
        # Track error metrics
        request_metrics.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=500,
            duration=process_time,
            error=str(e)
        )
        
        raise


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to responses."""
    response = await call_next(request)
    
    if settings.is_production:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# ==========================================
# EXCEPTION HANDLERS
# ==========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error on {request.url.path}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.is_development else "An unexpected error occurred",
            "path": request.url.path
        }
    )


# ==========================================
# ROUTES
# ==========================================

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Canvas MPC API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs" if settings.is_development else "Documentation disabled in production",
        "health": "/health",
        "metrics": "/metrics"
    }


@app.get("/health")
async def health():
    """
    Comprehensive health check endpoint.
    Returns health status of the API and all connected services.
    """
    try:
        # Get MCP service health
        mcp_health = await health_check()
        
        # Get metrics-based health
        metrics_health = request_metrics.get_health_status()
        
        # Combine health statuses
        overall_status = "healthy"
        if mcp_health["status"] == "degraded" or metrics_health["status"] == "degraded":
            overall_status = "degraded"
        if mcp_health["status"] == "unhealthy" or metrics_health["status"] == "unhealthy":
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "service": "Canvas MPC API",
            "version": "1.0.0",
            "environment": settings.environment,
            "mcp_services": mcp_health["services"],
            "metrics": metrics_health["metrics"],
            "timestamp": mcp_health["timestamp"]
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "service": "Canvas MPC API"
            }
        )


@app.get("/metrics")
async def metrics():
    """Get application metrics (for monitoring systems)."""
    if settings.is_production:
        # In production, you might want to protect this endpoint
        # or integrate with monitoring services like Prometheus
        pass
    
    return request_metrics.get_metrics()


@app.get("/readiness")
async def readiness():
    """
    Kubernetes readiness probe endpoint.
    Checks if the service is ready to accept traffic.
    """
    try:
        # Quick health check
        mcp_health = await health_check()
        
        if mcp_health["status"] == "unhealthy":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"ready": False, "reason": "MCP services unhealthy"}
            )
        
        return {"ready": True, "status": mcp_health["status"]}
    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "reason": str(e)}
        )


@app.get("/liveness")
async def liveness():
    """
    Kubernetes liveness probe endpoint.
    Simple check that the service is running.
    """
    return {"alive": True}


# ==========================================
# STARTUP
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    # Uvicorn configuration
    uvicorn_config = {
        "app": "backend.main:app",
        "host": settings.host,
        "port": settings.port,
        "reload": settings.is_development,
        "log_level": settings.log_level.lower(),
        "access_log": True,
        "proxy_headers": True,
        "forwarded_allow_ips": "*" if settings.is_production else None,
    }
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    uvicorn.run(**uvicorn_config)

