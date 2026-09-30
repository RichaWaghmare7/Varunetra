Put your model NetCDF file here, named `model.nc` (or update `MODEL_NC_PATH`
in docker-compose.yml to match your filename).

This directory is mounted read-only into the backend container at `/data`.
Also mounted into the scheduler container at `/app/data` for the ingestion
cron job — put `instruments.json`/`profiles.json` here too if you want the
scheduler's default command to find them (see infra/crontab).
