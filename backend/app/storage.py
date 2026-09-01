"""
Storage abstraction.

Everything above this file (artwork upload, publish job) talks to `Storage`
and never touches disk or S3 directly. Swapping local disk for Cloudflare R2
is: implement `write`/`read`/`exists`/`url_for`/`atomic_publish` against R2's
S3-compatible API and flip STORAGE_BACKEND=r2 in the env. Nothing else changes.
"""
from __future__ import annotations

import abc
import os
import shutil
from pathlib import Path

from app.config import get_settings

settings = get_settings()


class Storage(abc.ABC):
    @abc.abstractmethod
    def write_bytes(self, key: str, data: bytes) -> None: ...

    @abc.abstractmethod
    def read_bytes(self, key: str) -> bytes: ...

    @abc.abstractmethod
    def exists(self, key: str) -> bool: ...

    @abc.abstractmethod
    def url_for(self, key: str) -> str: ...

    @abc.abstractmethod
    def atomic_publish(self, run_key: str, pointer_key: str) -> None:
        """
        Make `run_key` (an already-fully-written, immutable object) become the
        thing `pointer_key` resolves to, as a single atomic step. See
        README "Part E" for why this is the crux of publish-safety.
        """
        ...


class LocalDiskStorage(Storage):
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = self.root / key
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def write_bytes(self, key: str, data: bytes) -> None:
        path = self._path(key)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)  # atomic on same filesystem

    def read_bytes(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def url_for(self, key: str) -> str:
        return f"{settings.storage_public_base_url}/{key}"

    def atomic_publish(self, run_key: str, pointer_key: str) -> None:
        # run_key was already written in full (write_bytes above uses tmp+rename,
        # so it's never partially written). We just need the pointer to flip in
        # one step. On POSIX, os.replace() on the same filesystem is atomic, so a
        # concurrent reader either sees the old pointer target or the new one —
        # never a half-copied file.
        src = self._path(run_key)
        dst = self._path(pointer_key)
        tmp_link = dst.with_suffix(dst.suffix + ".newpointer")
        shutil.copyfile(src, tmp_link)  # same content, new location
        os.replace(tmp_link, dst)


class R2Storage(Storage):
    """
    Cloudflare R2 (S3-compatible). Sketched, not wired into CI since it needs
    real credentials — see README for what changes vs LocalDiskStorage.
    """
    def __init__(self):
        import boto3  # local import: optional dependency, only needed in prod
        self.bucket = settings.r2_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
        )

    def write_bytes(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def read_bytes(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def url_for(self, key: str) -> str:
        return f"{settings.r2_public_base_url}/{key}"

    def atomic_publish(self, run_key: str, pointer_key: str) -> None:
        # S3/R2 has no rename; PUT-copy is the closest thing to atomic swap:
        # the object at pointer_key is replaced by a single PUT (copy), which
        # readers see as one atomic version change (R2 objects are immutable
        # per-version). No reader ever observes a partial object.
        self.client.copy_object(
            Bucket=self.bucket,
            CopySource={"Bucket": self.bucket, "Key": run_key},
            Key=pointer_key,
        )


_instance: Storage | None = None


def get_storage() -> Storage:
    global _instance
    if _instance is not None:
        return _instance
    if settings.storage_backend == "r2":
        _instance = R2Storage()
    else:
        _instance = LocalDiskStorage(settings.storage_local_path)
    return _instance
