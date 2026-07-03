# 🧠 MCP Collaborative System: Brain + Graph + Hands

An ultra-efficient, highly collaborative agentic coding framework built using the **Model Context Protocol (MCP)**. This system establishes a division of labor between planning, structural code understanding, and execution, optimizing performance and reducing cost.

---

## ⚡ Core Advantages

*   **📉 90% Token Cost Reduction:** The **Code-Review-Graph** indexes your repository and allows the agent to request only the exact, minimal line ranges required. No more dumping whole files or recursive directories into the context window.
*   **🛡️ Regressions & Bug Prevention:** By delegating coding tasks to a sandboxed instance of **OpenHands**, code runs and validates tests *before* writing changes back. This isolates syntax and logical bugs.
*   **🧩 True Separation of Concerns:**
    *   **The Brain (Orchestrator):** Manages planning, specifications, and architecture.
    *   **The Graph (code-review-graph):** Provides deep code analysis, comunidade identification, and impact radiuses.
    *   **The Hands (OpenHands):** Executes code editing, building, and validation in a clean environment.

---

## 🔄 Independent Core Updates

To ensure your environment remains up-to-date with the latest features, the core tools are **not** frozen in this repository. You download and update them directly from their official sources:

1.  **OpenHands:** You clone and update it directly from the [official OpenHands GitHub repository](https://github.com/All-Hands-AI/OpenHands).
2.  **Code-Review-Graph:** You install and upgrade it globally using its official package manager.

This repository serves strictly as your custom integration, routing rules (`AGENTS.md`), and FastMCP connection layer.

---

## ⚙️ Setup Guide

### 1. Prerequisites
Ensure you have the following installed on your machine:
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Required to run OpenHands and GitHub MCP Server)
*   [Python 3.10+](https://www.python.org/) and [uv](https://github.com/astral-sh/uv) (for running python MCP services)
*   [Node.js](https://nodejs.org/) (for running Stitch / NPX commands)

### 2. Core Setup

#### Step A: Setup Code-Review-Graph
Install `code-review-graph` globally on your system. Follow the official installation instructions for your OS to make sure the `code-review-graph` CLI is accessible on your system Path.

#### Step B: Setup OpenHands
1.  Clone the official OpenHands repository:
    ```bash
    git clone https://github.com/All-Hands-AI/OpenHands.git
    ```
2.  Build and run the OpenHands local container/instance according to their [Development Guide](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
3.  Note down the local URL (usually `http://localhost:8000`) and API token.

---

## 🚀 Easy Onboarding (LLM Bootstrap)

This workspace contains the configuration files and custom rules needed to run the system. When you open this workspace in your agentic IDE (like Antigravity, Cursor, or VS Code with Cline), copy and paste the prompt below into the agent's chat window. 

The agent will automatically locate your paths and set up your local `mcp_config.json` file.

### 📋 Copy-Paste Onboarding Prompt:
```markdown
Please help me bootstrap my local Antigravity environment. 

You need to create my user-specific `mcp_config.json` file. Please guide me through this by performing the following steps:

1. Detect the absolute path of this workspace on my computer.
2. Ask me to paste my GitHub Personal Access Token (PAT).
3. Create (or overwrite) the `mcp_config.json` file in my local directory at:
   `C:\Users\<my_username>\.gemini\antigravity-ide\mcp_config.json`
4. Use the following JSON template, substituting the detected workspace paths and the GitHub PAT I provide:

{
  "mcpServers": {
    "github-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<INSERT_USER_GITHUB_TOKEN>"
      }
    },
    "code-review-graph": {
      "command": "code-review-graph",
      "args": [
        "serve",
        "--auto-watch"
      ]
    },
    "openhands": {
      "command": "uv",
      "args": [
        "run",
        "<DETECTED_WORKSPACE_PATH>/infrastructure/openhands_mcp.py"
      ]
    }
  }
}

Once you have written the file, verify the configuration and confirm when we are ready to build!
```
*(Note: If you are using VS Code with the Cline extension, instruct the agent to write the configuration to `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` instead).*
