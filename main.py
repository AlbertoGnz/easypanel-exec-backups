import os
import requests
import json
import urllib.parse
import schedule
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
EASYPANEL_URL = os.getenv("EASYPANEL_URL", "https://easypanel.host.com.br/api")
EASYPANEL_TOKEN = os.getenv("EASYPANEL_TOKEN", "")
EASYPANEL_PROJECTS = os.getenv("EASYPANEL_PROJECTS", "").split(",")
BACKUP_TIME = os.getenv("BACKUP_TIME", "00:00")

# Note: This script executes database backup actions for the limited free version of Easypanel.

def inspect_project(project_name):
    """
    Inspects an Easypanel project to retrieve its services.
    """
    input_json = json.dumps({"json": {"projectName": project_name}})
    input_encoded = urllib.parse.quote(input_json)
    url = f"{EASYPANEL_URL}/trpc/projects.inspectProject?input={input_encoded}"
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error inspecting project {project_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to connect to Easypanel for project {project_name}: {e}")
        return None

def list_database_backups(project_name, service_name):
    """
    Lists backups for a specific database service.
    """
    input_json = json.dumps({"json": {"projectName": project_name, "serviceName": service_name}})
    input_encoded = urllib.parse.quote(input_json)
    url = f"{EASYPANEL_URL}/trpc/databaseBackups.listDatabaseBackups?input={input_encoded}"
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error listing backups for {service_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to list backups for {service_name}: {e}")
        return None

def run_database_backup(primary_domain_id):
    """
    Triggers a manual database backup.
    """
    payload = json.dumps({
        "json": {
            "id": primary_domain_id
        }
    })
        
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"{EASYPANEL_URL}/trpc/databaseBackups.runDatabaseBackup"
    try:
        requests.post(url, headers=headers, data=payload)
        print(f"Successfully triggered backup for ID: {primary_domain_id}")
    except Exception as e:
        print(f"Failed to trigger backup for ID {primary_domain_id}: {e}")

def perform_backup_routine():
    """
    Executes the full backup routine for all configured projects.
    """
    print(f"Starting backup routine at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not EASYPANEL_TOKEN or not EASYPANEL_PROJECTS[0]:
        print("Error: EASYPANEL_TOKEN or EASYPANEL_PROJECTS not configured in .env")
        return

    for project in EASYPANEL_PROJECTS:
        project = project.strip()
        if not project:
            continue
            
        print(f"Processing project: {project}")
        result = inspect_project(project)
        if result is None:
            continue
        
        try:
            services = result['result']['data']['json']['services']
            for service in services:
                # Retrieving backups for each service.
                backups = list_database_backups(service['projectName'], service['name'])
                if backups is None or len(backups['result']['data']['json']) == 0:
                    continue
                
                for backup in backups['result']['data']['json']:
                    # Execute the backups.
                    run_database_backup(backup['id'])
        except KeyError as e:
            print(f"Error parsing service info for project {project}: {e}")
            pass

def main():
    """
    Main entry point of the script, schedules the backup routine.
    """
    print(f"Backup scheduler started. Scheduled for: {BACKUP_TIME}")
    
    # Run once at startup to verify configuration
    # perform_backup_routine() 

    schedule.every().day.at(BACKUP_TIME).do(perform_backup_routine)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()