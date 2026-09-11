import shutil

import pytest


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    yield settings.MEDIA_ROOT
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
