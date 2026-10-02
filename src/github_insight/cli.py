"""Console entry point installed by the package."""

import uvicorn


def main() -> None:
    uvicorn.run("github_insight.main:app", host="127.0.0.1", port=8000, reload=False)
