from jinja2 import Environment, FileSystemLoader
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template("digest_template.html")

def render_html_for_user(owner, tasks):
    if not tasks:
        return
    rendered = template.render(data=tasks)

    output_path = os.path.join(OUTPUT_DIR, f"{owner}_digest.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)
    print(f"✅ Rendered HTML for {owner}: {output_path}")
