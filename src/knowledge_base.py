import os
import uuid
from dataclasses import dataclass
from typing import List
from loguru import logger

@dataclass
class BusinessRule:
    rule_id: str
    codebase_id: str
    rule_type: str
    title: str
    description: str
    source_file: str
    line_numbers: tuple
    code_snippet: str
    confidence: float

class KnowledgeBaseManager:
    def __init__(self):
        self.rules = []
        logger.info("KnowledgeBaseManager initialized (in-memory mode)")

    async def store_findings(self, result: dict):
        findings = result.get("findings", {})
        rules = findings.get("business_rules", [])
        for r in rules:
            rule = BusinessRule(
                rule_id=str(uuid.uuid4()),
                codebase_id="local-project",
                rule_type=r.get("rule_type", "unknown"),
                title=r.get("title", "Untitled Rule"),
                description=r.get("description", ""),
                source_file=result["file_path"],
                line_numbers=(r.get("line_start", 0), r.get("line_end", 0)),
                code_snippet=r.get("code_snippet", "")[:500],
                confidence=r.get("confidence", 0.8)
            )
            self.rules.append(rule)
            logger.info(f"Stored rule: {rule.title} ({rule.rule_type}) from {rule.source_file}")

    def get_summary(self):
        print(f"\nTOTAL BUSINESS RULES EXTRACTED: {len(self.rules)}")
        for r in self.rules[:10]:
            print(f" • [{r.rule_type.upper()}] {r.title} → {r.source_file}")
        if len(self.rules) > 10:
            print(f" ... and {len(self.rules)-10} more")
