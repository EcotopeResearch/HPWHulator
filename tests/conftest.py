import os
import tempfile

import pytest



testNames = ["test_SmallSwing"]

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

