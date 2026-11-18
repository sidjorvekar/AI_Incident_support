from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route('/')

def dashboard():

    with open("incidents/incidents.json", "r") as f:
        incidents = json.load(f)

    return render_template(
        "dashboard.html",
        incidents=incidents
    )

app.run(host='0.0.0.0', port=5000)
