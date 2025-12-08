# src/prompts.py
from jinja2 import Environment, FileSystemLoader
from src.config import settings

# Initialize Jinja2 environment pointing to the prompts directory
env = Environment(loader=FileSystemLoader(settings.prompts_dir))

def render_prompt(name: str, **context) -> str:
    """
    Renders a Jinja2 prompt template.
    
    Args:
        name: The name of the template file (without .j2 extension)
        **context: Variables to pass to the template (e.g., code, language, project_structure)
    """
    template = env.get_template(f"{name}.j2")
    return template.render(**context)