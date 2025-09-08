"""
dYdX Trading Bot - Main Application Entry Point
Enterprise-grade automated trading system with real-time monitoring and risk management.
"""

import asyncio
import logging
import sys
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import structlog

from src.config.settings import get_settings
from src.database.base import init_db, check_db_health
from src.monitoring.health_monitor import get_health_monitor
from src.monitoring.metrics import get_metrics_collector
from src.api.trading_routes import router as trading_router
from src.api.auth_routes import router as auth_router
from src.api.websocket_routes import router as websocket_router, periodic_updates_task
from src.api.health_routes import router as health_router


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class TradingBotApplication:
    """Main trading bot application class with lifecycle management"""
    
    def __init__(self):
        self.config = get_settings()
        self.health_monitor = get_health_monitor()
        self.metrics = get_metrics_collector()
        self.trading_engine = None
        self.websocket_task = None
        self.is_shutting_down = False
        
    async def startup(self) -> None:
        """Initialize all application components"""
        logger.info("Starting dYdX Trading Bot application", 
                   testnet=self.config.testnet,
                   debug=self.config.debug)
        
        try:
            # Initialize database
            await self._initialize_database()
            
            # Start health monitoring
            await self.health_monitor.start_monitoring()
            
            # Start WebSocket periodic updates
            self.websocket_task = asyncio.create_task(periodic_updates_task())
            
            # Initialize trading engine (placeholder)
            await self._initialize_trading_engine()
            
            logger.info("Trading bot application started successfully")
            
        except Exception as e:
            logger.error("Failed to start trading bot application", error=str(e))
            raise
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all components"""
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        logger.info("Shutting down trading bot application")
        
        try:
            # Stop WebSocket periodic updates
            if self.websocket_task:
                self.websocket_task.cancel()
                try:
                    await self.websocket_task
                except asyncio.CancelledError:
                    pass
            
            # Stop trading engine first
            if self.trading_engine:
                await self.trading_engine.stop()
            
            # Stop health monitoring
            await self.health_monitor.stop_monitoring()
            
            logger.info("Trading bot application shutdown complete")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
    
    async def _initialize_database(self) -> None:
        """Initialize database connections and run migrations"""
        logger.info("Initializing database...")
        try:
            await init_db()
            
            # Check database health
            if await check_db_health():
                logger.info("Database connection established successfully")
            else:
                logger.error("Database health check failed")
                raise RuntimeError("Database initialization failed")
                
        except Exception as e:
            logger.error("Database initialization error", error=str(e))
            raise
    
    async def _initialize_trading_engine(self) -> None:
        """Initialize and start the trading engine"""
        logger.info("Trading engine initialization - placeholder")
        # TODO: Implement actual trading engine initialization
        # This would start the strategy execution, market data processing, etc.
        pass


# Global application instance
app_instance = TradingBotApplication()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for startup/shutdown"""
    await app_instance.startup()
    try:
        yield
    finally:
        await app_instance.shutdown()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    config = get_settings()
    
    app = FastAPI(
        title="WolfHunt - dYdX Trading Bot API",
        description="Enterprise-grade automated trading system for dYdX v4",
        version="1.0.0",
        docs_url="/docs" if config.debug else None,  # Disable docs in production
        redoc_url="/redoc" if config.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if config.debug else ["https://your-domain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:
        start_time = asyncio.get_event_loop().time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=f"{process_time:.4f}s"
        )
        
        return response
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancers and monitoring"""
        if app_instance.is_shutting_down:
            return Response(status_code=503, content="Shutting down")
        
        try:
            health_status = app_instance.health_monitor.get_current_health()
            if health_status is None:
                health_status = await app_instance.health_monitor.perform_health_checks()
            
            status_code = 200 if health_status.status == "healthy" else 503
            
            return {
                "status": health_status.status,
                "timestamp": health_status.timestamp.isoformat(),
                "uptime_seconds": health_status.uptime_seconds
            }
        except Exception as e:
            logger.error("Health check error", error=str(e))
            return Response(status_code=503, content="Health check failed")
    
    # Metrics endpoint for Prometheus
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Include API routers
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(trading_router, tags=["Trading"])
    app.include_router(health_router, tags=["Health"])
    app.include_router(websocket_router, tags=["WebSocket"])
    
    # Serve frontend static files
    try:
        app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
    except RuntimeError:
        logger.warning("Frontend static files not found, serving API only")
    
    return app


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown"""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(app_instance.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Main entry point"""
    config = get_settings()
    
    # Setup logging
    log_level = "DEBUG" if config.debug else "INFO"
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Create FastAPI app
    app = create_application()
    
    # Run the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=log_level.lower(),
        access_log=True,
        loop="asyncio"
    )


if __name__ == "__main__":
    main()