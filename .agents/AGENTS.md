# Token-Efficient Collaborative System Rules (Antigravity + Graph + OpenHands)

To optimize native performance and stay strictly within the 8% remaining Gemini model quota, all agents working in this workspace must adhere to the following rules:

## 1. Graph-First Codebase Analysis
- **Rule**: Never run directory recursive listings (`list_dir`) or generic searches (`grep_search`) to understand codebase architecture or dependencies.
- **Rule**: Always query the `code-review-graph` server first (e.g., using `query_graph_tool`, `get_impact_radius_tool`, or `list_flows_tool`).
- **Rule**: Only load specific files identified by the graph analysis. Never load files larger than 150 lines in their entirety; request specific line ranges using `view_file` to conserve context.

## 2. Strict OpenHands Delegation
- **Rule**: Antigravity must act strictly as **The Brain** (Architect/Planner). It must **not** directly write code changes, run iterative debugging/build cycles, or write unit tests.
- **Rule**: All coding tasks, boilerplate generation, debugging loops, and test executions must be delegated to **OpenHands** via the `openhands.run_task` tool.
- **Rule**: When delegating:
  - Provide a highly specific prompt containing only the necessary context (e.g., paths of target files, target behavior, and test commands).
  - Do **not** pass full history or unrelated files to the OpenHands prompt.

## 3. No Status Polling (Async Execution)
- **Rule**: After calling `openhands.run_task`, the agent must immediately go idle (stop calling tools or schedule a fallback timer).
- **Rule**: Do **not** poll `openhands.get_task_status` or run `sleep` commands. The system's reactive wakeup mechanism will automatically resume execution once OpenHands completes.

## 4. Summarization and Verification
- **Rule**: When OpenHands finishes, only request the final diff and a brief test pass summary. Do not output raw build logs or stack traces to the main chat.
- **Rule**: Use the `code-review-graph` to review changes post-implementation to ensure architectural integrity.
