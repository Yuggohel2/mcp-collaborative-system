# Token-Efficient Collaborative System Rules (Antigravity + Graph + OpenHands)

To optimize native performance and stay strictly within the 8% remaining Gemini model quota, all agents working in this workspace must adhere to the following rules:

## 1. Onboarding and Workspace Configuration Discovery
- **Rule**: If this is a new workspace session or if the project folder, workspace root, or IDE client details are not yet identified, the agent must ask the user to verify/input:
  1. The **workspace root path** (e.g., `D:/AI workspace`).
  2. The **designated project folder name** (e.g., `Projects/` or any custom folder where their software application files live).
  3. The **IDE / Agent client** in use (Antigravity IDE, Cursor, Claude Code, or VS Code with Cline/Roo Code).
- **Rule**: If either folder does not exist, the agent must ask the user what to name them and create them. If they already exist, the agent must dynamically detect and connect them.
- **Rule**: The agent must automatically write the detected/configured paths (`WORKSPACE_ROOT` and `PROJECTS_DIR`) into the `env` section of the `openhands` server configuration in `mcp_config.json` (or the equivalent client settings file) to ensure the collaborative tools are correctly scoped.

## 2. Graph-First Codebase Analysis (Only inside the Designated Project Folder)
- **Rule**: First, identify the user's active/designated project folder containing their application/software code. If it is not clear or if multiple exist, ask the user to specify or confirm.
- **Rule**: When analyzing codebases or projects inside this designated project folder, always query the `code-review-graph` server first (using `query_graph_tool`, `get_impact_radius_tool`, etc.). Never run recursive directory listings (`list_dir`) or generic searches (`grep_search`) to understand codebase architecture or dependencies.
- **Rule**: Only load specific files identified by the graph analysis. Never load files larger than 150 lines in their entirety; request specific line ranges using `view_file` to conserve context.
- **Rule**: When working outside the designated project folder (e.g., workspace-level config files, infrastructure script updates, or agent rulebooks), you can list directories and view files directly without using the graph.

## 3. Strict OpenHands Sandbox Delegation (Only inside the Designated Project Folder)
- **Rule**: Antigravity must act strictly as **The Brain** (Architect/Planner) when making changes to code files inside the designated project folder. It must **not** directly write code changes to that folder on the host file system.
- **Rule**: All file updates, terminal command executions, build/test cycles, and debugging actions for code under the designated project folder must be executed inside the sandboxed OpenHands container via the `openhands.execute_bash` tool.
- **Rule**: When making changes *outside* the designated project folder (such as configuring MCP servers, updating `openhands_mcp.py`, or modifying `AGENTS.md`/`mcp_config.json`), Antigravity must edit files directly on the host using its native file-writing tools (e.g., `replace_file_content`, `write_to_file`) and run local commands directly if needed.
- **Rule**: **Path Translation:** When analyzing build/test outputs or errors produced inside the Docker container, the agent MUST automatically translate container-space absolute paths (e.g., `/projects/<project-name>/...`) back to host-space paths (e.g., `<PROJECTS_DIR>/<project-name>/...`) before using native file-viewing or editing tools (such as `view_file` or `replace_file_content`).

## 4. Synchronous Sandbox Execution (No Polling)
- **Rule**: Commands run inside the sandbox via `openhands.execute_bash` are executed synchronously. Specify an appropriate timeout (default 300s) and handle the result (exit code, stdout, stderr) immediately in your next step.
- **Rule**: Do **not** run background `sleep` loops or poll task status.
- **Rule**: **Execution Safety & Hang Prevention:** The agent MUST run background processes, listening ports, or long-running development servers inside the sandbox with non-blocking execution commands (e.g., using `nohup` or `&` in the background). For standard commands, always enforce a strict, short timeout to prevent the connection socket from hanging.


## 5. Summarization and Verification (Only inside the Designated Project Folder)
- **Rule**: When OpenHands finishes, only request the final diff and a brief test pass summary. Do not output raw build logs or stack traces to the main chat.
- **Rule**: Use the `code-review-graph` to review changes post-implementation to ensure architectural integrity.
- **Rule**: The verification test/challenge (specified in `README.md`) must only be run once to verify the initial system installation. If the user prompts to run the verification test, the agent must check if the `verification_test` directory already exists and has been successfully resolved. If it has, the agent must inform the user that the system is already verified and skip running it again.



## 6. Automatic Session State Persistence
- **Rule**: The agent MUST automatically maintain and update the `task.md` state at the end of every execution phase, or whenever pausing/ending a task.
- **Rule**: **Inside Project Folder:** If the work is occurring inside a specific project folder (under `PROJECTS_DIR`), the agent MUST create/update the `task.md` directly in that active project's root folder so that each project retains its own persistent memory. The global conversation-level `task.md` should not be used or updated in this case.
- **Rule**: **Outside Project Folder:** If the work is occurring outside or above the projects folder (such as configuring workspace-level MCP servers, editing rulebooks, or updating global configuration files), the agent MUST create/update a global `task.md` in the conversation artifacts directory (e.g., `<appDataDir>\brain\<conversation-id>\task.md`).
- **Rule**: **Inside the PROJECTS_DIR Root:** If the work is occurring directly in the parent container/projects directory itself (and not inside a specific project subfolder), neither the global nor the project-specific `task.md` should be updated.
- **Rule**: The update must detail completed tasks `[x]`, in-progress tasks `[/]`, and clearly state where the work was stopped so that a fresh conversation session can resume immediately without manual user explanation.




## 7. Docker Cleanup Shortcut
- **Rule**: If the user instructs to "run docker cleanup command", the agent must run the following PowerShell command in the workspace:
  `docker system prune --volumes -f`
- **Rule**: Print the execution stdout/stderr to show the user how much disk space was reclaimed.

## 8. GitHub Push Constraint
- **Rule**: Do NOT push code changes to the GitHub repository automatically.
- **Rule**: Only push changes to the remote GitHub repository when the user explicitly instructs you to do so.



