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

from src.config import get_config
from src.monitoring.health_monitor import SystemHealthMonitor
from src.monitoring.metrics import TradingMetrics
from src.api.trading_routes import router as trading_router
from src.api.auth_routes import router as auth_router
from src.api.websocket_routes import router as websocket_router


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
        self.config = get_config()
        self.health_monitor = SystemHealthMonitor()
        self.metrics = TradingMetrics()
        self.trading_engine = None
        self.websocket_manager = None
        self.is_shutting_down = False
        
    async def startup(self) -> None:
        """Initialize all application components"""
        logger.info("Starting dYdX Trading Bot application", 
                   mode=self.config.trading_mode,
                   environment=self.config.dydx_environment)
        
        try:
            # Initialize database connections
            await self._initialize_database()
            
            # Initialize Redis cache
            await self._initialize_redis()
            
            # Initialize dYdX API clients
            await self._initialize_dydx_clients()
            
            # Start health monitoring
            await self.health_monitor.start()
            
            # Start Prometheus metrics server
            if self.config.enable_monitoring:
                await self._start_metrics_server()
            
            # Initialize trading engine
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
            # Stop trading engine first
            if self.trading_engine:
                await self.trading_engine.stop()
            
            # Close WebSocket connections
            if self.websocket_manager:
                await self.websocket_manager.disconnect()
            
            # Stop health monitoring
            await self.health_monitor.stop()
            
            # Close database connections
            await self._close_database_connections()
            
            # Close Redis connections
            await self._close_redis_connections()
            
            logger.info("Trading bot application shutdown complete")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
    
    async def _initialize_database(self) -> None:
        """Initialize database connections and run migrations"""
        # TODO: Implement database initialization
        logger.info("Database initialization - TODO")
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis cache connections"""
        # TODO: Implement Redis initialization
        logger.info("Redis initialization - TODO")
    
    async def _initialize_dydx_clients(self) -> None:
        """Initialize dYdX API clients"""
        # TODO: Implement dYdX client initialization
        logger.info("dYdX client initialization - TODO")
    
    async def _start_metrics_server(self) -> None:
        """Start Prometheus metrics HTTP server"""
        # TODO: Implement metrics server
        logger.info("Metrics server initialization - TODO")
    
    async def _initialize_trading_engine(self) -> None:
        """Initialize and start the trading engine"""
        # TODO: Implement trading engine initialization
        logger.info("Trading engine initialization - TODO")
    
    async def _close_database_connections(self) -> None:
        """Close all database connections"""
        # TODO: Implement database connection cleanup
        pass
    
    async def _close_redis_connections(self) -> None:
        """Close Redis connections"""
        # TODO: Implement Redis connection cleanup  
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
    
    config = get_config()
    
    app = FastAPI(
        title="dYdX Trading Bot API",
        description="Enterprise-grade automated trading system for dYdX v4",
        version="1.0.0",
        docs_url="/docs" if config.trading_mode == "paper" else None,  # Disable docs in live mode
        redoc_url="/redoc" if config.trading_mode == "paper" else None,
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if config.trading_mode == "paper" else ["https://your-domain.com"],
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
        
        health_status = await app_instance.health_monitor.get_health_status()
        status_code = 200 if health_status["status"] == "healthy" else 503
        
        return Response(
            status_code=status_code,
            content=health_status,
            media_type="application/json"
        )
    
    # Metrics endpoint for Prometheus
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Include API routers
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(trading_router, prefix="/api/trading", tags=["Trading"])
    app.include_router(websocket_router, prefix="/api/ws", tags=["WebSocket"])
    
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
    config = get_config()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
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
        log_level=config.log_level.lower(),
        access_log=True,
        loop="asyncio"
    )


if __name__ == "__main__":
    main()