# src/prompts.py
from jinja2 import Environment, FileSystemLoader
from src.config import settings

env = Environment(loader=FileSystemLoader(settings.prompts_dir))

def render_prompt(name: str, **context) -> str:
    template = env.get_template(f"{name}.j2")
    return template.render(**context)