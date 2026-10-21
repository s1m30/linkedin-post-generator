import os
import sys
import uuid
import unittest.mock as mock
import pytest
from fastapi.testclient import TestClient

# Ensure the backend directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
# Bare import (no "app." prefix): app/main.py appends the app/ directory to
# sys.path as a side effect of the import above, and all of the app's own
# internal modules import `database.session` (and everything else) that same
# bare way. Importing it as `app.database.session` instead would load a
# second, separate copy of the module with its own empty Base.metadata, so
# drop_all/create_all below would silently operate on zero tables.
from database.session import Base, engine
from modules.auth.dependencies import get_current_user
from modules.auth.models import Profile

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    # Setup clean sqlite database before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_style_templates_flow():
    # 1. Assert initially empty
    res = client.get("/api/style-templates")
    assert res.status_code == 200
    assert res.json() == []

    # 2. Create template
    res = client.post("/api/style-templates", json={
        "name": "Professional Tech",
        "content": "This is sample content for style testing."
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Professional Tech"
    assert data["content"] == "This is sample content for style testing."
    assert "id" in data
    template_id = data["id"]

    # 3. Verify it's in the list
    res = client.get("/api/style-templates")
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == template_id

    # 4. Delete the template
    res = client.delete(f"/api/style-templates/{template_id}")
    assert res.status_code == 200
    assert res.json() == {"detail": "Style template deleted successfully"}

    # 5. Assert list is empty again
    res = client.get("/api/style-templates")
    assert res.json() == []

def test_posts_flow():
    # Patch the AI engine generate & refine methods to run tests without requiring API key
    with mock.patch("app.modules.posts.service.ai_engine.generate") as mock_generate, \
         mock.patch("app.modules.posts.service.ai_engine.refine") as mock_refine:
         
        mock_generate.return_value = "This is a mocked high-converting LinkedIn post about clean code."
        mock_refine.return_value = "This is a mocked refined LinkedIn post that is shorter."

        # 1. Assert initially empty history
        res = client.get("/api/posts")
        assert res.status_code == 200
        assert res.json() == []

        # 2. Create style template to link
        res_tpl = client.post("/api/style-templates", json={
            "name": "My Style",
            "content": "Write like a software leader."
        })
        tpl_id = res_tpl.json()["id"]

        # 3. Create & generate post
        payload = {
            "title": "3 Writing Rules",
            "type": "post",
            "rough_draft": "1. Think first, 2. Keep it simple, 3. Surgical changes.",
            "additional_context": "Notes from a team retro that aren't published anywhere.",
            "web_sources": ["https://example.com/rule1"],
            "style_template_id": tpl_id
        }
        res = client.post("/api/posts", json=payload)
        assert res.status_code == 201
        post_data = res.json()
        assert post_data["title"] == "3 Writing Rules"
        assert post_data["status"] == "draft"
        assert post_data["content"] == "This is a mocked high-converting LinkedIn post about clean code."
        assert post_data["web_sources"] == ["https://example.com/rule1"]
        assert post_data["additional_context"] == "Notes from a team retro that aren't published anywhere."
        post_id = post_data["id"]

        mock_generate.assert_called_once()
        generate_call_args = mock_generate.call_args[0]
        assert "Notes from a team retro that aren't published anywhere." in generate_call_args[1]

        # 4. Refine post
        res_refine = client.post(f"/api/posts/{post_id}/refine", json={
            "instruction": "make it shorter"
        })
        assert res_refine.status_code == 200
        assert res_refine.json()["content"] == "This is a mocked refined LinkedIn post that is shorter."
        mock_refine.assert_called_once()

        # 5. Delete post
        res_del = client.delete(f"/api/posts/{post_id}")
        assert res_del.status_code == 200

        # Verify history is empty
        res = client.get("/api/posts")
        assert res.json() == []

        # Clean up the style template created in step 2
        client.delete(f"/api/style-templates/{tpl_id}")

def test_assist_mode_flow():
    # Patch the AI engine so the test runs without requiring API keys
    with mock.patch("app.modules.posts.service.ai_engine.generate") as mock_generate:
        assist_json = (
            '{"fact_check": [{"claim": "X", "verdict": "unverified", "note": "no sources", "source": null}], '
            '"structured_draft": "Hook.\\n\\nBody.", '
            '"suggestions": [{"type": "add", "detail": "Add an example"}], '
            '"template": "[Hook]\\n\\n[Body]"}'
        )
        mock_generate.return_value = assist_json

        # 1. Create an assist-mode draft; it must NOT auto-generate content
        payload = {
            "title": "My Rough Idea",
            "type": "post",
            "mode": "assist",
            "rough_draft": "Some rough notes."
        }
        res = client.post("/api/posts", json=payload)
        assert res.status_code == 201
        post_data = res.json()
        assert post_data["mode"] == "assist"
        assert post_data["content"] is None
        assert post_data["assist_result"] is None
        mock_generate.assert_not_called()
        post_id = post_data["id"]

        # 2. Edit the draft in place via PATCH
        res_update = client.patch(f"/api/posts/{post_id}", json={"rough_draft": "Updated rough notes."})
        assert res_update.status_code == 200
        assert res_update.json()["rough_draft"] == "Updated rough notes."

        # 3. Run the assist pass and confirm it's advisory-only
        res_assist = client.post(f"/api/posts/{post_id}/assist")
        assert res_assist.status_code == 200
        assist_data = res_assist.json()
        assert assist_data["content"] is None
        assert assist_data["rough_draft"] == "Updated rough notes."
        assert assist_data["assist_result"]["structured_draft"] == "Hook.\n\nBody."
        assert assist_data["assist_result"]["suggestions"][0]["type"] == "add"
        mock_generate.assert_called_once()

        # 4. Clean up
        res_del = client.delete(f"/api/posts/{post_id}")
        assert res_del.status_code == 200

def test_posts_are_isolated_per_user():
    # Post created as the default test user (see conftest.py's dependency override)
    res = client.post("/api/posts", json={"title": "User A's post", "type": "post", "mode": "assist"})
    assert res.status_code == 201
    user_a_post_id = res.json()["id"]

    # Switch the authenticated identity to a second, unrelated user
    original_override = app.dependency_overrides[get_current_user]
    other_user = Profile(id=uuid.uuid4(), email="other@example.com", is_approved=True)
    app.dependency_overrides[get_current_user] = lambda: other_user
    try:
        # User B's history must not include User A's post
        res = client.get("/api/posts")
        assert res.status_code == 200
        assert all(p["id"] != user_a_post_id for p in res.json())

        # User B can't fetch, update, or delete User A's post by ID either
        assert client.get(f"/api/posts/{user_a_post_id}").status_code == 404
        assert client.patch(f"/api/posts/{user_a_post_id}", json={"title": "hijacked"}).status_code == 404
        assert client.delete(f"/api/posts/{user_a_post_id}").status_code == 404

        # User B creates their own post
        res = client.post("/api/posts", json={"title": "User B's post", "type": "post", "mode": "assist"})
        assert res.status_code == 201
        user_b_post_id = res.json()["id"]
    finally:
        # Restore the default test-user override for subsequent tests
        app.dependency_overrides[get_current_user] = original_override

    # Back to User A: their history should show only their own post
    res = client.get("/api/posts")
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert user_a_post_id in ids
    assert user_b_post_id not in ids

    # Clean up
    client.delete(f"/api/posts/{user_a_post_id}")
