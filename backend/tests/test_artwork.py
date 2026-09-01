import io
from PIL import Image


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_jpeg(width, height, quality=85):
    img = Image.new("RGB", (width, height), "red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return buf


def create_show(client, token):
    r = client.post("/admin/shows", json={"title": "Art Show", "categories": ["music"]}, headers=auth_headers(token))
    return r.json()["id"]


def test_correct_poster_is_accepted(client, editor_token):
    show_id = create_show(client, editor_token)
    f = make_jpeg(600, 900)
    r = client.post(
        "/admin/artwork/upload",
        data={"kind": "poster", "show_id": show_id},
        files={"file": ("poster.jpg", f, "image/jpeg")},
        headers=auth_headers(editor_token),
    )
    assert r.status_code == 201, r.text
    assert r.json()["width"] == 600


def test_wrong_aspect_ratio_is_rejected(client, editor_token):
    show_id = create_show(client, editor_token)
    f = make_jpeg(900, 900)  # square, poster needs 2:3
    r = client.post(
        "/admin/artwork/upload",
        data={"kind": "poster", "show_id": show_id},
        files={"file": ("poster.jpg", f, "image/jpeg")},
        headers=auth_headers(editor_token),
    )
    assert r.status_code == 422
    assert "aspect ratio" in r.json()["detail"].lower()


def test_oversized_file_is_rejected(client, editor_token):
    show_id = create_show(client, editor_token)
    # correct dimensions/ratio, but force size over the 200KB ceiling with low compression + noise
    import random
    img = Image.new("RGB", (1280, 720))
    pixels = img.load()
    for x in range(0, 1280, 2):
        for y in range(0, 720, 2):
            pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=100)
    buf.seek(0)
    assert len(buf.getvalue()) > 200 * 1024
    r = client.post(
        "/admin/artwork/upload",
        data={"kind": "banner", "show_id": show_id},
        files={"file": ("banner.jpg", buf, "image/jpeg")},
        headers=auth_headers(editor_token),
    )
    assert r.status_code == 422
    assert "KB" in r.json()["detail"]


def test_wrong_dimensions_far_off_target_rejected(client, editor_token):
    show_id = create_show(client, editor_token)
    f = make_jpeg(100, 150)  # right ratio (2:3) but way too small
    r = client.post(
        "/admin/artwork/upload",
        data={"kind": "poster", "show_id": show_id},
        files={"file": ("poster.jpg", f, "image/jpeg")},
        headers=auth_headers(editor_token),
    )
    assert r.status_code == 422
