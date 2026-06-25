# Container runtime for route-optimizer-factory: the queue worker + the optimizer
# engine it runs as a subprocess.
FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; pandas/numpy/openpyxl ship manylinux wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install runtime deps first for layer caching (engine + worker).
COPY optimizer/requirements.txt /app/optimizer/requirements.txt
COPY worker/requirements.txt    /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/optimizer/requirements.txt \
    && pip install --no-cache-dir -r /app/worker/requirements.txt

# App code.
COPY optimizer/ /app/optimizer/
COPY contract/  /app/contract/
COPY worker/    /app/worker/

# Smoke check that the engine imports and runs at build time.
RUN echo '{}' | python /app/optimizer/cli.py --mode config --out-dir /tmp >/dev/null

# Run the worker loop. It runs /app/worker/run.py; Python puts /app/worker on the
# path so the bare imports resolve, and cli.py is found at /app/optimizer/cli.py.
CMD ["python", "/app/worker/run.py"]
