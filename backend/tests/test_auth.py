def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_no_token_is_401(client):
    r = client.get("/admin/shows")
    assert r.status_code == 401


def test_editor_cannot_publish(client, editor_token):
    r = client.post("/admin/catalog/publish", headers=auth_headers(editor_token))
    assert r.status_code == 403


def test_admin_can_reach_publish_gate(client, admin_token):
    # even with nothing published yet, admin should get past the role check
    # (422 = blocked by validation, not 403 = blocked by role)
    r = client.post("/admin/catalog/publish", headers=auth_headers(admin_token))
    assert r.status_code in (201, 422)


def test_editor_can_crud_shows(client, editor_token):
    r = client.post("/admin/shows", json={"title": "Test Show", "categories": ["music"]}, headers=auth_headers(editor_token))
    assert r.status_code == 201


def test_bad_token_is_401(client):
    r = client.get("/admin/shows", headers=auth_headers("not-a-real-token"))
    assert r.status_code == 401
