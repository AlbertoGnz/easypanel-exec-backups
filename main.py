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
    print(f"  --> Inspecting project: {project_name}...")
    input_json = json.dumps({"json": {"projectName": project_name}})
    input_encoded = urllib.parse.quote(input_json)
    url = f"{EASYPANEL_URL}/trpc/projects.inspectProject?input={input_encoded}"
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            try:
                services_count = len(data['result']['data']['json']['services'])
                print(f"  [OK] Project {project_name} inspected. Found {services_count} services.")
            except:
                print(f"  [OK] Project {project_name} inspected, but services structure is unusual.")
            return data
        else:
            print(f"  [ERROR] Inspecting project {project_name}: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"  [ERROR] Failed to connect for project {project_name}: {e}")
        return None

def list_database_backups(project_name, service_name):
    """
    Lists backups for a specific database service.
    """
    print(f"      --> Fetching backup configurations for service: {service_name}...")
    input_json = json.dumps({"json": {"projectName": project_name, "serviceName": service_name}})
    input_encoded = urllib.parse.quote(input_json)
    url = f"{EASYPANEL_URL}/trpc/databaseBackups.listDatabaseBackups?input={input_encoded}"
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            try:
                backups_count = len(data['result']['data']['json'])
                print(f"      [OK] Found {backups_count} backup configurations for {service_name}.")
            except:
                print(f"      [OK] Backup list fetched for {service_name}.")
            return data
        else:
            print(f"      [ERROR] Listing backups for {service_name}: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"      [ERROR] Failed to list backups for {service_name}: {e}")
        return None

def run_database_backup(primary_domain_id, service_name):
    """
    Triggers a manual database backup.
    """
    print(f"          --> Triggering backup action for {service_name} (ID: {primary_domain_id})...")
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
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            print(f"          [SUCCESS] Backup triggered successfully for {service_name}.")
        else:
            print(f"          [FAILED] Trigger status {response.status_code} for {service_name}. Response: {response.text}")
    except Exception as e:
        print(f"          [ERROR] Request failed for {service_name}: {e}")

def perform_backup_routine():
    """
    Executes the full backup routine for all configured projects.
    """
    print("\n" + "="*60)
    print(f"BACKUP ROUTINE STARTED - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if not EASYPANEL_TOKEN or not EASYPANEL_PROJECTS or not EASYPANEL_PROJECTS[0]:
        print("[CRITICAL] EASYPANEL_TOKEN or EASYPANEL_PROJECTS not configured in .env")
        return

    projects_processed = 0
    backups_triggered = 0

    for project in EASYPANEL_PROJECTS:
        project = project.strip()
        if not project:
            continue
            
        print(f"\n[*] Processing Project: {project}")
        result = inspect_project(project)
        if result is None:
            continue
        
        projects_processed += 1
        try:
            services = result['result']['data']['json']['services']
            for service in services:
                # Retrieving backups for each service.
                backups = list_database_backups(service['projectName'], service['name'])
                if backups is None:
                    continue
                
                try:
                    backup_list = backups['result']['data']['json']
                    if len(backup_list) == 0:
                        print(f"      [INFO] No backup configurations found for service {service['name']}.")
                        continue
                    
                    for backup in backup_list:
                        # Execute the backups.
                        run_database_backup(backup['id'], service['name'])
                        backups_triggered += 1
                except (KeyError, TypeError) as e:
                    print(f"      [ERROR] Could not parse backup list for {service['name']}: {e}")
                    
        except KeyError as e:
            print(f"  [ERROR] Error parsing service info for project {project}: {e}")
            pass

    print("\n" + "="*60)
    print(f"BACKUP ROUTINE FINISHED - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Summary: {projects_processed} projects processed, {backups_triggered} backups triggered.")
    print("="*60 + "\n")

def main():
    """
    Main entry point of the script, schedules the backup routine.
    """
    print("\n" + "!"*60)
    print("EASYPANEL BACKUP SERVICE INITIALIZED")
    print(f"Scheduled daily at: {BACKUP_TIME}")
    print(f"Targeting projects: {', '.join(EASYPANEL_PROJECTS)}")
    print("!"*60 + "\n")
    
    # Run once at startup to verify configuration (optional)
    # perform_backup_routine() 

    schedule.every().day.at(BACKUP_TIME).do(perform_backup_routine)

    while True:
        schedule.run_pending()
        time.sleep(30) # Check every 30 seconds

if __name__ == "__main__":
    main()