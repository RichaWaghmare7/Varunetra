#!/bin/bash
# infra/scheduler_entrypoint.sh
set -e
touch /var/log/ingest.log
echo "Starting cron scheduler for daily ingestion (see /etc/cron.d/ocean3d-ingest)"
cron
tail -f /var/log/ingest.log
