# Contributing to Zero-Trust Secure Software Supply Chain

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Report unacceptable behavior

## Getting Started

### Prerequisites

- Azure CLI (v2.50+)
- Terraform (v1.5+)
- kubectl (v1.28+)
- Python 3.11+
- Docker 24.0+
- GitHub account

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/falsaafani/Zero-Trust-Secure-Software-Supply-Chain-on-Azure.git
cd Zero-Trust-Secure-Software-Supply-Chain-on-Azure

# Install Python dependencies
cd App
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run app locally
python src/app.py
```

## Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, documented code
   - Add tests for new features
   - Update documentation

4. **Run quality checks**
   ```bash
   # Run tests
   pytest tests/ -v

   # Check code formatting
   black App/src/
   flake8 App/src/

   # Security scan
   bandit -r App/src/

   # Type checking
   mypy App/src/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `test:` Tests
   - `refactor:` Code refactoring
   - `chore:` Maintenance

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Process

1. **Update documentation**
   - README.md for user-facing changes
   - Comments for complex code
   - ADRs for architecture decisions

2. **Ensure CI passes**
   - All tests pass
   - Security scans clean
   - Code coverage > 80%

3. **Request review**
   - Assign reviewers
   - Address feedback
   - Resolve conversations

4. **Merge requirements**
   - 1+ approvals
   - All checks passing
   - Up to date with main

## Coding Standards

### Python

- Follow PEP 8
- Use type hints
- Write docstrings
- Max line length: 100
- Use Black for formatting

### Terraform

- Use consistent naming
- Add descriptions to variables
- Use modules for reusability
- Tag all resources
- Document outputs

### Kubernetes

- Use namespaces
- Set resource limits
- Add labels and annotations
- Use secrets for sensitive data
- Implement health checks

## Testing Requirements

### Unit Tests

- Test all business logic
- Mock external dependencies
- Use pytest fixtures
- Aim for >80% coverage

```python
def test_app_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
```

### Integration Tests

- Test API endpoints
- Test database interactions
- Test external services

### Security Tests

- Test authentication
- Test authorization
- Test input validation
- Test for common vulnerabilities

## Infrastructure Changes

When modifying Terraform:

1. Run `terraform fmt`
2. Run `terraform validate`
3. Run `checkov -d terraform/`
4. Test in dev environment first
5. Document changes in PR

## Documentation

- Keep README.md updated
- Document architecture decisions
- Add inline comments for complex logic
- Update diagrams if needed
- Include examples

## Questions?

- Open a discussion on GitHub
- Check existing issues
- Review documentation

Thank you for contributing! 🎉
