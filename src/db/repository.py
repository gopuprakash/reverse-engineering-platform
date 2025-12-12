from sqlalchemy.orm import Session
from sqlalchemy import select, text
from src.db.models import BusinessRule, FileDependency, CodeSummary, AnalysisRun, Project

class BusinessRuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def register_run(self, run_id: str, project_id: str):
        run = AnalysisRun(run_id=run_id, project_id=project_id, status="IN_PROGRESS")
        self.db.add(run)
        self.db.commit()

    def bulk_insert_rules(self, rules_data: list[dict], run_id: str):
        objects = []
        for r in rules_data:
            # Safe conversion of rule data to Model
            objects.append(BusinessRule(
                run_id=run_id,
                file_path=r.get("file_path", "unknown"),
                title=r.get("title", "Untitled"),
                description=r.get("description", ""),
                code_snippet=r.get("code_snippet", ""),
                # Handle embedding if you have it, else None
                embedding=r.get("embedding") 
            ))
        
        if objects:
            self.db.add_all(objects)
            self.db.commit()

    def get_all_rules(self, run_id: str):
        return self.db.query(BusinessRule).filter(BusinessRule.run_id == run_id).all()

class GraphRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_summary(self, file_path: str, summary: str, embedding=None):
        # Upsert logic (merge)
        obj = self.db.query(CodeSummary).filter_by(file_path=file_path).first()
        if not obj:
            obj = CodeSummary(file_path=file_path)
        
        obj.summary = summary
        if embedding:
            obj.embedding = embedding
            
        self.db.add(obj)
        self.db.commit()

    def add_dependency(self, source, target, type="import"):
        # Check if exists to avoid primary key violation on duplicates
        exists = self.db.query(FileDependency).filter_by(source_file=source, target_file=target).first()
        if not exists:
            edge = FileDependency(source_file=source, target_file=target, relation_type=type)
            self.db.add(edge)
            self.db.commit()

    def get_smart_context(self, current_file: str) -> str:
        """
        Fetches summaries of files that the current_file imports.
        """
        # Join FileDependency -> CodeSummary
        results = self.db.query(CodeSummary.summary)\
            .join(FileDependency, FileDependency.target_file == CodeSummary.file_path)\
            .filter(FileDependency.source_file == current_file)\
            .all()
        
        context_parts = ["### Explicit Dependencies (Graph)"]
        context_parts.extend([r[0] for r in results if r[0]])
        
        if len(context_parts) == 1:
            return "" # No context found
            
        return "\n\n".join(context_parts)

    def get_summaries_for_files(self, file_paths: list[str]):
        return self.db.query(CodeSummary).filter(CodeSummary.file_path.in_(file_paths)).all()

    def get_dependencies_for_files(self, file_paths: list[str]):
        # Get edges where the source is in the active file list
        return self.db.query(FileDependency).filter(FileDependency.source_file.in_(file_paths)).limit(200).all()