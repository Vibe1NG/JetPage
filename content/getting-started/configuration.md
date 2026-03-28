# Configuration

JetPage is configured through environment variables and the `content/_meta.json` file.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Port the web server listens on |
| `HOST` | `0.0.0.0` | Host address to bind |
| `CONTENT_DIR` | `./content` | Path to the content directory |

## Content Structure

Your content directory must contain a `_meta.json` file at the root that defines
the site title, documents, and navigation tree.

See the [Getting Started overview](getting-started/index) for a full example.
