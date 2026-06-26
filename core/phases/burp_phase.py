from core.burp_agent import BurpSuiteAgent
import json, os
class BurpAttackPhase:
    def __init__(self): self.agent = BurpSuiteAgent()
    def execute(self, target_url, depth="standard"):
        result = self.agent.autonomous_scan(target_url, depth)
        issues = result.get("issues",[])
        return {"phase":"burpsuite","target":target_url,"found":len(issues),"critical":len([i for i in issues if i.get("severity")=="critical"]),"high":len([i for i in issues if i.get("severity")=="high"])}
