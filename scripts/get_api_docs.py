import os

import yaml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from myunla.app import app


def dump_api_docs(app: FastAPI, path: str):
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            openapi_schema, f, allow_unicode=True, default_flow_style=False
        )


if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    dump_api_docs(app, "docs/api_docs.yaml")
