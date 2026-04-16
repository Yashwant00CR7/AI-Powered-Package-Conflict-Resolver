# Stylize

Strict coding conventions for the AI to follow in every file.

- **Error Handling**: Use `try-except-finally` blocks extensively, especially around network/API calls. Log errors with full context using the project's `logger`.
- **Naming**: Snake_case for functions and variables. PascalCase for classes. Prefix private methods with `_`.
- **Typing**: Use Python type hints (`from typing import ...`) for all function signatures and complex variables.
- **Async First**: Utilize `async/await` for all IO-bound tasks (API, DB, Search). Use `nest_asyncio` only if event loop conflicts occur in entry points.
- **LLM Prompting**: Keep prompts in `agents.py` versioned and descriptive. Use structured output (JSON/Tool calls) whenever possible.
- **Documentation**: Use Sphinx/Google-style docstrings for all functions and classes.
