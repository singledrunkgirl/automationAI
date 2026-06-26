from tools.burpsuite_integration import BurpSuiteAPI, BurpSuiteAgentTools
import json, os
class BurpSuiteAgent:
    def __init__(self, api_url="http://127.0.0.1:1337", api_key=""):
        self.burp = BurpSuiteAPI(api_url, api_key)
        self.tools = BurpSuiteAgentTools(self.burp)
    def autonomous_scan(self, target_url, depth="standard"):
        quick = self.tools.quick_scan(target_url)
        deep = self.tools.deep_scan(target_url) if depth=="deep" else quick
        return {"target":target_url,"quick_scan":quick,"deep_scan":deep,"issues":deep.get("vulnerabilities",[])}
