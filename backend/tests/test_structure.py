"""Structure validation tests — bootstrap Steps 2–5.

Verifies backend layout and monorepo alignment. Requires the repo root to be visible
(one level above backend/). Docker Compose mounts the full monorepo at /workspace.
"""

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = BACKEND_ROOT / "app"
REPO_ROOT = BACKEND_ROOT.parent


def test_modular_monolith_directories_exist() -> None:
    for name in ("core", "modules", "shared"):
        assert (APP_ROOT / name).is_dir(), f"missing app/{name}/"


def test_core_wiring_files_exist() -> None:
    core = APP_ROOT / "core"
    for name in ("config.py", "database.py", "models.py", "security.py"):
        assert (core / name).is_file(), f"missing core/{name}"


def test_planned_feature_module_stubs_exist() -> None:
    modules = APP_ROOT / "modules"
    for name in ("auth", "statements", "analysis"):
        assert (modules / name / "README.md").is_file(), f"missing modules/{name}/README.md"


def test_alembic_is_configured() -> None:
    assert (BACKEND_ROOT / "alembic.ini").is_file()
    assert (BACKEND_ROOT / "alembic" / "env.py").is_file()
    assert (BACKEND_ROOT / "alembic" / "versions").is_dir()


def test_compose_and_env_example_exist() -> None:
    assert (REPO_ROOT / "docker-compose.yml").is_file()
    assert (REPO_ROOT / ".env.example").is_file()


def test_frontend_app_router_layout_exists() -> None:
    frontend = REPO_ROOT / "frontend"
    assert (frontend / "app" / "page.tsx").is_file()
    assert (frontend / "lib").is_dir()
    assert (frontend / "components").is_dir()
