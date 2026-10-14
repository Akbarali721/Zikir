from pathlib import Path

import pytest

from app.main import create_app


REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_INDEX = REPO_ROOT / "frontend" / "dist" / "index.html"


def test_dist_index_uses_vite_assets():
    if not DIST_INDEX.is_file():
        pytest.skip("Avval: cd frontend && npm run build")
    html = DIST_INDEX.read_text(encoding="utf-8")
    assert "/assets/" in html
    assert 'id="app"' in html
    assert "profile.css" not in html


def test_create_app_serves_spa_when_dist_exists():
    if not DIST_INDEX.is_file():
        pytest.skip("Avval: npm run build")
    app = create_app()
    web_routes = [r for r in app.routes if getattr(r, "name", None) == "index"]
    assert len(web_routes) == 0
