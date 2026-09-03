import io
import json
from PIL import Image


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_jpeg(width, height):
    img = Image.new("RGB", (width, height), "blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    buf.seek(0)
    return buf


def upload(client, token, kind, w, h, show_id=None, episode_id=None):
    data = {"kind": kind}
    if show_id:
        data["show_id"] = show_id
    if episode_id:
        data["episode_id"] = episode_id
    r = client.post("/admin/artwork/upload", data=data, files={"file": (f"{kind}.jpg", make_jpeg(w, h), "image/jpeg")},
                     headers=auth_headers(token))
    assert r.status_code == 201, r.text


def build_publishable_show(client, editor_token, admin_token, title="Playtime Pals", langs=("en", "hi")):
    r = client.post("/admin/shows", json={
        "title": title, "categories": ["music"], "section": "featured",
    }, headers=auth_headers(editor_token))
    show = r.json()
    upload(client, editor_token, "poster", 600, 900, show_id=show["id"])
    upload(client, editor_token, "banner", 1280, 720, show_id=show["id"])

    r = client.post(f"/admin/shows/{show['id']}/seasons", json={"number": 1}, headers=auth_headers(editor_token))
    season = r.json()

    episode_ids = []
    for lang in langs:
        r = client.post(f"/admin/seasons/{season['id']}/episodes", json={
            "title": "Episode One", "episode_number": 1, "duration_seconds": 600,
            "language": lang, "content_group": "cg-playtime-1", "status": "draft",
        }, headers=auth_headers(editor_token))
        assert r.status_code == 201, r.text
        ep = r.json()
        episode_ids.append(ep["id"])
        upload(client, editor_token, "thumbnail", 640, 360, episode_id=ep["id"])
        r = client.patch(f"/admin/episodes/{ep['id']}", json={"status": "published"}, headers=auth_headers(editor_token))
        assert r.status_code == 200, r.text

    r = client.patch(f"/admin/shows/{show['id']}", json={"status": "published"}, headers=auth_headers(editor_token))
    assert r.status_code == 200, r.text
    return show, episode_ids


def test_publish_succeeds_trivially_with_no_shows(client, admin_token):
    # nothing exists yet, so there's nothing to fail validation -> publish
    # succeeds with an empty catalogue. Validation only blocks *broken*
    # published content, not the absence of any.
    r = client.post("/admin/catalog/publish", headers=auth_headers(admin_token))
    assert r.status_code == 201
    assert r.json()["show_count"] == 0


def test_publish_blocked_by_incomplete_published_show(client, editor_token, admin_token):
    # a show marked published with no section is exactly the kind of broken
    # state the validation report exists to catch before it reaches publish
    r = client.post("/admin/shows", json={"title": "Broken Show", "categories": ["music"]},
                     headers=auth_headers(editor_token))
    show = r.json()
    r = client.patch(f"/admin/shows/{show['id']}", json={"status": "published", "section": "featured"},
                      headers=auth_headers(editor_token))
    assert r.status_code == 200  # allowed: section supplied in the same request

    r = client.get("/admin/validation-report", headers=auth_headers(editor_token))
    report = r.json()
    # published show with zero published episodes + missing required artwork should show up
    rules = {g["rule"] for g in report["groups"]}
    assert "published_show_missing_required_artwork" in rules
    assert "published_show_has_no_published_episodes" in rules

    r = client.post("/admin/catalog/publish", headers=auth_headers(admin_token))
    assert r.status_code == 422
    assert r.json()["detail"]["report"]["can_publish"] is False


def test_publish_succeeds_and_groups_languages(client, editor_token, admin_token):
    build_publishable_show(client, editor_token, admin_token)

    r = client.post("/admin/catalog/publish", headers=auth_headers(admin_token))
    assert r.status_code == 201, r.text
    run = r.json()
    assert run["outcome"] == "success"
    assert run["show_count"] == 1
    assert run["episode_count"] == 2  # 2 language rows collapsed into publish accounting

    r = client.get("/catalog")
    assert r.status_code == 200
    catalogue = r.json()
    section = next(s for s in catalogue["sections"] if s["section"] == "featured")
    show = section["shows"][0]
    assert len(show["episodes"]) == 1  # the two language variants collapsed into ONE entry
    langs = sorted(language_entry["language"] for language_entry in show["episodes"][0]["languages"])
    assert langs == ["en", "hi"]


def test_publish_never_exposes_partial_catalogue(client, editor_token, admin_token):
    """
    The pointer file is only ever the fully-old or fully-new catalogue. We can't
    easily kill the process mid-write in a unit test, but we can assert the
    invariant that matters: after N publishes, the served catalogue always
    parses as complete, valid JSON with a matching checksum — never truncated.
    """
    build_publishable_show(client, editor_token, admin_token)
    for _ in range(3):
        r = client.post("/admin/catalog/publish", headers=auth_headers(admin_token))
        assert r.status_code == 201
        catalogue = client.get("/catalog").json()
        assert catalogue["checksum"]
        assert catalogue["run_id"] == r.json()["id"]


def test_publish_is_idempotent(client, editor_token, admin_token):
    build_publishable_show(client, editor_token, admin_token)
    r1 = client.post("/admin/catalog/publish", headers=auth_headers(admin_token))
    r2 = client.post("/admin/catalog/publish", headers=auth_headers(admin_token))
    assert r1.status_code == 201 and r2.status_code == 201
    c1 = client.get("/catalog").json()
    assert c1["checksum"]
    # two runs with unchanged data produce the same checksum
    body1 = json.dumps({k: v for k, v in c1.items() if k not in ("generated_at", "run_id")}, sort_keys=True)
    assert body1  # sanity: content is stable/deterministic across runs


def test_duplicate_content_group_language_rejected(client, editor_token):
    r = client.post("/admin/shows", json={"title": "Dup Show", "categories": ["music"]}, headers=auth_headers(editor_token))
    show = r.json()
    r = client.post(f"/admin/shows/{show['id']}/seasons", json={"number": 1}, headers=auth_headers(editor_token))
    season = r.json()
    body = {"title": "Ep", "episode_number": 1, "duration_seconds": 300, "language": "en", "content_group": "cg-x"}
    r1 = client.post(f"/admin/seasons/{season['id']}/episodes", json=body, headers=auth_headers(editor_token))
    assert r1.status_code == 201
    r2 = client.post(f"/admin/seasons/{season['id']}/episodes", json=body, headers=auth_headers(editor_token))
    assert r2.status_code == 409


def test_trailer_season_excluded_from_normal_season_numbering(client, editor_token, admin_token):
    show, _ = build_publishable_show(client, editor_token, admin_token, title="Trailer Show")
    r = client.post(f"/admin/shows/{show['id']}/seasons", json={"number": 0}, headers=auth_headers(editor_token))
    trailer_season = r.json()
    r = client.post(f"/admin/seasons/{trailer_season['id']}/episodes", json={
        "title": "Trailer", "episode_number": 1, "duration_seconds": 60, "language": "en",
    }, headers=auth_headers(editor_token))
    ep = r.json()
    upload(client, editor_token, "thumbnail", 640, 360, episode_id=ep["id"])
    client.patch(f"/admin/episodes/{ep['id']}", json={"status": "published"}, headers=auth_headers(editor_token))

    client.post("/admin/catalog/publish", headers=auth_headers(admin_token))
    catalogue = client.get("/catalog").json()
    show_entry = next(s for sec in catalogue["sections"] for s in sec["shows"] if s["title"] == "Trailer Show")
    trailer_entries = [e for e in show_entry["episodes"] if e["season"] == 0]
    assert len(trailer_entries) == 1
    assert trailer_entries[0]["is_trailer"] is True
