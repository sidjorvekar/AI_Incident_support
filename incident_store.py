import json
import os

FILE = "incidents/incidents.json"

def save_incident(data):

    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump([], f)

    with open(FILE, "r") as f:
        incidents = json.load(f)

    incidents.append(data)

    with open(FILE, "w") as f:
        json.dump(incidents, f, indent=2)
