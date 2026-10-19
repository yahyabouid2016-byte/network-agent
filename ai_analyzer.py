import json
import subprocess

from groq import Groq


class AIAnalyzer:
    def __init__(self, api_key, model):
        self.client = Groq(api_key=api_key)
        self.model = model

    def analyze_issue(self, layer, issue, context=""):
        system_prompt = """You are a senior network engineer.
Analyze the issue and respond ONLY with a valid JSON object. No markdown.
Schema: {"root_cause": "...", "action": "restart_service|manual", "target": "...", "safe_to_auto": true/false, "confidence": 0.0, "message": "..."}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Layer: {layer}\nIssue: {issue}\nContext: {context}"},
                ],
                temperature=0.1,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1].replace("json", "").strip()
            return json.loads(content)
        except Exception as e:
            return {
                "root_cause": "AI failed",
                "action": "manual",
                "target": None,
                "safe_to_auto": False,
                "confidence": 0.0,
                "message": str(e),
            }


def get_recent_logs(service_name, lines=15):
    return subprocess.run(
        f"journalctl -u {service_name} -n {lines} --no-pager",
        shell=True, capture_output=True, text=True,
    ).stdout.strip()


def get_service_context(service_name):
    enabled = subprocess.run(
        f"systemctl is-enabled {service_name} 2>&1",
        shell=True, capture_output=True, text=True,
    ).stdout.strip()
    port = "N/A"
    if service_name == "dnsmasq":
        port = subprocess.run(
            "ss -ulnp | grep :53 || echo 'free'",
            shell=True, capture_output=True, text=True,
        ).stdout.strip()
    return f"Status: {enabled}\nPort usage: {port}\nLogs:\n{get_recent_logs(service_name)}"
