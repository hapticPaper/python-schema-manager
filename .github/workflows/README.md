# GitHub Actions Workflows

This repository includes two GitHub Actions workflows for continuous integration and package publishing.

## Workflows

### 1. CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual dispatch

**What it does:**
- Runs tests on multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12)
- Tests on multiple operating systems (Ubuntu, macOS, Windows)
- Performs code quality checks:
  - Linting with flake8
  - Code formatting with black
  - Type checking with mypy
  - Unit tests with pytest
  - Code coverage reporting

**Code coverage** is uploaded to Codecov for the Python 3.11/Ubuntu combination.

### 2. Publish Workflow (`publish.yml`)

**Triggers:**
- Automatic: When a new GitHub Release is published
- Manual: Via workflow_dispatch with option to publish to TestPyPI or PyPI

**What it does:**
1. **Build Job**: Creates source and wheel distributions
2. **Publish Job**: Publishes to PyPI or TestPyPI depending on trigger

**Publishing options:**
- **TestPyPI** (for testing): Manual dispatch without `publish_to_pypi` flag
- **Production PyPI**: Automatically on release OR manual dispatch with `publish_to_pypi` flag

## Setup Requirements

### For CI Workflow

No setup required - works out of the box.

Optional: Set up [Codecov](https://codecov.io/) for coverage reporting:
1. Sign up at codecov.io
2. Add your repository
3. No token needed for public repositories

### For Publish Workflow

The workflow uses **Trusted Publishing** (OIDC), which is the recommended secure method. No API tokens needed!

#### Setting up PyPI Trusted Publishing

1. **For TestPyPI:**
   - Go to https://test.pypi.org
   - Create an account and verify email
   - Go to Account Settings → Publishing
   - Add a new publisher:
     - PyPI Project Name: `python-schema-manager`
     - Owner: `hapticPaper`
     - Repository name: `python-schema-manager`
     - Workflow name: `publish.yml`
     - Environment name: `testpypi`

2. **For Production PyPI:**
   - Go to https://pypi.org
   - Create an account and verify email
   - Go to Account Settings → Publishing
   - Add a new publisher:
     - PyPI Project Name: `python-schema-manager`
     - Owner: `hapticPaper`
     - Repository name: `python-schema-manager`
     - Workflow name: `publish.yml`
     - Environment name: `pypi`

#### GitHub Environment Setup (Optional)

For additional control, set up environments in GitHub:

1. Go to repository Settings → Environments
2. Create two environments:
   - `testpypi` - for TestPyPI publishing
   - `pypi` - for production PyPI publishing
3. For `pypi` environment, add protection rules:
   - Required reviewers (recommended)
   - Limit to `main` branch

## Usage

### Running Tests

Tests run automatically on every push and pull request to `main` or `develop`.

To manually trigger tests:
1. Go to Actions tab
2. Select "CI" workflow
3. Click "Run workflow"

### Publishing to TestPyPI (Testing)

1. Go to Actions tab
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Leave "Publish to production PyPI" **unchecked**
5. Click "Run workflow"

This will publish to https://test.pypi.org for testing.

### Publishing to Production PyPI

#### Method 1: GitHub Release (Recommended)
1. Go to Releases
2. Click "Draft a new release"
3. Create a new tag (e.g., `v0.1.0`)
4. Fill in release notes
5. Click "Publish release"

The package will be automatically built and published to PyPI.

#### Method 2: Manual Dispatch
1. Go to Actions tab
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. **Check** "Publish to production PyPI"
5. Click "Run workflow"

## Version Management

Before publishing, ensure the version in `pyproject.toml` is updated:

```toml
[project]
version = "0.1.0"  # Update this before release
```

## Testing the Package After Publishing

### From TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple python-schema-manager
```

### From PyPI:
```bash
pip install python-schema-manager
```

## Troubleshooting

### Build Fails
- Check that all tests pass locally: `pytest tests/`
- Verify code formatting: `black --check .`
- Check linting: `flake8 .`
- Verify types: `mypy schema_registry`

### Publish Fails
- **First time publishing**: Ensure Trusted Publishing is set up on PyPI
- **Version conflict**: Update version in `pyproject.toml` (PyPI doesn't allow re-uploading same version)
- **Environment protection**: Check if environment has required reviewers

### Trusted Publishing Not Working
- Verify the publisher settings on PyPI match exactly:
  - Repository owner
  - Repository name
  - Workflow filename
  - Environment name
- Check that the workflow has `id-token: write` permission

## Best Practices

1. **Test before publishing**: Always test on TestPyPI first
2. **Use releases**: Prefer GitHub Releases over manual dispatch for production
3. **Semantic versioning**: Follow [semver](https://semver.org/) for version numbers
4. **Update CHANGELOG**: Update `CHANGELOG.md` before each release
5. **Review changes**: Check the built package with `twine check dist/*` locally before pushing

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
