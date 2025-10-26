from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


# ============= Models =============

class ServiceIntegration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_type: str  # huggingface, github, gmail, google_drive
    name: str
    credentials: Dict[str, Any]  # API keys, tokens, OAuth configs
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceIntegrationCreate(BaseModel):
    service_type: str
    name: str
    credentials: Dict[str, Any]
    enabled: bool = True


class ServiceIntegrationUpdate(BaseModel):
    name: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class MCPServer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    server_type: str  # predefined (e.g., 'browser_automation', 'filesystem') or 'custom'
    endpoint_url: Optional[str] = None  # For custom servers
    authentication: Optional[Dict[str, Any]] = None  # API keys, tokens
    enabled: bool = True
    priority: int = 0  # For load balancing
    fallback_order: Optional[int] = None  # For fallback logic
    health_status: str = "unknown"  # unknown, healthy, unhealthy
    last_health_check: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = None  # Additional config
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MCPServerCreate(BaseModel):
    name: str
    server_type: str
    endpoint_url: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None
    enabled: bool = True
    priority: int = 0
    fallback_order: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    endpoint_url: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    fallback_order: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    health_status: Optional[str] = None


# Helper function to serialize datetime
def serialize_doc(doc):
    if 'created_at' in doc and isinstance(doc['created_at'], datetime):
        doc['created_at'] = doc['created_at'].isoformat()
    if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
        doc['updated_at'] = doc['updated_at'].isoformat()
    if 'last_health_check' in doc and isinstance(doc['last_health_check'], datetime):
        doc['last_health_check'] = doc['last_health_check'].isoformat()
    return doc


def deserialize_doc(doc):
    if 'created_at' in doc and isinstance(doc['created_at'], str):
        doc['created_at'] = datetime.fromisoformat(doc['created_at'])
    if 'updated_at' in doc and isinstance(doc['updated_at'], str):
        doc['updated_at'] = datetime.fromisoformat(doc['updated_at'])
    if 'last_health_check' in doc and isinstance(doc['last_health_check'], str):
        doc['last_health_check'] = datetime.fromisoformat(doc['last_health_check'])
    return doc


# ============= Service Integrations Endpoints =============

@router.post("/integrations", response_model=ServiceIntegration)
async def create_integration(integration: ServiceIntegrationCreate):
    """Create a new service integration"""
    integration_obj = ServiceIntegration(**integration.model_dump())
    doc = serialize_doc(integration_obj.model_dump())
    
    await db.service_integrations.insert_one(doc)
    return integration_obj


@router.get("/integrations", response_model=List[ServiceIntegration])
async def get_integrations():
    """Get all service integrations"""
    integrations = await db.service_integrations.find({}, {"_id": 0}).to_list(1000)
    return [deserialize_doc(integration) for integration in integrations]


@router.get("/integrations/{integration_id}", response_model=ServiceIntegration)
async def get_integration(integration_id: str):
    """Get a specific integration by ID"""
    integration = await db.service_integrations.find_one({"id": integration_id}, {"_id": 0})
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return deserialize_doc(integration)


@router.put("/integrations/{integration_id}", response_model=ServiceIntegration)
async def update_integration(integration_id: str, update: ServiceIntegrationUpdate):
    """Update an integration"""
    integration = await db.service_integrations.find_one({"id": integration_id}, {"_id": 0})
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    await db.service_integrations.update_one(
        {"id": integration_id},
        {"$set": serialize_doc(update_data)}
    )
    
    updated = await db.service_integrations.find_one({"id": integration_id}, {"_id": 0})
    return deserialize_doc(updated)


@router.delete("/integrations/{integration_id}")
async def delete_integration(integration_id: str):
    """Delete an integration"""
    result = await db.service_integrations.delete_one({"id": integration_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"message": "Integration deleted successfully"}


# ============= MCP Servers Endpoints =============

@router.post("/mcp-servers", response_model=MCPServer)
async def create_mcp_server(server: MCPServerCreate):
    """Create a new MCP server configuration"""
    server_obj = MCPServer(**server.model_dump())
    doc = serialize_doc(server_obj.model_dump())
    
    await db.mcp_servers.insert_one(doc)
    return server_obj


@router.get("/mcp-servers", response_model=List[MCPServer])
async def get_mcp_servers():
    """Get all MCP servers, sorted by priority"""
    servers = await db.mcp_servers.find({}, {"_id": 0}).sort("priority", -1).to_list(1000)
    return [deserialize_doc(server) for server in servers]


@router.get("/mcp-servers/{server_id}", response_model=MCPServer)
async def get_mcp_server(server_id: str):
    """Get a specific MCP server by ID"""
    server = await db.mcp_servers.find_one({"id": server_id}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return deserialize_doc(server)


@router.put("/mcp-servers/{server_id}", response_model=MCPServer)
async def update_mcp_server(server_id: str, update: MCPServerUpdate):
    """Update an MCP server configuration"""
    server = await db.mcp_servers.find_one({"id": server_id}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    await db.mcp_servers.update_one(
        {"id": server_id},
        {"$set": serialize_doc(update_data)}
    )
    
    updated = await db.mcp_servers.find_one({"id": server_id}, {"_id": 0})
    return deserialize_doc(updated)


@router.delete("/mcp-servers/{server_id}")
async def delete_mcp_server(server_id: str):
    """Delete an MCP server"""
    result = await db.mcp_servers.delete_one({"id": server_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"message": "MCP server deleted successfully"}


@router.post("/mcp-servers/{server_id}/health-check")
async def health_check_mcp_server(server_id: str):
    """Perform a health check on an MCP server"""
    server = await db.mcp_servers.find_one({"id": server_id}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    # TODO: Implement actual health check logic
    # For now, just update the timestamp and set to healthy
    health_status = "healthy"
    
    await db.mcp_servers.update_one(
        {"id": server_id},
        {"$set": {
            "health_status": health_status,
            "last_health_check": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"status": health_status, "server_id": server_id}


@router.get("/mcp-servers/active/list")
async def get_active_mcp_servers():
    """Get all enabled MCP servers with fallback order"""
    servers = await db.mcp_servers.find(
        {"enabled": True}, 
        {"_id": 0}
    ).sort([("fallback_order", 1), ("priority", -1)]).to_list(1000)
    
    return [deserialize_doc(server) for server in servers]
