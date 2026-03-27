# Easypanel Database Backup Automation

This script automates database and general application backups for the Easypanel hosting platform, specifically targeting users of the free version which has limitations on automatic backups. 

It iterates through your configured projects, identifies database services and application services, and triggers manual backup actions at a scheduled time every day.

## Features

- **Scheduled Backups**: Configure a specific time (HH:MM) for backups to run daily.
- **Environment Variable Configuration**: Keep your credentials and project names secure and separate from the code.
- **Full Support**: Backs up both **Database Services** and **General Application Services**.
- **Multiple Project Support**: List all your Easypanel projects that need backup.
- **Docker Ready**: Easily deploy as a container.

## Configuration

1.  **Environment Variables**:
    - Rename `.env.example` to `.env`.
    - `EASYPANEL_URL`: Your Easypanel API URL (e.g., `https://yourdomain.com/api`).
    - `EASYPANEL_TOKEN`: Your personal access token for Easypanel API.
    - `EASYPANEL_PROJECTS`: A comma-separated list of project names (e.g., `project1,project2,project3`).
    - `BACKUP_TIME`: Time to trigger backups in `HH:MM` format (e.g., `03:00` for 3 AM).

2.  **Dependencies**:
    - `requests`: To interact with the Easypanel API.
    - `python-dotenv`: To load configuration from `.env`.
    - `schedule`: To manage the backup timing.

## Installation

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/easypanel-exec-backups.git
cd easypanel-exec-backups

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit .env with your credentials

# Run the script
python main.py
```

### Docker Setup

```bash
docker-compose up --build -d
```

## How It Works

1.  **Scheduler**: The script uses the `schedule` library to check for the appointed backup time every minute.
2.  **Inspection**: It calls the `inspectProject` API to find all services within each project.
3.  **Backup Listing**: For each database service, it identifies the backup IDs.
4.  **Triggering**: Finally, it sends a POST request to `runDatabaseBackup` for each identified backup.

## Note

This script is intended for users who need a workaround for the backup limitations in the Easypanel free version. Use responsibly and ensure your backups are being stored correctly in your configured storage locations.
I'm not responsible for any damage caused by the use of this script.
