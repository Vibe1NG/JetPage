# Getting Started

This section covers how to install and configure SiteGen.

## Overview

![SiteGen 3-column layout](./sitegen-overview.svg)

SiteGen presents your documentation in a clean 3-column layout: navigation sidebar on the left, content in the centre, and an "On This Page" TOC panel on the right.

## Prerequisites

- Python 3.12
- Poetry
- Podman (for container-based deployment)

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-org/sitegen.git
cd sitegen
poetry install
```

## Running Locally

```bash
poetry run python -m sitegen.main
```

Then open your browser at `http://localhost:8080`.
