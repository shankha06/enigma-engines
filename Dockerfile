# Install uv
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Change the working directory to the `app` directory
WORKDIR /app

# Copy the lockfile and `pyproject.toml` into the image
COPY uv.lock /app/uv.lock
COPY pyproject.toml /app/pyproject.toml

# Install dependencies
RUN uv sync --all-groups --frozen --no-install-project

# Copy the project into the image
COPY . /app

# Sync the project
RUN uv sync --all-groups --frozen

CMD [ "python", "enigma_engines/animal_crossing/simulation.py" ]
