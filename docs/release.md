# Release Checklist

This project is configured for standard PyPI packaging with Hatchling.

## Local Release Verification

1. Update the version in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Reinstall development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests:

   ```bash
   pytest
   ```

5. Build distributions:

   ```bash
   python -m build
   ```

6. Validate metadata:

   ```bash
   twine check dist/*
   ```

## TestPyPI

Upload to TestPyPI first:

```bash
twine upload --repository testpypi dist/*
```

Install from TestPyPI in a clean environment:

```bash
python -m venv /tmp/jseasy-test
/tmp/jseasy-test/bin/python -m pip install --index-url https://test.pypi.org/simple/ jseasy
/tmp/jseasy-test/bin/python -c "from jseasy import Page; print(Page.from_html('<h1>ok</h1>').select('h1').text)"
```

## PyPI

```bash
twine upload dist/*
```

## GitHub Release

1. Push the version commit.
2. Create a tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. Draft a GitHub release from the tag.

The included publish workflow can publish to PyPI from GitHub releases if trusted publishing is configured in PyPI.
