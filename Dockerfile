# Container runtime for route-optimizer-factory.
# Phase 1: builds the optimizer engine + deps so `cli.py` runs in a container.
# Phase 4: the worker loop (worker/run.py) becomes the CMD.
FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; pandas/numpy/openpyxl ship manylinux wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install runtime deps first for layer caching.
COPY optimizer/requirements.txt /app/optimizer/requirements.txt
RUN pip install --no-cache-dir -r /app/optimizer/requirements.txt

# App code.
COPY optimizer/ /app/optimizer/
COPY contract/ /app/contract/
COPY worker/   /app/worker/

# Smoke check that the engine imports and runs at build time.
RUN echo '{}' | python /app/optimizer/cli.py --mode config --out-dir /tmp >/dev/null

# Phase 4: replace with the worker loop, e.g.
#   CMD ["python", "/app/worker/run.py"]
CMD ["python", "-c", "print('route-optimizer-factory: worker loop not implemented yet (Phase 4). optimizer/ is runnable via cli.py.')"]
