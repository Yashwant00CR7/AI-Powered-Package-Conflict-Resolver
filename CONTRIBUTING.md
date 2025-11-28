# Contributing to AI-Powered Package Conflict Resolver

Thank you for your interest in contributing! 🎉

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/package_conflict_resolver.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Make your changes
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install browsers
crawl4ai-setup

# Set up environment
cp .env.example .env
# Add your GOOGLE_API_KEY
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and modular

## Testing

Before submitting a PR:
1. Test your changes with `python main.py`
2. Ensure no errors in the web interface: `adk web web_app.py --no-reload`

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Error message (full stack trace)
- Steps to reproduce

## Questions?

Feel free to open an issue for any questions or discussions!
