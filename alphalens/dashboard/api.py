"""
FastAPI application for monitoring and control.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from alphalens.agents.config import SystemConfig
from alphalens.orchestrator import TradingOrchestrator
from loguru import logger

# Global orchestrator instance
orchestrator: Optional[TradingOrchestrator] = None


class StartRequest(BaseModel):
    """Request to start orchestrator."""
    market_data: Optional[Dict[str, Any]] = None


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    section: str
    updates: Dict[str, Any]


def create_app(config: Optional[SystemConfig] = None) -> FastAPI:
    """
    Create FastAPI application.

    Args:
        config: System configuration (will load from file if not provided)

    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Alphalens Autonomous Trading System",
        description="Monitoring and control API for AI-powered trading system",
        version="1.0.0"
    )

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize orchestrator
    if config is None:
        try:
            config = SystemConfig.from_yaml("config.yaml")
        except Exception as e:
            logger.warning(f"Could not load config.yaml: {e}")
            config = SystemConfig()

    global orchestrator
    orchestrator = TradingOrchestrator(config)

    # Routes

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Alphalens Autonomous Trading System",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        health = orchestrator.health_check()
        return {
            "status": "healthy" if all(health["memory"].values()) else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "details": health
        }

    @app.get("/status")
    async def get_status():
        """Get current system status."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        state = orchestrator.get_state()
        return {
            "is_running": state["is_running"],
            "is_paused": state["is_paused"],
            "current_stage": state["current_state"].get("stage", "idle"),
            "iteration": state["current_state"].get("iteration", 0),
            "last_update": state["current_state"].get("last_update"),
            "agents": state["agents_status"]
        }

    @app.get("/performance")
    async def get_performance():
        """Get performance metrics."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        performance = orchestrator.get_performance()
        return performance

    @app.post("/start")
    async def start_orchestrator(request: StartRequest, background_tasks: BackgroundTasks):
        """Start the orchestrator."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        if orchestrator.is_running:
            raise HTTPException(status_code=400, detail="Orchestrator already running")

        # Run in background
        def run():
            try:
                orchestrator.start(market_data=request.market_data)
            except Exception as e:
                logger.error(f"Orchestrator failed: {e}")

        background_tasks.add_task(run)

        return {"status": "started", "message": "Orchestrator iteration started"}

    @app.post("/pause")
    async def pause_orchestrator():
        """Pause the orchestrator."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        orchestrator.pause()
        return {"status": "paused"}

    @app.post("/resume")
    async def resume_orchestrator():
        """Resume the orchestrator."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        orchestrator.resume()
        return {"status": "resumed"}

    @app.post("/emergency-stop")
    async def emergency_stop():
        """Emergency stop."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        orchestrator.emergency_stop()
        return {"status": "stopped", "message": "Emergency stop activated"}

    @app.get("/agents")
    async def list_agents():
        """List all agents and their status."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        agents_info = {}
        for name, agent in orchestrator.agents.items():
            agents_info[name] = agent.health_check()

        return {"agents": agents_info}

    @app.get("/agents/{agent_name}/state")
    async def get_agent_state(agent_name: str):
        """Get agent state."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        if agent_name not in orchestrator.agents:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")

        agent = orchestrator.agents[agent_name]
        return {
            "agent": agent_name,
            "state": agent.get_state()
        }

    @app.get("/memory/global")
    async def get_global_state():
        """Get global system state."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        return orchestrator.memory.get_global_state()

    @app.get("/memory/learning-summary")
    async def get_learning_summary():
        """Get learning summary."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        return orchestrator.memory.get_learning_summary()

    @app.get("/factors/successful")
    async def get_successful_factors(limit: int = 10):
        """Get successful factors."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        strategies = orchestrator.memory.get_successful_strategies(
            strategy_type="factor",
            limit=limit
        )
        return {"factors": strategies}

    @app.get("/risk/events")
    async def get_risk_events(limit: int = 50):
        """Get recent risk events."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        events = orchestrator.memory.get_risk_events(limit=limit)
        return {"events": events}

    @app.get("/config")
    async def get_config():
        """Get current configuration."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        return orchestrator.config.to_dict()

    @app.post("/config/update")
    async def update_config(update: ConfigUpdate):
        """Update configuration."""
        # Note: This updates in-memory config only, not persisted
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        try:
            config_dict = orchestrator.config.to_dict()
            if update.section in config_dict:
                config_dict[update.section].update(update.updates)
                orchestrator.config = SystemConfig.from_dict(config_dict)
                return {"status": "updated", "section": update.section}
            else:
                raise HTTPException(status_code=400, detail=f"Invalid section: {update.section}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app


def run_server(host: str = "0.0.0.0", port: int = 8000, config: Optional[SystemConfig] = None):
    """
    Run the API server.

    Args:
        host: Host to bind to
        port: Port to bind to
        config: System configuration
    """
    import uvicorn

    app = create_app(config)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
