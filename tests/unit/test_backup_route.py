import io
import json
import zipfile

from src.api.routes import backup


def _archive_names(content: bytes) -> set[str]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        return set(archive.namelist())


def test_safe_backup_excludes_credentials_and_login_state(monkeypatch, tmp_path):
    monkeypatch.setattr(backup, "BACKUP_ROOT", tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "app.sqlite3").write_text("db", encoding="utf-8")
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "criteria.txt").write_text("prompt", encoding="utf-8")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=secret", encoding="utf-8")
    (tmp_path / "xianyu_state.json").write_text("{}", encoding="utf-8")
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "account.json").write_text("{}", encoding="utf-8")

    names = _archive_names(backup._build_backup_bytes())

    assert "data/app.sqlite3" in names
    assert "prompts/criteria.txt" in names
    assert ".env" not in names
    assert "xianyu_state.json" not in names
    assert "state/account.json" not in names
    assert backup.BACKUP_INFO_NAME in names


def test_full_backup_and_legacy_metadata_are_valid_for_restore(monkeypatch, tmp_path):
    monkeypatch.setattr(backup, "BACKUP_ROOT", tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "app.sqlite3").write_text("db", encoding="utf-8")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=secret", encoding="utf-8")

    content = backup._build_backup_bytes(include_sensitive=True)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        members, metadata = backup._validate_archive(archive)
    assert ".env" in members
    assert metadata["backup_type"] == "full"

    legacy = io.BytesIO()
    with zipfile.ZipFile(legacy, "w") as archive:
        archive.writestr("data/app.sqlite3", "db")
        archive.writestr(backup.LEGACY_BACKUP_INFO_NAME, "legacy")
    with zipfile.ZipFile(io.BytesIO(legacy.getvalue())) as archive:
        members, metadata = backup._validate_archive(archive)
    assert members == ["data/app.sqlite3"]
    assert metadata["format_version"] == 0
