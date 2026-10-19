import json
import os
from flask import Flask, render_template

app = Flask(__name__)

def read_json(f):
    try:
        if os.path.exists(f) and os.path.getsize(f) > 0:
            with open(f, "r", encoding="utf-8") as file:
                return json.load(file)
    except Exception:
        pass
    return {}

@app.route("/")
def index():
    return render_template(
        "index.html",
        status=read_json("status.json"),
        events=read_json("events.json"),
        ai=read_json("ai_decision.json"),
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)