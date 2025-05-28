# Installation

This project uses [uv](https://github.com/astral-sh/uv) as a package manager and a `pyproject.toml` file to manage dependencies.

## Prerequisites

Before you begin, ensure you have `uv` installed. If not, you can install it by following the instructions on the [official uv installation guide](https://github.com/astral-sh/uv?tab=readme-ov-file#installation).

## Installation Steps

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Create a virtual environment and install dependencies:**
    `uv` can create a virtual environment and install dependencies from `pyproject.toml` in a single step.
    ```bash
    uv venv
    uv pip install -e .
    ```
    Or, if you prefer to activate the environment first:
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
    uv pip install -e .
    ```
    The `-e .` flag installs the project in editable mode. If you have specific dependency groups (e.g., `dev`, `test`), you can install them like so:
    ```bash
    uv pip install -e .[dev,test]
    ```

3.  **Verify the installation:**
    After installation, you should be able to run the project's entry points or import its modules.

## Updating Dependencies

If the `pyproject.toml` file is updated, you can update your environment by running:
```bash
uv pip sync
```
This command will ensure your environment matches the exact dependencies specified in `pyproject.toml` and `uv.lock` (if present).
