# Acme Parser — turn messy logs into typed events

Acme Parser is a Python library **for backend engineers** who need to turn
unstructured application logs into typed, queryable events. It exists because
grep-and-regret does not scale past a few services.

![Acme Parser pipeline diagram](https://example.com/acme/pipeline.png)

## What problem does it solve?

Logs arrive as free text. Acme Parser maps each line to a typed event with a
stable schema, so downstream code queries fields instead of scraping strings.

## How do I install it?

Install from PyPI with your package manager of choice. See the
[full guide](https://example.com/acme/install) for platform notes.

## Where do I go next?

- [Quickstart](https://example.com/acme/quickstart)
- [API reference](https://example.com/acme/api)
