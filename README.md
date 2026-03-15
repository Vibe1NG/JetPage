# SiteGen
Generate webistes with markdown content directory similar to Nextra but using Flet

## Goal

1. Use [Flet](https://flet.dev/) to create and run a website that the pages are generated from a content directory with markdown.
1. Allow for expansion of the Markdown language such that it can support everything Nextra does, but using python code as the parsing mechnaism instead of Node.
    1. No node, react or nextra dependencies 
1. Navigation configured via json file similar to Nextra but have the notion of a 'document'. 
    1. Allow for the website to be downloaded as a PDF, with same outline (table of contents) as a 'document' in the website based on the navigation configuration.
    1. A document is a first class citizen in this context. It should be what the website is structured around.
1. It should support the ability to create latex syntax within the Markdown and parse it.
1. Application must use a Containerfile to run, with minimal/python hardened container from ironbank as the base image.

## Tools
1. Python 3.12
1. Poetry - for python build and dependency management
1. [Flet](https://flet.dev/)
1. PDF generation with Playwrite
1. Podman - to run the images locally

## Build

Build the container image using Podman:

```bash
podman build -t sitegen -f Containerfile .
```

Or with the Makefile:

```bash
make build
```

This installs production dependencies via Poetry and downloads Playwright's Chromium browser (used for PDF export) inside the image.

## Run

**Local development** (requires Python 3.12 and Poetry):

```bash
poetry install
poetry run python -m sitegen.main
```

Or with the Makefile:

```bash
make run
```

The app starts on `http://localhost:8080` by default.

**From the container image:**

```bash
podman run -p 8080:8080 sitegen
```

To serve custom content, mount your content directory:

```bash
podman run -p 8080:8080 -v ./content:/app/content:ro sitegen
```

**Environment variables:**

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Port the web server listens on |
| `HOST` | `0.0.0.0` | Bind address |
| `CONTENT_DIR` | `/app/content` | Path to the markdown content directory |

## Testing

### Unit and BDD tests

Runs pytest (unit/integration) and Behave (BDD feature files):

```bash
make test
```

Or individually:

```bash
# pytest only
poetry run pytest tests/ -v --ignore=tests/e2e

# Behave only
poetry run behave features/
```

### End-to-end tests (Playwright)

The e2e suite starts the SiteGen server automatically — no manual `make run` needed.

Install the Chromium browser on first run:

```bash
poetry run playwright install chromium
```

Then run the tests:

```bash
make test-e2e
```

Or directly:

```bash
poetry run pytest tests/e2e/ -v
```

The suite opens one browser session shared across all tests (~70s total). It tests:

- Flutter app shell renders (canvas, accessibility overlay)
- All document tabs and sidebar nav items are present
- Clicking sidebar links changes the page content
- Switching document tabs changes the sidebar

> **Note:** Flet's CanvasKit renderer draws everything to a `<canvas>` — text is
> not in the DOM. Navigation is driven by clicking Flutter semantic nodes, and
> content changes are verified by screenshot comparison.

