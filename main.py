import requests
import json
import urllib.parse

# Esse script executa as ações de backups para banco de dados na versão free limitada do Easypanel.

EASYPANEL_URL="https://easypanel.host.com.br/api"
EASYPANEL_TOKEN="token"
EASYPANEL_PROJECTS=['workspance1','workspance2','workspance3']

def projectsInspectProject(projectName):
    input_json = json.dumps({"json": {"projectName": projectName}})
    input_encoded = urllib.parse.quote(input_json)
    url = f"{EASYPANEL_URL}/trpc/projects.inspectProject?input={input_encoded}"
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    

def listDatabaseBackups(projectName, serviceName):
    input_json = json.dumps({"json": {"projectName": projectName,"serviceName":serviceName}})
    input_encoded = urllib.parse.quote(input_json)
    url = f"{EASYPANEL_URL}/trpc/databaseBackups.listDatabaseBackups?input={input_encoded}"
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def runDatabaseBackup(primaryDomainId):
    payload = json.dumps({
        "json": {
            "id": primaryDomainId
        }
    })
        
    headers = {
        "Authorization": f"Bearer {EASYPANEL_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"{EASYPANEL_URL}/trpc/databaseBackups.runDatabaseBackup"
    requests.post(url, headers=headers, data=payload)
    


for project in EASYPANEL_PROJECTS:
    result = projectsInspectProject(project)
    if result==None:
        continue
    
    for service in result['result']['data']['json']['services']:
        try:
            # Recuperando os backups. 
            backups=listDatabaseBackups(service['projectName'],service['name'])
            if len(backups['result']['data']['json']) == 0:
                continue
            
            for  backup in backups['result']['data']['json'] :
                # Executa os backups.
                runDatabaseBackup(backup['id'])
                
        except KeyError:
            pass
        
        