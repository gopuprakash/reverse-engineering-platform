from src.db.config import SessionLocal
from src.db.models import AnalysisRun, Project

db = SessionLocal()
print("-" * 50)
print(f"{'Run ID':<40} | {'Status':<12} | {'Created At'}")
print("-" * 50)
for run in db.query(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(5):
    print(f"{str(run.run_id):<40} | {run.status:<12} | {run.created_at}")
print("-" * 50)
db.close()
