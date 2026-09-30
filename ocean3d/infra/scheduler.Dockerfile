# infra/scheduler.Dockerfile
# Per Deployment Plan step 6: "Add a cron job or scheduled task that pulls
# new model NetCDF files ... and runs the Argo/Glider ingestion script into
# PostGIS on a regular interval (e.g. daily)."
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron postgresql-client libhdf5-dev libnetcdf-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ingestion/ ./ingestion/
RUN pip install --no-cache-dir xarray netCDF4 psycopg2-binary

COPY infra/crontab /etc/cron.d/ocean3d-ingest
RUN chmod 0644 /etc/cron.d/ocean3d-ingest && crontab /etc/cron.d/ocean3d-ingest

COPY infra/scheduler_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
