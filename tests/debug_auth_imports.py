import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def log(msg):
    print(f"[DEBUG] {time.strftime('%H:%M:%S')} - {msg}")


def debug_imports():
    log("Starting import debug...")

    try:
        log("Importing src.modules.auth.domain.models...")
        from src.modules.auth.domain.models import UserCredentials, CurrentUser

        log("Success.")

        log("Importing src.modules.auth.infrastructure.config...")
        from src.modules.auth.infrastructure.config import AuthSettings

        log("Success.")

        log("Importing src.modules.auth.application.service...")
        from src.modules.auth.application.service import AuthService

        log("Success.")

        log("Importing src.modules.auth.application.oauth_service...")
        from src.modules.auth.application.oauth_service import OAuthService

        log("Success.")

        log("Importing src.modules.auth.application.roles...")
        from src.modules.auth.application.roles import enrich_user_from_db

        log("Success.")

        log("Importing src.modules.auth.api.dependencies...")
        from src.modules.auth.api.dependencies import get_auth_service

        log("Success.")

        log("Importing src.modules.auth.api.routes...")
        from src.modules.auth.api.routes import router as auth_router

        log("Success.")

        log("Importing src.modules.auth.api.oauth_routes...")
        from src.modules.auth.api.oauth_routes import router as oauth_router

        log("Success.")

        log("Importing src.main...")
        from src.main import app

        log("Success.")

    except Exception as e:
        log(f"FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_imports()
