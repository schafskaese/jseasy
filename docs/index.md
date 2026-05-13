# jsEasy Documentation

jsEasy is a lightweight Python runtime for executing JavaScript against a small browser-like DOM without launching a browser.

## Start Here

- [README](../README.md)
- [API Reference](api.md)
- [Recipes](recipes.md)
- [Troubleshooting](troubleshooting.md)

## Project Notes

- [Limitations And Compatibility](limitations.md)
- [iv8 Comparison](iv8-comparison.md)
- [Release Checklist](release.md)

## Core Concepts

jsEasy is optimized for scraping and testing workflows where:

- HTML is available through HTTP;
- JavaScript mutates the DOM;
- data may be loaded through `fetch()` or XHR;
- final extraction is done through selectors.

It is not a rendering engine and does not aim to behave like Chrome in every detail.
