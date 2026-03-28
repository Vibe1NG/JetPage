# Installation

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Podman (for container deployment)

## Install with uv

```bash
git clone https://github.com/your-org/jetpage.git
cd jetpage
uv sync
```

## Run the dev server

```bash
uv run python -m jetpage.main
```

Open `http://localhost:8080` in your browser.
