from pathlib import Path

import yaml
from fastapi.openapi.utils import get_openapi

from app.main import app


def main() -> None:
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    out_path = Path(__file__).resolve().parent.parent / "swagger.yaml"
    with out_path.open("w", encoding="utf-8") as f:
        yaml.dump(openapi_schema, f, allow_unicode=True, sort_keys=False)
    print(f"OpenAPI schema exported to {out_path}")


if __name__ == "__main__":
    main()
