# /// script
# dependencies = [
#   "fastmcp",
#   "httpx"
# ]
# ///

import os
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastmcp import FastMCP
import httpx
import subprocess
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openhands_mcp")

# Initialize FastMCP server
mcp = FastMCP("openhands")

OPENHANDS_URL = os.getenv("OPENHANDS_URL", "http://localhost:8000")

_LAST_API_KEY = None

def get_api_key() -> str:
    """Dynamically retrieve the OpenHands session API key."""
    global _LAST_API_KEY
    key = None
    
    # 1. Try environment variables
    key_env = os.getenv("OPENHANDS_API_KEY") or os.getenv("SESSION_API_KEY")
    if key_env:
        key = key_env.strip()

    # 2. Resolve default path: ~/.openhands/agent-canvas/api-key.txt
    if not key:
        try:
            home = Path.home()
            key_file = home / ".openhands" / "agent-canvas" / "api-key.txt"
            if key_file.exists():
                key = key_file.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error(f"Failed to read api-key.txt: {e}")

    # Fallback/Error
    if not key:
        raise ValueError("OpenHands API Key could not be resolved from environment or ~/.openhands/agent-canvas/api-key.txt")

    # Logging on rotation
    if key != _LAST_API_KEY:
        if _LAST_API_KEY is not None:
            logger.info(f"OpenHands API key rotated dynamically. New key prefix: {key[:8]}...")
        else:
            logger.info(f"Dynamically loaded OpenHands API key. Key prefix: {key[:8]}...")
        _LAST_API_KEY = key

    return key

def get_headers() -> dict:
    """Construct headers for API requests."""
    return {
        "X-Session-API-Key": get_api_key(),
        "Content-Type": "application/json"
    }

def map_workspace_path(host_path: str) -> str:
    """
    Map host workspace path under PROJECTS_DIR to container path.
    Example: D:/AI workspace/Projects/ML PROJECT-1 -> /projects/ML PROJECT-1
    """
    # Standardize path separators
    normalized = host_path.replace("\\", "/").rstrip("/")
    
    # Resolve host project directory dynamically (supports other machines)
    workspace_root = os.getenv("WORKSPACE_ROOT", str(Path(__file__).parent.parent.resolve()))
    projects_dir = os.getenv("PROJECTS_DIR", str(Path(workspace_root) / "Projects"))
    prefix_host = projects_dir.replace("\\", "/").lower().rstrip("/")
    
    if normalized.lower().startswith(prefix_host):
        # Extract the relative path after Projects root directory
        relative = normalized[len(prefix_host):].lstrip("/")
        return f"/projects/{relative}"
        
    return normalized

def extract_text_content(content) -> str:
    """Helper to extract and join text content from lists or strings."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts).strip()
    return ""

@mcp.tool()
async def list_conversations(limit: int = 10) -> Dict[str, Any]:
    """List existing conversations/sessions in the OpenHands instance."""
    url = f"{OPENHANDS_URL}/api/conversations/search"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=get_headers(), params={"limit": limit})
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def create_conversation(workspace_path: str, initial_message: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new conversation session configured for a specific workspace.
    workspace_path: Host path (e.g. D:/AI workspace/Projects/my-project)
    initial_message: Optional task instruction to kick off the conversation
    """
    # 1. Fetch active agent profile ID dynamically
    profile_url = f"{OPENHANDS_URL}/api/agent-profiles"
    headers = get_headers()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        profile_res = await client.get(profile_url, headers=headers)
        profile_res.raise_for_status()
        profile_data = profile_res.json()
        active_profile_id = profile_data.get("active_agent_profile_id")
        if not active_profile_id:
            raise ValueError("No active agent profile found on OpenHands server.")
        
        # 2. Map host workspace path to container path
        mapped_path = map_workspace_path(workspace_path)
        
        # 3. Build StartConversationRequest payload
        payload = {
            "workspace": {
                "working_dir": mapped_path,
                "kind": "LocalWorkspace"
            },
            "agent_profile_id": active_profile_id
        }
        
        if initial_message:
            payload["initial_message"] = {
                "content": [
                    {
                        "type": "text",
                        "text": initial_message
                    }
                ]
            }
            
        # 4. Post conversation creation
        conv_url = f"{OPENHANDS_URL}/api/conversations"
        conv_res = await client.post(conv_url, json=payload, headers=headers)
        conv_res.raise_for_status()
        return conv_res.json()

@mcp.tool()
async def run_task(conversation_id: str) -> Dict[str, Any]:
    """Run/Resume a conversation session in the background."""
    url = f"{OPENHANDS_URL}/api/conversations/{conversation_id}/run"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(url, headers=get_headers())
        res.raise_for_status()
        return res.json()

@mcp.tool()
async def execute_bash(command: str, cwd: Optional[str] = None, timeout: int = 300) -> Dict[str, Any]:
    """Execute a bash command inside the sandboxed OpenHands container."""
    url = f"{OPENHANDS_URL}/api/bash/execute_bash_command"
    payload = {
        "command": command,
        "cwd": cwd,
        "timeout": timeout
    }
    async with httpx.AsyncClient(timeout=float(timeout + 10)) as client:
        res = await client.post(url, json=payload, headers=get_headers())
        res.raise_for_status()
        return res.json()


@mcp.tool()
async def get_task_status(conversation_id: str) -> Dict[str, Any]:
    """Retrieve the current execution status and last response of an OpenHands conversation."""
    headers = get_headers()
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Get status/details
        info_url = f"{OPENHANDS_URL}/api/conversations/{conversation_id}"
        info_res = await client.get(info_url, headers=headers)
        info_res.raise_for_status()
        info_data = info_res.json()
        
        # Get final/last agent response
        resp_url = f"{OPENHANDS_URL}/api/conversations/{conversation_id}/agent_final_response"
        resp_res = await client.get(resp_url, headers=headers)
        resp_res.raise_for_status()
        resp_data = resp_res.json()
        
        return {
            "conversation_id": conversation_id,
            "execution_status": info_data.get("execution_status"),
            "agent_final_response": resp_data.get("response", ""),
            "updated_at": info_data.get("updated_at")
        }

@mcp.tool()
async def interrupt_task(conversation_id: str) -> Dict[str, Any]:
    """Immediately interrupt/pause the execution of a running conversation task."""
    url = f"{OPENHANDS_URL}/api/conversations/{conversation_id}/interrupt"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(url, headers=get_headers())
        res.raise_for_status()
        return res.json()

@mcp.tool()
async def delete_conversation(conversation_id: str) -> Dict[str, Any]:
    """Permanently delete a conversation session and clean up its resources."""
    url = f"{OPENHANDS_URL}/api/conversations/{conversation_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.delete(url, headers=get_headers())
        res.raise_for_status()
        return res.json()

@mcp.tool()
async def retrieve_logs(conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve sequential event logs (messages, actions, observations) for a conversation."""
    url = f"{OPENHANDS_URL}/api/conversations/{conversation_id}/events/search"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(url, headers=get_headers(), params={"limit": limit, "sort_order": "TIMESTAMP"})
        res.raise_for_status()
        events_data = res.json()
        
        parsed_events = []
        for event in events_data.get("items", []):
            kind = event.get("kind")
            source = event.get("source", "unknown")
            timestamp = event.get("timestamp")
            
            parsed_event = {
                "timestamp": timestamp,
                "source": source,
                "kind": kind
            }
            
            if kind == "MessageEvent":
                content_list = event.get("llm_message", {}).get("content", [])
                parsed_event["message"] = extract_text_content(content_list)
                
            elif kind == "ActionEvent":
                parsed_event["tool_called"] = event.get("tool_name")
                parsed_event["summary"] = event.get("summary")
                action_data = event.get("action")
                if action_data:
                    parsed_event["action_details"] = action_data
                    
            elif kind == "ObservationEvent":
                parsed_event["tool_called"] = event.get("tool_name")
                obs_data = event.get("observation", {})
                parsed_event["observation"] = extract_text_content(obs_data.get("content")) or extract_text_content(obs_data.get("message"))
                
            else:
                parsed_event["details"] = event
                
            parsed_events.append(parsed_event)
            
        return parsed_events

def auto_register_project(project_path: Path):
    """
    Ensure the folder has a code-review-graph repository marker, register it, 
    and add it to the code-review-graph watch daemon.
    """
    project_path = project_path.resolve()
    git_dir = project_path / ".git"
    crg_dir = project_path / ".code-review-graph"
    
    # Initialize an empty CRG marker if not in git to allow non-git projects to build graphs
    if not git_dir.exists() and not crg_dir.exists():
        try:
            crg_dir.mkdir(exist_ok=True)
            logger.info(f"Created .code-review-graph directory in {project_path}")
        except Exception as e:
            logger.error(f"Failed to create .code-review-graph in {project_path}: {e}")
            return

    try:
        # Standardize path string with forward slashes to prevent Windows TOML escaping bugs
        path_str = str(project_path).replace("\\", "/")
        
        # 1. Register repository
        logger.info(f"Registering project with code-review-graph register: {path_str}")
        subprocess.run(["code-review-graph", "register", path_str], check=True, capture_output=True, text=True)
        
        # 2. Add to daemon watcher config
        logger.info(f"Adding project to code-review-graph daemon: {path_str}")
        subprocess.run(["code-review-graph", "daemon", "add", path_str], check=True, capture_output=True, text=True)
        
        # 3. Restart daemon to load the new config
        logger.info(f"Restarting code-review-graph watch daemon")
        subprocess.run(["code-review-graph", "daemon", "restart"], check=True, capture_output=True, text=True)
        
    except Exception as e:
        logger.error(f"Error registering project {project_path} with code-review-graph: {e}")

def watch_projects_folder():
    """
    Background worker that polls the Projects directory for new folders
    and automatically registers them.
    """
    # Use standard host path location matching map_workspace_path
    workspace_root = os.getenv("WORKSPACE_ROOT", str(Path(__file__).parent.parent.resolve()))
    projects_dir = Path(os.getenv("PROJECTS_DIR", str(Path(workspace_root) / "Projects"))).resolve()
    if not projects_dir.exists():
        logger.warning(f"Projects directory {projects_dir} does not exist. Auto-registration watcher stopped.")
        return

    # Track already scanned project names
    known_dirs = set()
    try:
        for entry in projects_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                known_dirs.add(entry.name)
                # Register existing folders on startup to verify state
                auto_register_project(entry)
    except Exception as e:
        logger.error(f"Error during initial Projects directory scan: {e}")

    logger.info(f"Projects folder watcher active, scanning {projects_dir} every 5s...")
    while True:
        try:
            time.sleep(5)
            current_dirs = set()
            for entry in projects_dir.iterdir():
                if entry.is_dir() and not entry.name.startswith("."):
                    current_dirs.add(entry.name)
                    if entry.name not in known_dirs:
                        logger.info(f"New project folder detected: {entry.name}")
                        auto_register_project(entry)
            known_dirs = current_dirs
        except Exception as e:
            logger.error(f"Error in projects watcher loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Start the Projects directory auto-registration watcher in a daemon thread
    watcher_thread = threading.Thread(target=watch_projects_folder, daemon=True)
    watcher_thread.start()
    logger.info("Started background Projects directory watcher thread.")
    
    mcp.run()
