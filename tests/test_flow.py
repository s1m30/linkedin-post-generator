import os
import sys
import unittest.mock as mock
import pytest
from fastapi.testclient import TestClient

# Ensure the backend directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database.session import Base, engine

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
        post_id = post_data["id"]

        mock_generate.assert_called_once()

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
