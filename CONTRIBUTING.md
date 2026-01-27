# Contributing to BanglaJudex

Thank you for your interest in contributing to BanglaJudex! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and constructive in all interactions. We're building a tool to help the legal community in Bangladesh.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Create a new issue with:
   - Clear title
   - Description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)

### Suggesting Features

1. Open an issue with the "feature request" label
2. Describe the feature and its use case
3. Explain how it aligns with project goals

### Code Contributions

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Write/update tests
5. Ensure all tests pass: `pytest`
6. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/BanglaJudex.git
cd BanglaJudex

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install pytest pytest-asyncio black isort flake8

# Setup frontend
cd ../frontend
npm install
```

## Code Style

### Python

- Use **Black** for formatting
- Use **isort** for import sorting
- Use **flake8** for linting
- Write docstrings for all public functions

```bash
# Format code
black app/
isort app/

# Check linting
flake8 app/
```

### JavaScript/React

- Use **ESLint** and **Prettier**
- Prefer functional components with hooks
- Use TypeScript types where possible

```bash
npm run lint
npm run format
```

## Testing

All new features must include tests.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_parsing.py -v
```

## Pull Request Guidelines

1. **Title**: Clear, descriptive title
2. **Description**: Explain what and why
3. **Tests**: Include tests for new functionality
4. **Documentation**: Update docs if needed
5. **Small PRs**: Keep changes focused and manageable

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe your test approach

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
```

## Architecture Decisions

When proposing significant changes:

1. Open an issue for discussion first
2. Explain the problem and proposed solution
3. Consider alternatives
4. Document trade-offs

## Legal Considerations

- This is a research tool, not legal advice software
- Do not commit copyrighted judgment text
- Ensure all contributions can be MIT licensed

## Questions?

Open an issue or reach out to maintainers.

---

Thank you for contributing to BanglaJudex! 🙏
