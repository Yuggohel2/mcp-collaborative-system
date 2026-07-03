# 🧠 MCP Collaborative System: Brain + Graph + Hands

An ultra-efficient, highly collaborative agentic coding framework built using the **Model Context Protocol (MCP)**. This system establishes a division of labor between planning, structural code understanding, and execution, optimizing performance and reducing cost.

---

## 💻 Supported Clients & IDEs

Since this system is built entirely on the open-standard **Model Context Protocol (MCP)**, it is compatible with any MCP-enabled agentic environment, including:
*   **Antigravity IDE**
*   **Claude Code (CLI)**
*   **Cursor**
*   **VS Code** (using extensions like [Cline](https://github.com/cline/cline) or [Roo Code](https://github.com/RooVetGit/Roo-Code))
*   **Windsurf**
*   Any other MCP-compliant agent.


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

This workspace contains the configuration files and custom rules needed to run the system. When you open this workspace in your agentic environment, copy and paste the prompt below into your agent's chat window. 

The agent will automatically detect your setup and configure the MCP servers for you.

### 📋 Copy-Paste Onboarding Prompt:
```markdown
Please help me bootstrap my local MCP Collaborative System. Follow these steps to configure the environment:

1. Detect the absolute path of this workspace on my computer.
2. Detect which IDE or agent extension we are currently running in (e.g., Antigravity IDE, VS Code with Cline/Roo Code, Claude Desktop, or Cursor).
3. Ask me to paste my GitHub Personal Access Token (PAT).
4. Configure the following MCP settings:

   - **If running in Claude Code CLI:** Write the configuration to `~/.claude.json` (or use `claude mcp add` CLI commands to add each server).
   
   - **If running in Antigravity IDE:** Write the JSON config below to:
     `C:\Users\<username>\.gemini\antigravity-ide\mcp_config.json`
     
   - **If running in VS Code (Cline/Roo Code):** Write the JSON config below to:
     Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
     macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
     
   - **If running in Cursor:** Since Cursor uses a settings GUI, print out the exact values (Name, Type, Command, Args, Env) and give me step-by-step instructions on how to enter them manually in Cursor's settings.


### Configuration Template to Apply/Generate:
(Be sure to replace `<DETECTED_WORKSPACE_PATH>` with the actual absolute path of this workspace, and `<USER_GITHUB_TOKEN>` with the token I provide).

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
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<USER_GITHUB_TOKEN>"
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

Verify the configuration once complete and confirm when we are ready to build!
```


---

## 🧪 Verifying Your Installation

Once you have completed the onboarding setup, you can test that the entire system (Brain + Graph + Hands) is working together correctly by using the following verification challenge.

### The Verification Challenge Prompt:
Copy and paste this prompt into your agentic chat window:

```markdown
Let's run a verification test for our MCP Collaborative System. Please execute the following steps:

1. Create a new directory in our workspace called `verification_test`.
2. Inside it, create a Python script with a deliberate logic bug (e.g., a function that is supposed to calculate fibonacci numbers but has an incorrect recursion base case).
3. Use the `code-review-graph` tools to index the new directory and locate the code.
4. Delegate the task of fixing the bug and running a unit test validation to the `openhands` server.
5. Once fixed and tested, output a summary report showing:
   - The original broken code vs. the fixed code.
   - The verification test status.
   - An estimate of the token context saved by using the graph-targeted lookup rather than passing the whole file/directory into the context window.
```

### Expected Results:
If the setup is fully functional, your agent will:
1. Automatically write the broken script.
2. Query the graph to register/index it.
3. Call `openhands.run_task` to spin up a sandboxed execution, correct the logic, and write a verification test.
4. Output a summary report showing the fix and demonstrating the token efficiency gains of the system (typically saving 80% to 95% of context window tokens compared to standard, full-file reading).
