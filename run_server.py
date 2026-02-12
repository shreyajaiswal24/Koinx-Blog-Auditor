"""Launch the FastAPI server."""

import logging
import os
import sys

import uvicorn


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RENDER") is None  # no reload in production
    uvicorn.run("api.server:app", host="0.0.0.0", port=port, reload=reload)


if __name__ == "__main__":
    main()
