# Token-Efficient Collaborative System Rules (Antigravity + Graph + OpenHands)

To optimize native performance and stay strictly within the 8% remaining Gemini model quota, all agents working in this workspace must adhere to the following rules:

## 1. Onboarding and Workspace Configuration Discovery
- **Rule**: Onboarding and path discovery are only performed for new workspaces or when configuration values cannot be automatically resolved. If the workspace root, designated project folder, and client settings have already been identified or verified in a prior session, the agent MUST NOT ask the user to re-verify or re-input these details. Instead, the agent should dynamically detect the configuration and connect silently.
- **Rule**: The agent must automatically write the detected/configured paths (`WORKSPACE_ROOT` and `PROJECTS_DIR`) into the `env` section of the `openhands` server configuration in `mcp_config.json` (or the equivalent client settings file) to ensure the collaborative tools are correctly scoped.
- **Rule**: **Path Formatting in Configs:** When writing paths to `mcp_config.json` or client settings, the agent MUST always standardize paths to use forward slashes `/` (e.g., `C:/Users/John/Workspace`) instead of backslashes. This prevents JSON escape corruption bugs on Windows.

## 2. Graph-First Codebase Analysis (Only inside the Designated Project Folder)
- **Rule**: First, identify the user's active/designated project folder containing their application/software code. If it is not clear or if multiple exist, ask the user to specify or confirm.
- **Rule**: When analyzing codebases or projects inside this designated project folder, always query the `code-review-graph` server first (using `query_graph_tool`, `get_impact_radius_tool`, etc.). Never run recursive directory listings (`list_dir`) or generic searches (`grep_search`) to understand codebase architecture or dependencies.
- **Rule**: Only load specific files identified by the graph analysis. Never load files larger than 150 lines in their entirety; request specific line ranges using `view_file` to conserve context.
- **Rule**: When working outside the designated project folder (e.g., workspace-level config files, infrastructure script updates, or agent rulebooks), you can list directories and view files directly without using the graph.

## 3. Complexity-Based OpenHands Delegation (Inside the Designated Project Folder)
- **Rule**: When working on **complex architectural changes** to code files inside the designated project folder (e.g., multi-file refactors, new module integrations, build pipeline changes, or changes spanning multiple components), Antigravity MUST delegate the execution to the OpenHands sandbox via the `openhands.execute_bash` tool. Antigravity acts as **The Brain** (Architect/Planner) — designing the solution, then instructing OpenHands to implement it.
- **Rule**: For **simple or straightforward work** (e.g., creating a new file from scratch, small single-file edits, config changes, adding comments, fixing typos, or writing tests), Antigravity MAY write code directly to the project folder on the host file system using its native tools (e.g., `write_to_file`, `replace_file_content`). This avoids unnecessary overhead for trivial changes.
- **Rule**: All terminal command executions for build/test cycles and debugging actions inside the designated project folder SHOULD use the OpenHands sandbox when the sandbox is available and the task involves complex multi-step operations. Simple one-off commands (e.g., running a test file, checking a Python import) may be run directly on the host.
- **Rule**: When making changes *outside* the designated project folder (such as configuring MCP servers, updating `openhands_mcp.py`, or modifying `AGENTS.md`/`mcp_config.json`), Antigravity must edit files directly on the host using its native file-writing tools and run local commands directly if needed.
- **Rule**: **Path Translation:** When analyzing build/test outputs or errors produced inside the Docker container, the agent MUST automatically translate container-space absolute paths (e.g., `/projects/<project-name>/...`) back to host-space paths (e.g., `<PROJECTS_DIR>/<project-name>/...`) before using native file-viewing or editing tools (such as `view_file` or `replace_file_content`).
- **Rule**: **Sandbox Path Quoting:** When generating bash commands to execute inside the sandbox (especially directory operations like `cd`, `ls`, or path targets in compilation/tests), the agent MUST always wrap path arguments in double quotes (e.g., `cd "/projects/my-app"`) to ensure compatibility with folder names containing spaces.

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
- **Rule**: **Inside Project Folder:** If the work is occurring inside a specific project folder (under `PROJECTS_DIR`), the agent MUST create/update the `task.md` directly in that active project's root folder so that each project retains its own persistent memory.
- **Rule**: **Outside Project Folder:** If the work is occurring outside or above the projects folder (such as configuring workspace-level MCP servers, editing rulebooks, or updating global configuration files), the agent MUST create/update the global `task.md` directly at the workspace root (`WORKSPACE_ROOT/task.md`). This global file acts as a persistent log of system-level work across all conversation sessions and must never be deleted or cleared unless the user explicitly instructs it.
- **Rule**: **Inside the PROJECTS_DIR Root:** If the work is occurring directly in the parent container/projects directory itself (and not inside a specific project subfolder), neither the global nor the project-specific `task.md` should be updated.
- **Rule**: The update must detail completed tasks `[x]`, in-progress tasks `[/]`, and clearly state where the work was stopped so that a fresh conversation session can resume immediately without manual user explanation.
- **Rule**: **Task List Size Limit & Archiving:** To prevent context window bloat, the active `task.md` (both global and project-specific) must be kept compact (typically under 2,000 lines or 30,000 words). If it exceeds this size, the agent MUST automatically archive older completed tasks/phases into a single sibling archive file named `task_archive.md` (e.g., `WORKSPACE_ROOT/task_archive.md` or `PROJECT_DIR/task_archive.md`) in the same folder.
    *   **Retention**: The active `task.md` MUST always retain all pending/in-progress tasks and the most recently completed tasks (e.g., the last 24-48 hours of work), only archiving older completed phases/tasks to ensure recent context remains immediately accessible.
    *   **Archive Structure**: The agent MUST write archived entries in `task_archive.md` using clear, chronological, and searchable date/phase headers (e.g., `### 2026-07-04 - Phase 1`).
    *   **Targeted Retrieval**: When the user queries history, the agent MUST NOT load `task_archive.md` in its entirety. Instead, it must locate the target date/phase header and use the `view_file` tool with specific `StartLine` and `EndLine` ranges to retrieve only the relevant portion, keeping the context window clean. The active `task.md` should retain a brief, high-level summary list of archived phases for navigation.




## 7. Docker Cleanup Shortcut
- **Rule**: If the user instructs to "run docker cleanup command", the agent must run the following PowerShell command in the workspace:
  `docker system prune -f`
- **Rule**: Print the execution stdout/stderr to show the user how much disk space was reclaimed.


## 8. GitHub Push Constraint
- **Rule**: Do NOT push code changes to the GitHub repository automatically.
- **Rule**: Only push changes to the remote GitHub repository when the user explicitly instructs you to do so.


## 9. Dynamic LLM Proxy Handling
- **Rule**: When executing task canvas processes or intercepting OpenHands requests, the agent must check the user's home `.openhands/` directory (e.g., `~/.openhands/` or resolved dynamically via `Path.home() / ".openhands"`) for any incoming requests matching the pattern `llm_request_<id>.json`.
- **Rule**: For each discovered request file, extract the unique `<id>` string from the filename, read its JSON payload, call the appropriate LLM completion, and save the result directly to `llm_response_<id>.json` in the same directory. Once written, ensure files are cleaned up or unlinked to prevent stale state.


## 10. Rules Compliance & Mandatory Startup Check
- **Rule**: At the start of every session (the very first turn), the agent MUST read `.agents/AGENTS.md` in the workspace root and the active project's `task.md` (if in a project subdirectory) or workspace root `task.md` to ensure complete alignment with project-specific rules, constraints, and current state. The agent must never proceed with executing commands or answering user questions without validating this state.

## 11. Browser Subagent Permission Constraint
- **Rule**: The agent MUST NEVER invoke the `browser_subagent` tool or spawn any browser automation subagent without explicit written permission or instruction from the user. Even for visual verification or layout testing of styling edits, the agent should instruct the user to verify on their end instead of running the browser subagent automatically.

## 12. Token-Saving Search, Listing, and Testing Constraints
- **Rule**: **No Recursive Listings:** Never run recursive directory listings (`list_dir`) on the project root or directories containing deep dependencies (such as `node_modules`, `.venv`, `.git`). Always scope listings to immediate target folders.
- **Rule**: **Filtered Search:** When performing text searches via `grep_search`, always use specific query terms and apply target folder or file extension filters (e.g., `Includes=["*.py"]`) to limit matching lines. Avoid broad global searches without filters.
- **Rule**: **Quiet & Targeted Testing:** When executing unit or integration tests, always run them with the quiet flag (e.g., `pytest -q`) or target specific test files/functions directly rather than running the full verbose suite. This prevents long test execution logs from blobbing the context window.
- **Rule**: **Graph-Based File Reading:** Always use the `code-review-graph` server to identify the exact line ranges for target code symbols (classes, functions) first, and read only that range via `view_file`. Avoid reading full files over 150 lines.
- **Rule**: **No Manual/Command Polling Loops:** Never run shell loops containing `sleep` (e.g., `while true; do sleep 5; done`) or submit consecutive check commands (e.g. repeatedly checking process status in separate turns) to wait for background tasks. Instead, launch background jobs and let the agent turn go idle. The system's reactive wakeup mechanism will notify and resume the session automatically when the task finishes.

## 13. Mandatory AGENTS.md Compliance
- **Rule**: Every session, strictly follow ALL rules in `.agents/AGENTS.md` without exception. Read and internalize them before taking any action.
- **Rule**: At session start, build or update the `code-review-graph` for the active project before doing any code analysis. Always query the graph first to locate files and understand dependencies — never use `grep_search` or recursive `list_dir` to explore codebase structure.
- **Rule**: For complex multi-file changes inside the project folder (new module integrations, multi-file refactors), delegate implementation to OpenHands. Only write directly for simple single-file creations or trivial edits.
- **Rule**: The AGENTS.md rules are non-negotiable — never skip or shortcut them for convenience.

## 14. Leverage Agent Swarms (Parallel Execution) When Feasible
- **Rule**: Whenever tasks are decoupled and have no linear dependencies (such as parallel testing, parallel security/performance code reviews, or independent feature development on separate branches), the agent should design and leverage parallel agent swarms or concurrent execution loops rather than default to sequential operations. Apply this organically and systematically across current and future projects.
