from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

# Mutable dict passed as Jinja2 global.
# Update SITE in place anywhere in the app — templates pick it up immediately.
SITE: dict = {"logo_path": None, "site_name": None}
templates.env.globals["site"] = SITE
