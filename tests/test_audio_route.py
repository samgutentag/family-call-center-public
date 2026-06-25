import os


def test_serves_audio_public(client):
    import config
    os.makedirs(config.Config.AUDIO_DIR, exist_ok=True)
    with open(os.path.join(config.Config.AUDIO_DIR, "abc123.mp3"), "wb") as f:
        f.write(b"ID3audio")
    # public: works over BOTH a tailnet host and the funnel host
    r1 = client.get("/audio/abc123.mp3", headers={"Host": "pi.tailtest.ts.net"})
    r2 = client.get("/audio/abc123.mp3", headers={"Host": "funnel.example.ts.net"})
    assert r1.status_code == 200 and r1.data == b"ID3audio"
    assert r2.status_code == 200 and r2.data == b"ID3audio"
    os.remove(os.path.join(config.Config.AUDIO_DIR, "abc123.mp3"))


def test_audio_route_blocks_traversal(client):
    resp = client.get("/audio/../config.py")
    assert resp.status_code in (403, 404)
