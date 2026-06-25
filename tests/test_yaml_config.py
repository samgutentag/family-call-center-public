from app.utils.yaml_config import load_yaml


def test_loads_yaml(tmp_path):
    f = tmp_path / "x.yml"
    f.write_text("a: 1\nb:\n  - one\n  - two\n")
    data = load_yaml(str(f))
    assert data["a"] == 1
    assert data["b"] == ["one", "two"]


def test_missing_file_returns_none():
    assert load_yaml("/no/such/file.yml") is None
