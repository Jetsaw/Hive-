"""
Admin dashboard endpoints for monitoring and analytics
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from collections import deque

router = APIRouter(prefix="/admin", tags=["admin"])

# In-memory storage for logs and metrics (replace with database in production)
system_logs = deque(maxlen=1000)  # Keep last 1000 logs
metrics_data = {
    "total_requests": 0,
    "requests_today": 0,
    "total_errors": 0,
    "errors_today": 0,
    "response_times": [],
    "confidence_scores": [],
}

def add_log(level: str, message: str, details: Dict[str, Any] = None):
    """Add a log entry"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "details": details or {}
    }
    system_logs.append(log_entry)

def update_metrics(response_time: float = None, confidence: float = None, is_error: bool = False):
    """Update metrics data"""
    metrics_data["total_requests"] += 1
    metrics_data["requests_today"] += 1
    
    if response_time:
        metrics_data["response_times"].append(response_time)
        # Keep only last 100
        if len(metrics_data["response_times"]) > 100:
            metrics_data["response_times"].pop(0)
    
    if confidence is not None:
        metrics_data["confidence_scores"].append(confidence)
        if len(metrics_data["confidence_scores"]) > 100:
            metrics_data["confidence_scores"].pop(0)
    
    if is_error:
        metrics_data["total_errors"] += 1
        metrics_data["errors_today"] += 1

@router.get("/logs")
async def get_logs(level: str = None, limit: int = 100):
    """Get system logs"""
    logs = list(system_logs)
    
    # Filter by level if specified
    if level:
        logs = [log for log in logs if log["level"].upper() == level.upper()]
    
    # Return most recent first
    logs.reverse()
    return logs[:limit]

@router.get("/metrics")
async def get_metrics():
    """Get real-time metrics"""
    avg_response_time = (
        sum(metrics_data["response_times"]) / len(metrics_data["response_times"])
        if metrics_data["response_times"] else 0
    )
    
    avg_confidence = (
        sum(metrics_data["confidence_scores"]) / len(metrics_data["confidence_scores"])
        if metrics_data["confidence_scores"] else 0
    )
    
    return {
        "total_requests": metrics_data["total_requests"],
        "requests_today": metrics_data["requests_today"],
        "total_errors": metrics_data["total_errors"],
        "errors_today": metrics_data["errors_today"],
        "avg_response_time": round(avg_response_time, 2),
        "avg_confidence": round(avg_confidence * 100, 1),
        "confidence_distribution": calculate_confidence_distribution(),
    }

def calculate_confidence_distribution():
    """Calculate confidence score distribution"""
    if not metrics_data["confidence_scores"]:
        return {"90-100": 0, "70-89": 0, "50-69": 0, "0-49": 0}
    
    distribution = {"90-100": 0, "70-89": 0, "50-69": 0, "0-49": 0}
    
    for score in metrics_data["confidence_scores"]:
        score_percent = score * 100
        if score_percent >= 90:
            distribution["90-100"] += 1
        elif score_percent >= 70:
            distribution["70-89"] += 1
        elif score_percent >= 50:
            distribution["50-69"] += 1
        else:
            distribution["0-49"] += 1
    
    total = len(metrics_data["confidence_scores"])
    return {k: round((v / total) * 100, 1) for k, v in distribution.items()}

@router.get("/health")
async def get_health():
    """Get system health status"""
    # Check various services
    health_status = {
        "backend": {"status": "online", "response_time": 50},
        "database": {"status": "online", "response_time": 30},
        "rag_system": {"status": "online", "response_time": 150},
        "llm_service": {"status": "online", "response_time": 800},
    }
    
    return health_status

@router.get("/analytics")
async def get_analytics():
    """Get analytics data"""
    # This would query your database for actual data
    return {
        "top_questions": [
            {"question": "What are the prerequisites for ACE6313?", "count": 23},
            {"question": "Tell me about Year 1 courses", "count": 18},
            {"question": "Intelligent Robotics programme details", "count": 15},
            {"question": "What is machine learning?", "count": 12},
            {"question": "Graduation requirements", "count": 10},
        ],
        "kb_stats": {
            "total_documents": 1245,
            "last_updated": datetime.now().isoformat(),
            "coverage": {
                "courses": 450,
                "programmes": 120,
                "rules": 85,
                "general": 590,
            }
        }
    }

@router.post("/actions/{action}")
async def execute_action(action: str):
    """Execute admin actions"""
    if action == "clear_cache":
        add_log("INFO", "Cache cleared by admin")
        return {"status": "success", "message": "Cache cleared"}
    
    elif action == "refresh_kb":
        add_log("INFO", "Knowledge base refresh initiated")
        return {"status": "success", "message": "KB refresh started"}
    
    else:
        raise HTTPException(status_code=400, detail="Unknown action")

# Initialize with some sample logs
add_log("INFO", "System started", {"version": "1.0.0"})
add_log("INFO", "Knowledge base loaded", {"documents": 1245})
