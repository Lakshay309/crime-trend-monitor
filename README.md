# Cambridge Crime Trend Monitor

A data engineering project that collects Cambridge Police Daily Log records, validates and transforms the data, stores it in a database, and presents crime trends through a Streamlit dashboard.

The project supports two separate runtime configurations:

- **Local / Windows:** SQLite database, local Prefect server, and Streamlit.
- **Docker:** PostgreSQL database with the application services running in containers.

> **Important:** These environments use separate databases. Data stored in the local SQLite database is not automatically copied to the Docker PostgreSQL database.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Clone the Repository](#clone-the-repository)
- [Configure Environment Variables](#configure-environment-variables)
- [Option 1: Run Locally with SQLite](#option-1-run-locally-with-sqlite)
- [Option 2: Run with Docker and PostgreSQL](#option-2-run-with-docker-and-postgresql)
- [Useful Docker Commands](#useful-docker-commands)
- [Accessing the Services](#accessing-the-services)
- [Database Persistence](#database-persistence)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

The pipeline follows these general stages:

1. **Extract** — retrieve crime incident records from the Cambridge Police Daily Log data source.
2. **Validate** — check the incoming records and required fields.
3. **Transform** — clean records, handle duplicates, normalize fields, and derive useful date-related features.
4. **Load** — write the processed records to SQLite or PostgreSQL.
5. **Visualize** — explore the stored data through the Streamlit dashboard.

Prefect is used to orchestrate and monitor pipeline execution.

---

## Prerequisites

### For local execution on Windows

- Windows 10/11
- Python **3.11**
- Git
- A terminal such as PowerShell

### For Docker execution

- Docker Engine or Docker Desktop
- Docker Compose v2 (`docker compose`)
- Git

---

## Clone the Repository

Open PowerShell and run:

```powershell
git clone https://github.com/Lakshay309/crime-trend-monitor
cd crime-trend-monitor
```

If the repository is already on your machine, navigate to its directory instead:

```powershell
cd D:\Coding\crime-trend-monitor
```

---

## Configure Environment Variables

Create a `.env` file in the project root directory. Add the environment variables required by the project.

For the **local SQLite configuration**, the database settings are:

```env
DATABASE_TYPE=sqlite
SQLITE_PATH=data/crime_monitor.db
```

For the **Docker PostgreSQL configuration**, provide the PostgreSQL credentials expected by `docker-compose.yml`:

```env
POSTGRES_USER=your_database_user
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=your_database_name
```

Also add any source/API credentials required by the extractor, using the variable names defined in the project's configuration file.

**Security notes:**

- Do not commit `.env` to Git.
- Do not put real passwords, API tokens, or other secrets in this README.
- Keep `.env` in `.gitignore`.
- Use a strong, unique PostgreSQL password for any internet-accessible deployment.

---

## Option 1: Run Locally with SQLite

These instructions are for running the project directly on Windows without Docker.

### 1. Create a Python virtual environment

From the project root:

```powershell
py -3.11 -m venv .venv
```

### 2. Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this for the current terminal session and try activation again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Upgrade pip and install the packages listed in `requirements.txt`:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure SQLite

Ensure your `.env` contains:

```env
DATABASE_TYPE=sqlite
SQLITE_PATH=data/crime_monitor.db
```

### 5. Start the Prefect server

Open **Terminal 1**:

```powershell
cd D:\Coding\crime-trend-monitor
.venv\Scripts\Activate.ps1
prefect server start
```

Keep this terminal running. The Prefect UI is available at:

`http://localhost:4200`

### 6. Run the pipeline

Open **Terminal 2**:

```powershell
cd D:\Coding\crime-trend-monitor
.venv\Scripts\Activate.ps1
python -m pipeline.flow
```

### 7. Start the dashboard

Open **Terminal 3**:

```powershell
cd D:\Coding\crime-trend-monitor
.venv\Scripts\Activate.ps1
streamlit run app.py
```

### 8. Keep Alive

Open **Terminal 4**:

```powershell
python -c "from pipeline.flow import crime_pipeline; crime_pipeline.serve(name='daily-crime-monitor', cron='30 18 * * *')"
```

Streamlit will print the local dashboard URL in the terminal. It is usually:

`http://localhost:8501`

---

## Option 2: Run with Docker and PostgreSQL

Docker runs the application services in containers and uses PostgreSQL instead of the local SQLite database.

Make sure Docker is running and that your `.env` file contains the PostgreSQL credentials required by `docker-compose.yml`.

### 1. Open the project directory

```bash
cd crime-trend-monitor
```

On Windows PowerShell, use the full local path:

```powershell
cd D:\Coding\crime-trend-monitor
```

### 2. (Optional) Remove existing containers and volumes

Use this only when you intentionally want a **fresh deployment with existing Docker volume data deleted**:

```bash
docker compose down -v --remove-orphans
```

This deletes the Compose-managed database and service volumes, including PostgreSQL data and persisted service metadata. It does not delete your source code or your local SQLite database.

To restart without deleting persistent data, use:

```bash
docker compose down
```

### 3. Build and start the services

```bash
docker compose up -d --build
```

Check the service status:

```bash
docker compose ps
```

### 4. Trigger the pipeline

The Docker pipeline service registers and serves the Prefect deployment. Trigger a run manually with:

```bash
docker exec crime_pipeline prefect deployment run "Cambridge Crime Monitoring Pipeline/daily-crime-monitor"
```

### 5. Monitor pipeline logs

```bash
docker compose logs -f crime-pipeline
```

Press `Ctrl+C` to stop following the logs. This does not stop the containers.

### 6. Verify the PostgreSQL records

Run:

```bash
docker exec -it crime_postgres psql -U crime_admin -d cpd_db -c "SELECT COUNT(*) FROM cpd_incidents;"
```

The command prints the number of records currently stored in `cpd_incidents`.

---

## Useful Docker Commands

| Task | Command |
|---|---|
| Start services | `docker compose up -d` |
| Build and start | `docker compose up -d --build` |
| Check status | `docker compose ps` |
| Stop services and preserve volumes | `docker compose down` |
| Follow all service logs | `docker compose logs -f` |
| Follow pipeline logs | `docker compose logs -f crime-pipeline` |
| View Metabase logs | `docker compose logs --tail=100 metabase` |
| Restart one service | `docker compose restart metabase` |
| Recreate one service | `docker compose up -d --force-recreate metabase` |
| Remove containers and volumes | `docker compose down -v --remove-orphans` |

**Warning:** `docker compose down -v` permanently removes the Compose-managed volumes. Do not use it for an ordinary restart.

---

## Accessing the Services

When running locally, use `localhost` and the ports printed by the application.

For the Docker deployment, the typical service URLs are:

| Service | Local URL |
|---|---|
| Streamlit dashboard | `http://localhost:8501` |
| Prefect UI | `http://localhost:4200` |
| Metabase | `http://localhost:3000` |
| pgAdmin | `http://localhost:8082` |

For a remote EC2 deployment, replace `localhost` with the EC2 public IP address, for example:

- `http://<EC2_PUBLIC_IP>:8501`
- `http://<EC2_PUBLIC_IP>:4200`
- `http://<EC2_PUBLIC_IP>:3000`
- `http://<EC2_PUBLIC_IP>:8082`

A service is reachable remotely only if Docker publishes its port on an external interface and the EC2 security group and host firewall permit the connection. Restrict administrative tools such as Metabase, Prefect, and pgAdmin to trusted IP addresses or place them behind a secure access layer. Do not expose database port 5432 publicly.

---

## Database Persistence

Docker Compose uses named volumes to persist data beyond the lifetime of an individual container.

| Data | Persistence |
|---|---|
| PostgreSQL records | `crime_postgres_data` volume |
| Metabase application data | `crime_metabase_data` volume |
| pgAdmin data | `crime_pgadmin_data` volume |
| Prefect server data | `crime_prefect_data` volume |
| Local SQLite records | `data/crime_monitor.db` on the host |

- `docker compose down` removes containers and the Compose network but preserves named volumes.
- `docker compose up -d` recreates containers and reuses those volumes.
- `docker compose down -v` removes the Compose-managed named volumes and their data.
- The local SQLite database is separate and is not removed by Docker Compose.

For normal shutdowns and restarts, use `docker compose down` rather than `docker compose down -v`.

---

## Troubleshooting

### PowerShell cannot activate the virtual environment

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### Python package import or dependency errors

Confirm that the virtual environment is active, then run:

```powershell
python -m pip install -r requirements.txt
```

### A Docker service is not starting

Check its status and logs:

```bash
docker compose ps
docker compose logs --tail=100 <service-name>
```

Replace `<service-name>` with the relevant Compose service, such as `metabase`, `postgres`, `crime-pipeline`, or `frontend`.

### A service works on the EC2 instance but not from your browser

Check the published port:

```bash
docker ps
```

For external access, the port mapping should generally show `0.0.0.0:<HOST_PORT>-><CONTAINER_PORT>/tcp` rather than `127.0.0.1:<HOST_PORT>->...`. Also verify the EC2 security group and host firewall rules.

### Check the PostgreSQL container

```bash
docker compose ps postgres
docker compose logs --tail=100 postgres
```

---

## Notes

- Use Python 3.11 for the documented local setup.
- Activate `.venv` in each new PowerShell terminal before running local Python commands.
- Run the local SQLite setup and Docker PostgreSQL setup as separate environments.
- Keep credentials in `.env`, not in source control or this README.
![alt text](<Screenshot 2026-11-17 181351.png>)