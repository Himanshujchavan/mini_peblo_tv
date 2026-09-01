import io
from PIL import Image


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_jpeg(w, h):
    img = Image.new("RGB", (w, h), "green")
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
    client.post("/admin/artwork/upload", data=data, files={"file": (f"{kind}.jpg", make_jpeg(w, h), "image/jpeg")},
                headers=auth_headers(token))


def make_show(client, editor_token, admin_token, title, category, section, lang="en"):
    r = client.post("/admin/shows", json={"title": title, "categories": [category], "section": section},
                     headers=auth_headers(editor_token))
    show = r.json()
    upload(client, editor_token, "poster", 600, 900, show_id=show["id"])
    upload(client, editor_token, "banner", 1280, 720, show_id=show["id"])
    r = client.post(f"/admin/shows/{show['id']}/seasons", json={"number": 1}, headers=auth_headers(editor_token))
    season = r.json()
    r = client.post(f"/admin/seasons/{season['id']}/episodes", json={
        "title": f"{title} Ep 1", "episode_number": 1, "duration_seconds": 500, "language": lang,
    }, headers=auth_headers(editor_token))
    ep = r.json()
    upload(client, editor_token, "thumbnail", 640, 360, episode_id=ep["id"])
    client.patch(f"/admin/episodes/{ep['id']}", json={"status": "published"}, headers=auth_headers(editor_token))
    client.patch(f"/admin/shows/{show['id']}", json={"status": "published"}, headers=auth_headers(editor_token))
    return show


def test_filters_compose(client, editor_token, admin_token):
    make_show(client, editor_token, admin_token, "Rocket Rex", "adventure", "featured", lang="en")
    make_show(client, editor_token, admin_token, "Rocket Song", "music", "featured", lang="hi")
    make_show(client, editor_token, admin_token, "Calm Nights", "music", "series", lang="en")
    client.post("/admin/catalog/publish", headers=auth_headers(admin_token))

    r = client.get("/catalog/search", params={"q": "rocket"})
    titles = {s["title"] for s in r.json()["results"]}
    assert titles == {"Rocket Rex", "Rocket Song"}

    r = client.get("/catalog/search", params={"category": "music", "section": "series"})
    titles = {s["title"] for s in r.json()["results"]}
    assert titles == {"Calm Nights"}

    r = client.get("/catalog/search", params={"q": "rocket", "category": "music"})
    titles = {s["title"] for s in r.json()["results"]}
    assert titles == {"Rocket Song"}
