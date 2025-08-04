#!/usr/bin/env python3
"""
Production monitoring and health check system for Autopicker Platform
Monitors system resources, API health, and model performance
"""

import asyncio
import json
import logging
import os
import platform
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/autopicker_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Monitoring router for FastAPI
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


class SystemMetrics(BaseModel):
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    load_average: List[float]
    uptime_hours: float
    process_count: int
    network_connections: int


class APIHealthCheck(BaseModel):
    """API endpoint health status"""
    endpoint: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    status_code: Optional[int]
    error_message: Optional[str]
    timestamp: datetime


class ModelMetrics(BaseModel):
    """LLM model performance metrics"""
    model_name: str
    requests_count: int
    avg_response_time_ms: float
    error_rate_percent: float
    tokens_processed: int
    timestamp: datetime


class MonitoringService:
    """Production monitoring service"""
    
    def __init__(self):
        self.metrics_file = Path("/tmp/autopicker_metrics.json")
        self.start_time = time.time()
        self.api_base_url = "http://localhost:8001"
        self.check_interval = 60  # seconds
        
    async def get_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_free_gb = disk.free / (1024**3)
            
            # Load average (Unix systems)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0.0, 0.0, 0.0]
            
            # Uptime
            uptime_hours = (time.time() - self.start_time) / 3600
            
            # Process and network info
            process_count = len(psutil.pids())
            network_connections = len(psutil.net_connections(kind='inet'))
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_gb=memory.available / (1024**3),
                disk_usage_percent=disk.percent,
                disk_free_gb=disk_free_gb,
                load_average=list(load_avg),
                uptime_hours=uptime_hours,
                process_count=process_count,
                network_connections=network_connections
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise
    
    async def check_api_health(self) -> List[APIHealthCheck]:
        """Check health of API endpoints"""
        endpoints = [
            "/health",
            "/api/v1/chat/completions",
            "/api/v1/files",
            "/api/v1/upload"
        ]
        
        health_checks = []
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    
                    if endpoint == "/api/v1/chat/completions":
                        # Test with minimal payload
                        response = await client.post(
                            f"{self.api_base_url}{endpoint}",
                            json={
                                "messages": [{"role": "user", "content": "health check"}],
                                "model": "auto",
                                "max_tokens": 1
                            }
                        )
                    else:
                        response = await client.get(f"{self.api_base_url}{endpoint}")
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status_code < 400 else "unhealthy"
                    if response.status_code >= 400 and response.status_code < 500:
                        status = "degraded"
                    
                    health_checks.append(APIHealthCheck(
                        endpoint=endpoint,
                        status=status,
                        response_time_ms=response_time,
                        status_code=response.status_code,
                        error_message=None,
                        timestamp=datetime.now()
                    ))
                    
                except Exception as e:
                    health_checks.append(APIHealthCheck(
                        endpoint=endpoint,
                        status="unhealthy",
                        response_time_ms=0.0,
                        status_code=None,
                        error_message=str(e),
                        timestamp=datetime.now()
                    ))
        
        return health_checks
    
    async def check_ollama_health(self) -> APIHealthCheck:
        """Check Ollama service health"""
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                response_time = (time.time() - start_time) * 1000
                
                status = "healthy" if response.status_code == 200 else "unhealthy"
                
                return APIHealthCheck(
                    endpoint="ollama:/api/tags",
                    status=status,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    error_message=None,
                    timestamp=datetime.now()
                )
        except Exception as e:
            return APIHealthCheck(
                endpoint="ollama:/api/tags",
                status="unhealthy",
                response_time_ms=0.0,
                status_code=None,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def save_metrics(self, data: Dict):
        """Save metrics to file"""
        try:
            # Keep only last 24 hours of metrics
            if self.metrics_file.exists():
                async with aiofiles.open(self.metrics_file, 'r') as f:
                    existing_data = json.loads(await f.read())
                
                # Filter old entries
                cutoff_time = datetime.now() - timedelta(hours=24)
                existing_data = [
                    entry for entry in existing_data 
                    if datetime.fromisoformat(entry['timestamp']) > cutoff_time
                ]
                data['history'] = existing_data
            
            async with aiofiles.open(self.metrics_file, 'w') as f:
                await f.write(json.dumps(data, default=str, indent=2))
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    async def get_alerts(self) -> List[Dict]:
        """Check for alert conditions"""
        alerts = []
        
        try:
            metrics = await self.get_system_metrics()
            
            # CPU alert
            if metrics.cpu_percent > 80:
                alerts.append({
                    "type": "cpu_high",
                    "severity": "warning" if metrics.cpu_percent < 90 else "critical",
                    "message": f"CPU usage is {metrics.cpu_percent:.1f}%",
                    "timestamp": datetime.now()
                })
            
            # Memory alert
            if metrics.memory_percent > 85:
                alerts.append({
                    "type": "memory_high",
                    "severity": "warning" if metrics.memory_percent < 95 else "critical",
                    "message": f"Memory usage is {metrics.memory_percent:.1f}%",
                    "timestamp": datetime.now()
                })
            
            # Disk space alert
            if metrics.disk_usage_percent > 85:
                alerts.append({
                    "type": "disk_full",
                    "severity": "warning" if metrics.disk_usage_percent < 95 else "critical",
                    "message": f"Disk usage is {metrics.disk_usage_percent:.1f}%",
                    "timestamp": datetime.now()
                })
            
            # Check API health
            health_checks = await self.check_api_health()
            unhealthy_apis = [hc for hc in health_checks if hc.status == "unhealthy"]
            
            if unhealthy_apis:
                alerts.append({
                    "type": "api_unhealthy",
                    "severity": "critical",
                    "message": f"{len(unhealthy_apis)} API endpoints are unhealthy",
                    "endpoints": [api.endpoint for api in unhealthy_apis],
                    "timestamp": datetime.now()
                })
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            alerts.append({
                "type": "monitoring_error",
                "severity": "warning",
                "message": f"Error in monitoring system: {str(e)}",
                "timestamp": datetime.now()
            })
        
        return alerts


# Global monitoring service instance
monitoring_service = MonitoringService()


@router.get("/health")
async def get_monitoring_health():
    """Get overall system health status"""
    try:
        system_metrics = await monitoring_service.get_system_metrics()
        api_health = await monitoring_service.check_api_health()
        ollama_health = await monitoring_service.check_ollama_health()
        alerts = await monitoring_service.get_alerts()
        
        # Determine overall status
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        unhealthy_apis = [h for h in api_health if h.status == "unhealthy"]
        
        if critical_alerts or ollama_health.status == "unhealthy":
            overall_status = "unhealthy"
        elif unhealthy_apis or any(a.get("severity") == "warning" for a in alerts):
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(),
            "system": system_metrics,
            "api_health": api_health,
            "ollama_health": ollama_health,
            "alerts": alerts,
            "summary": {
                "total_alerts": len(alerts),
                "critical_alerts": len(critical_alerts),
                "healthy_apis": len([h for h in api_health if h.status == "healthy"]),
                "total_apis": len(api_health)
            }
        }
    except Exception as e:
        logger.error(f"Error in monitoring health check: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring error: {str(e)}")


@router.get("/metrics")
async def get_system_metrics():
    """Get current system metrics"""
    try:
        return await monitoring_service.get_system_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts():
    """Get current system alerts"""
    try:
        return await monitoring_service.get_alerts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_metrics_history():
    """Get historical metrics data"""
    try:
        if not monitoring_service.metrics_file.exists():
            return {"history": []}
        
        async with aiofiles.open(monitoring_service.metrics_file, 'r') as f:
            data = json.loads(await f.read())
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def monitoring_loop():
    """Background monitoring loop"""
    logger.info("Starting monitoring loop...")
    
    while True:
        try:
            # Collect all metrics
            system_metrics = await monitoring_service.get_system_metrics()
            api_health = await monitoring_service.check_api_health()
            ollama_health = await monitoring_service.check_ollama_health()
            alerts = await monitoring_service.get_alerts()
            
            # Save metrics
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "system": system_metrics.dict(),
                "api_health": [h.dict() for h in api_health],
                "ollama_health": ollama_health.dict(),
                "alerts": alerts
            }
            
            await monitoring_service.save_metrics(metrics_data)
            
            # Log critical alerts
            critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
            if critical_alerts:
                logger.warning(f"CRITICAL ALERTS: {len(critical_alerts)} alerts detected")
                for alert in critical_alerts:
                    logger.warning(f"  - {alert['type']}: {alert['message']}")
            
            # Log system status
            logger.info(f"System Status: CPU={system_metrics.cpu_percent:.1f}% "
                       f"MEM={system_metrics.memory_percent:.1f}% "
                       f"DISK={system_metrics.disk_usage_percent:.1f}% "
                       f"APIs={len([h for h in api_health if h.status == 'healthy'])}/{len(api_health)}")
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        # Wait for next check
        await asyncio.sleep(monitoring_service.check_interval)


if __name__ == "__main__":
    # Run monitoring loop for testing
    import asyncio
    asyncio.run(monitoring_loop())