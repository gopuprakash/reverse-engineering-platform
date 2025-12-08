import os
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv
from loguru import logger
import psycopg2
from psycopg2.extras import execute_values

from src.config import settings

load_dotenv()

@dataclass
class BusinessRule:
    rule_id: str
    run_id: str
    rule_type: str
    title: str
    description: str
    source_file: str
    line_numbers: tuple
    code_snippet: str
    confidence: float

class KnowledgeBaseManager:
    def __init__(self, project_id="local-project", project_name="Local Analysis Project"):
        self.conn = psycopg2.connect(
            dbname=settings.kb_db_name,
            user=settings.kb_db_user,
            password=os.getenv("DB_PASSWORD"),
            host=settings.kb_db_host,
            port=settings.kb_db_port
        )

        # Load Parameterized Project Info
        self.project_id = settings.project_id
        self.project_name = settings.project_name
        
        # Identifiers
        self.run_id = str(uuid.uuid4())
        self.run_timestamp = datetime.now()

        # Initialize and Register
        self._init_db()
        self._register_run()
        
        logger.info(f"KB Session: {self.run_id} | Project: {self.project_id} ({self.project_name})")

    def _init_db(self):
        with self.conn.cursor() as cur:
            # 1. projects (Renamed from 'codebases' to avoid conflict with old DB schema)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. analysis_runs (Tracks history of executions)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    run_id UUID PRIMARY KEY,
                    project_id TEXT REFERENCES projects(id),
                    executed_at TIMESTAMP,
                    status TEXT
                );
            """)

            # 3. business_rules (The actual extracted logic)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS business_rules (
                    rule_id UUID PRIMARY KEY,
                    run_id UUID REFERENCES analysis_runs(run_id),
                    rule_type TEXT,
                    title TEXT,
                    description TEXT,
                    source_file TEXT,
                    line_start INT,
                    line_end INT,
                    code_snippet TEXT,
                    confidence FLOAT
                );
            """)
            
            # Ensure Project Exists
            cur.execute("""
                INSERT INTO projects (id, name) 
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, (self.project_id, self.project_name))
            
            self.conn.commit()

    def _register_run(self):
        """Log the start of this specific analysis run."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO analysis_runs (run_id, project_id, executed_at, status)
                VALUES (%s, %s, %s, 'IN_PROGRESS')
            """, (self.run_id, self.project_id, self.run_timestamp))
            self.conn.commit()

    async def store_findings(self, result: dict):
        findings = result.get("findings", {})
        rules = findings.get("business_rules", [])
        
        if not rules:
            return

        data_to_insert = []
        for r in rules:
            data_to_insert.append((
                str(uuid.uuid4()),
                self.run_id,  # Links to the RUN, not the project
                r.get("rule_type", "unknown"),
                r.get("title", "Untitled"),
                r.get("description", ""),
                result["file_path"],
                r.get("line_start", 0),
                r.get("line_end", 0),
                r.get("code_snippet", "")[:1000], # Increased limit slightly
                r.get("confidence", 0.8)
            ))

        with self.conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO business_rules 
                (rule_id, run_id, rule_type, title, description, source_file, line_start, line_end, code_snippet, confidence)
                VALUES %s
            """, data_to_insert)
            self.conn.commit()
        
        logger.info(f"Saved {len(rules)} rules for Run {self.run_id}")

    def get_summary(self):
        print(f"\n--- SUMMARY FOR RUN: {self.run_id} ---")
        print(f"Time: {self.run_timestamp}")
        
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM business_rules WHERE run_id = %s", (self.run_id,))
            count = cur.fetchone()[0]
            print(f"Rules Extracted: {count}")
            
            cur.execute("""
                SELECT rule_type, title, source_file 
                FROM business_rules 
                WHERE run_id = %s 
                LIMIT 5
            """, (self.run_id,))
            
            rows = cur.fetchall()
            for row in rows:
                print(f" • {row[1]} ({row[2]})")