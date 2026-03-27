import os
import requests
import json
import urllib.parse
import schedule
import time
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
EASYPANEL_URL = os.getenv("EASYPANEL_URL", "https://easypanel.host.com.br/api")
EASYPANEL_TOKEN = os.getenv("EASYPANEL_TOKEN", "")
EASYPANEL_PROJECTS = os.getenv("EASYPANEL_PROJECTS", "").split(",")
BACKUP_TIME = os.getenv("BACKUP_TIME", "00:00")
TIMEZONE = os.getenv("TIMEZONE", "UTC")
BACKUP_INTERVAL = os.getenv("BACKUP_INTERVAL", "daily").lower()
BACKUP_WEEKDAY = os.getenv("BACKUP_WEEKDAY", "monday").lower()

def str_to_bool(s):
    if not s: return True # Default to True if not set
    return str(s).lower() in ("true", "1", "yes", "on")

ENABLE_DB_BACKUPS = str_to_bool(os.getenv("ENABLE_DB_BACKUPS", "true"))
ENABLE_APP_BACKUPS = str_to_bool(os.getenv("ENABLE_APP_BACKUPS", "true"))

# Set system timezone for the process (Unix/Docker)
if hasattr(time, 'tzset'):
    os.environ['TZ'] = TIMEZONE
    time.tzset()
    print(f"INFO: System timezone set to {TIMEZONE}")
else:
    # On Windows, we will log the time in the target timezone manually
    print(f"WARNING: time.tzset() not available on this platform. {TIMEZONE} will be reflected in logs using pytz.")

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
    Uses the serviceBackups namespace.
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

def list_app_backups(project_name, service_name):
    """
    Lists backups for a general application service. 
    Uses the appBackups namespace (alternative in some versions).
    """
    input_json = json.dumps({"json": {"projectName": project_name, "serviceName": service_name}})
    input_encoded = urllib.parse.quote(input_json)
    url = f"{EASYPANEL_URL}/trpc/appBackups.listAppBackups?input={input_encoded}"
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
    print(f"          --> APP (serviceBackups): Triggering backup for {service_name}...")
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

def run_app_backup(primary_domain_id, service_name):
    """
    Triggers a manual general application backup (appBackups namespace).
    """
    print(f"          --> APP (appBackups): Triggering backup for {service_name}...")
    payload = json.dumps({"json": {"id": primary_domain_id}})
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{EASYPANEL_URL}/trpc/appBackups.runAppBackup"
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
    try:
        now_str = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"BACKUP ROUTINE STARTED - {now_str} ({TIMEZONE})")
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
            json_data = result['result']['data']['json']
            services = json_data.get('services', [])
            print(f"      [DEBUG] Found {len(services)} items in 'services' list.")
            print(f"      [DEBUG] Project object keys: {list(json_data.keys())}")
            
            for service in services:
                service_name = service['name']
                service_type = service.get('type', 'unknown')
                print(f"      --> [{service_type.upper()}] Checking service: {service_name}...")
                print(f"      --> Checking backups for: {service_name}...")
                
                # Check for Database Backups
                found_backups = False
                if ENABLE_DB_BACKUPS:
                    db_backups = list_database_backups(project, service_name)
                    if db_backups:
                        try:
                            db_list = db_backups['result']['data']['json']
                            if db_list:
                                for backup in db_list:
                                    run_database_backup(backup['id'], service_name)
                                    backups_triggered += 1
                                    found_backups = True
                            else:
                                print(f"      [INFO] No DB backup configurations for {service_name}.")
                        except Exception as e:
                            print(f"      [ERROR] Parsing DB backup list for {service_name}: {e}")
                else:
                    print(f"      [SKIP] DB backups are disabled in .env")
                
                # Check for Service (App) Backups
                if ENABLE_APP_BACKUPS:
                    # Try serviceBackups namespace first
                    app_backups = list_service_backups(project, service_name)
                    processed_app = False
                    
                    if app_backups:
                        try:
                            app_json = app_backups.get('result', {}).get('data', {}).get('json', [])
                            if isinstance(app_json, list):
                                app_list = app_json
                            elif isinstance(app_json, dict) and 'backups' in app_json:
                                app_list = app_json['backups']
                            else:
                                app_list = []

                            if app_list:
                                for backup in app_list:
                                    run_service_backup(backup['id'], service_name)
                                    backups_triggered += 1
                                    found_backups = True
                                    processed_app = True
                        except Exception as e:
                            print(f"      [DEBUG] Note: serviceBackups check for {service_name} reported: {e}")

                    # Fallback: Try appBackups namespace if serviceBackups didn't find anything
                    if not processed_app:
                        app_v2_backups = list_app_backups(project, service_name)
                        if app_v2_backups:
                            try:
                                app_json = app_v2_backups.get('result', {}).get('data', {}).get('json', [])
                                if isinstance(app_json, list):
                                    app_list = app_json
                                elif isinstance(app_json, dict) and 'backups' in app_json:
                                    app_list = app_json['backups']
                                else:
                                    app_list = []

                                if app_list:
                                    for backup in app_list:
                                        run_app_backup(backup['id'], service_name)
                                        backups_triggered += 1
                                        found_backups = True
                            except Exception as e:
                                print(f"      [DEBUG] Note: appBackups check for {service_name} reported: {e}")
                else:
                    print(f"      [SKIP] App/Service backups are disabled in .env")
                
                if not found_backups:
                    print(f"      [INFO] No backup configurations found for {service_name} (in either DB or App).")
                        
        except KeyError as e:
            print(f"  [ERROR] Error parsing service info for project {project}: {e}")
            pass

    print("\n" + "="*60)
    try:
        now_str = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"BACKUP ROUTINE FINISHED - {now_str} ({TIMEZONE})")
    print(f"Summary: {projects_processed} projects processed, {backups_triggered} backups triggered.")
    print("="*60 + "\n")

def main():
    """
    Main entry point of the script, schedules the backup routine.
    """
    print("\n" + "!"*60)
    print("EASYPANEL BACKUP SERVICE INITIALIZED (DB + APP)")
    print(f"Scheduled interval: {BACKUP_INTERVAL}")
    if BACKUP_INTERVAL == "weekly":
        print(f"Scheduled day: {BACKUP_WEEKDAY}")
    print(f"Scheduled time: {BACKUP_TIME}")
    print(f"Timezone: {TIMEZONE}")
    print(f"Enable DB Backups: {ENABLE_DB_BACKUPS}")
    print(f"Enable App Backups: {ENABLE_APP_BACKUPS}")
    print(f"Targeting projects: {', '.join(EASYPANEL_PROJECTS)}")
    print("!"*60 + "\n")
    
    # Run once at startup to verify configuration (optional)
    # perform_backup_routine() 

    # Choose scheduling strategy based on interval
    if BACKUP_INTERVAL == "daily":
        schedule.every().day.at(BACKUP_TIME).do(perform_backup_routine)
    elif BACKUP_INTERVAL == "weekly":
        if BACKUP_WEEKDAY == "monday":
            schedule.every().monday.at(BACKUP_TIME).do(perform_backup_routine)
        elif BACKUP_WEEKDAY == "tuesday":
            schedule.every().tuesday.at(BACKUP_TIME).do(perform_backup_routine)
        elif BACKUP_WEEKDAY == "wednesday":
            schedule.every().wednesday.at(BACKUP_TIME).do(perform_backup_routine)
        elif BACKUP_WEEKDAY == "thursday":
            schedule.every().thursday.at(BACKUP_TIME).do(perform_backup_routine)
        elif BACKUP_WEEKDAY == "friday":
            schedule.every().friday.at(BACKUP_TIME).do(perform_backup_routine)
        elif BACKUP_WEEKDAY == "saturday":
            schedule.every().saturday.at(BACKUP_TIME).do(perform_backup_routine)
        elif BACKUP_WEEKDAY == "sunday":
            schedule.every().sunday.at(BACKUP_TIME).do(perform_backup_routine)
        else:
            print(f"[WARNING] Invalid BACKUP_WEEKDAY: {BACKUP_WEEKDAY}. Defaulting to Monday.")
            schedule.every().monday.at(BACKUP_TIME).do(perform_backup_routine)
    else:
        print(f"[WARNING] Invalid BACKUP_INTERVAL: {BACKUP_INTERVAL}. Defaulting to Daily.")
        schedule.every().day.at(BACKUP_TIME).do(perform_backup_routine)

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()