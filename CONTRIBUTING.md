# Contributing to DistillAI

We welcome contributions from developers and researchers.

## How to Contribute

### Bug Reports
1. Search existing issues first
2. Create a clear issue with:
   - Environment (OS, Python version)
   - Steps to reproduce
   - Expected vs actual behavior
   - Error logs

### Code Contributions
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for new features
4. Ensure all tests pass: `python -m pytest`
5. Commit with clear messages
6. Submit a Pull Request

### Code Style
- Follow PEP 8
- Add type hints where possible
- Include docstrings for public functions
- Keep functions small and focused

### Commit Message Format
```
type(scope): short description

Longer explanation if needed.

Fixes: #issue-number
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## Development Setup

```bash
# Clone
git clone https://github.com/6ss6com/distill-ai.git
cd distill-ai

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

## Questions?
Open an issue or start a discussion.