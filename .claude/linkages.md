# Linkages

Define how agents and services interact to prevent integration bugs.

**Data Flow:**
1. **Input**: User Query -> Root Agent.
2. **Phase 1 (History Check)**: Root Agent -> Context Search Agent -> Pinecone -> Root Agent.
3. **Phase 2 (Research)**: Root Agent -> Parallel Research Team -> Web Docs/Community -> Root Agent.
4. **Phase 3 (Surgery)**: Root Agent -> Code Surgeon -> Validation -> `requirements.txt` Fix.
5. **Output**: Result -> User UI / MCP Client.

**Agent Communication:**
- Every agent must log its "Thought" and "Action" to the centralized logger.
- Tools must return typed strings or JSON objects to ensure LLM parsing consistency.
- Session ID is the primary key for state across all service layers.
