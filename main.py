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

# Note: This script executes database and general service backup actions for the limited free version of Easypanel.

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
                print(f"  [OK] Project {project_name} inspected.")
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
        return None
    except:
        return None

def list_service_backups(project_name, service_name):
    """
    Lists backups for a general application service (not a database).
    """
    input_json = json.dumps({"json": {"projectName": project_name, "serviceName": service_name}})
    input_encoded = urllib.parse.quote(input_json)
    url = f"{EASYPANEL_URL}/trpc/serviceBackups.listServiceBackups?input={input_encoded}"
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def run_database_backup(primary_domain_id, service_name):
    """
    Triggers a manual database backup.
    """
    print(f"          --> DB: Triggering backup for {service_name}...")
    payload = json.dumps({"json": {"id": primary_domain_id}})
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{EASYPANEL_URL}/trpc/databaseBackups.runDatabaseBackup"
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            print(f"          [SUCCESS] DB: {service_name} backup triggered.")
        else:
            print(f"          [FAILED] DB: {service_name} trigger status {response.status_code}.")
    except Exception as e:
        print(f"          [ERROR] DB: Request failed for {service_name}: {e}")

def run_service_backup(primary_domain_id, service_name):
    """
    Triggers a manual general service backup.
    """
    print(f"          --> APP: Triggering backup for {service_name}...")
    payload = json.dumps({"json": {"id": primary_domain_id}})
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{EASYPANEL_URL}/trpc/serviceBackups.runServiceBackup"
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            print(f"          [SUCCESS] APP: {service_name} backup triggered.")
        else:
            print(f"          [FAILED] APP: {service_name} trigger status {response.status_code}.")
    except Exception as e:
        print(f"          [ERROR] APP: Request failed for {service_name}: {e}")

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
                service_name = service['name']
                print(f"      --> Checking backups for: {service_name}...")
                
                # Check for Database Backups
                db_backups = list_database_backups(project, service_name)
                found_backups = False
                
                if db_backups:
                    try:
                        db_list = db_backups['result']['data']['json']
                        for backup in db_list:
                            run_database_backup(backup['id'], service_name)
                            backups_triggered += 1
                            found_backups = True
                    except:
                        pass
                
                # Check for Service (App) Backups
                app_backups = list_service_backups(project, service_name)
                if app_backups:
                    try:
                        app_list = app_backups['result']['data']['json']
                        for backup in app_list:
                            run_service_backup(backup['id'], service_name)
                            backups_triggered += 1
                            found_backups = True
                    except:
                        pass
                
                if not found_backups:
                    print(f"      [INFO] No backup configurations found for {service_name} (in either DB or App).")
                        
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
    print("EASYPANEL BACKUP SERVICE INITIALIZED (DB + APP)")
    print(f"Scheduled daily at: {BACKUP_TIME}")
    print(f"Targeting projects: {', '.join(EASYPANEL_PROJECTS)}")
    print("!"*60 + "\n")
    
    # Run once at startup to verify configuration (optional)
    # perform_backup_routine() 

    schedule.every().day.at(BACKUP_TIME).do(perform_backup_routine)

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()