# Contributing to GarminTurso

We love your input! We want to make contributing to GarminTurso as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/dpshade/GarminTurso.git
cd GarminTurso

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
uv sync
# OR
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt

# Setup environment
cp .env.example .env
# Edit .env with your test credentials
```

## Testing

```bash
# Run basic functionality tests
python test_final.py

# Run report generation tests
python test_reports.py

# Test database creation
python -c "
import sys; sys.path.insert(0, 'src')
from database import TursoDatabase
db = TursoDatabase('./data/test.db')
db.connect()
db.create_schema()
print('Database test passed')
"

# Test imports
python -c "
import sys; sys.path.insert(0, 'src')
from auth import GarminAuthenticator
from garmin_collector import GarminCollector
from sync_service import GarminSyncService
print('Import test passed')
"
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings for public functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### Code Organization

```
src/
├── auth.py              # Authentication handling
├── database.py          # Database operations
├── garmin_collector.py  # Main data collection
├── sync_service.py      # Continuous sync functionality
├── enhanced_collector.py # Enhanced API collection
├── intraday_collector.py # Intraday data collection
└── fit_processor.py     # FIT file processing
```

## Submitting Changes

### Bug Fixes

1. Create an issue describing the bug
2. Reference the issue in your pull request
3. Include steps to reproduce the bug
4. Add tests that would have caught the bug

### New Features

1. Create an issue describing the feature
2. Discuss the implementation approach
3. Get approval before starting development
4. Include tests for the new functionality
5. Update documentation as needed

## Reporting Bugs

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/dpshade/GarminTurso/issues).

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Feature Requests

Feature requests are welcome! Please provide:

- **Use case**: Describe the problem you're trying to solve
- **Proposed solution**: How you envision the feature working
- **Alternatives**: Other approaches you've considered
- **Impact**: Who would benefit from this feature

## Security Considerations

- Never commit credentials, API keys, or personal data
- Be mindful of Garmin's API rate limits and terms of service
- Ensure authentication tokens are handled securely
- Report security vulnerabilities privately

## Code Review Process

All submissions require review. We use GitHub pull requests for this purpose.

### Review Criteria

- **Functionality**: Does the code work as intended?
- **Testing**: Are there adequate tests?
- **Documentation**: Is the code well-documented?
- **Style**: Does it follow our coding standards?
- **Security**: Are there any security concerns?
- **Performance**: Does it impact performance negatively?

## Getting Help

- Check existing [issues](https://github.com/dpshade/GarminTurso/issues)
- Read the [CLAUDE.md](CLAUDE.md) developer documentation
- Join discussions in issue comments

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- README.md acknowledgments
- Release notes
- GitHub contributors page

Thank you for contributing to GarminTurso! 🚀