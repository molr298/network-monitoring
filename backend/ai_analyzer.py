import json
import os
import google.generativeai as genai

class AIAnalyzer:
    def __init__(self, api_key):
        if api_key:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
            self.model = genai.GenerativeModel(model_name)
        else:
            self.model = None

    def analyze_alert(self, alert_data):
        if not self.model:
            return {
                "analysis": "AI analysis is not configured.",
                "recommendation": "Please provide a Google AI API key to enable this feature.",
                "error": True
            }

        try:
            prompt = self._build_prompt(alert_data)
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            return {
                "analysis": f"An error occurred during AI analysis: {str(e)}",
                "recommendation": "Check the backend logs and ensure the Google AI API key is valid and has access.",
                "error": True
            }

    def _build_prompt(self, alert):
        host_name = alert.get('host', 'Unknown Host')
        description = alert.get('description', 'No description')
        severity = alert.get('severity', 'Not classified')

        return f"""
        As an expert Site Reliability Engineer (SRE), analyze the following Zabbix alert and provide a detailed, actionable response in a structured format.

        **Alert Details:**
        - **Host:** {host_name}
        - **Problem:** {description}
        - **Severity:** {severity}

        **Instructions:**
        1.  **Analysis:** Briefly explain what this alert means in a practical context.
        2.  **Potential Root Causes:** List the most likely root causes for this issue, ordered from most to least probable.
        3.  **Recommended Actions:** Provide a clear, step-by-step troubleshooting plan. The steps should be concrete and easy for a junior engineer to follow.

        **Output Format (Strictly follow this):**
        [ANALYSIS]
        <Your analysis here>

        [ROOT_CAUSES]
        1. <Cause 1>
        2. <Cause 2>
        3. <Cause 3>

        [RECOMMENDATIONS]
        1. <Step 1>
        2. <Step 2>
        3. <Step 3>

        [REMEDIATION]
        {{ "action": "script", "script_id": "<script_id_if_applicable>" }} // or null if no safe action
        """

    def _parse_response(self, text):
        analysis = text.split('[ANALYSIS]')[-1].split('[ROOT_CAUSES]')[0].strip()
        root_causes_text = text.split('[ROOT_CAUSES]')[-1].split('[RECOMMENDATIONS]')[0].strip()
        recommendations_text = text.split('[RECOMMENDATIONS]')[-1].split('[REMEDIATION]')[0].strip()
        remediation_text = text.split('[REMEDIATION]')[-1].strip()

        root_causes = [line.strip() for line in root_causes_text.split('\n') if line.strip()]
        recommendations = [line.strip() for line in recommendations_text.split('\n') if line.strip()]
        
        remediation = None
        try:
            # The remediation block might contain non-JSON text, so we extract the JSON part.
            json_start = remediation_text.find('{')
            json_end = remediation_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                remediation = json.loads(remediation_text[json_start:json_end])
        except (json.JSONDecodeError, IndexError):
            remediation = None # Could not parse

        return {
            "analysis": analysis,
            "root_causes": root_causes,
            "recommendations": recommendations,
            "remediation": remediation
        }
