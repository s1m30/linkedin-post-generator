import os
import sys

# Point the app at a disposable, path-independent test database *before* any
# app module (which reads DATABASE_URL at import time) gets imported. Without
# this, a relative sqlite path resolves against whatever directory pytest is
# invoked from, which can collide with a real on-disk database instead of a
# dedicated test one.
_TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".test_linkedin_gen.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
import pytest
from fastapi import Depends

from app.main import app
# Bare imports (no "app." prefix) are intentional here: app/main.py appends
# the app/ directory to sys.path as a side effect of the import above, and
# every module the running app actually uses imports `database.session`,
# `modules.auth.*` etc. that same bare way. Importing these as `app.X`
# instead would load second, separate copies of the modules - e.g. a second
# Profile class fighting the first over the same "profiles" table name on
# two different (and differently populated) Base.metadata objects.
from database.session import get_db
from modules.auth.dependencies import get_current_user
from modules.auth.models import Profile

# Fixed fake identity for tests: bypasses real Supabase JWT verification so the
# suite doesn't need live Supabase credentials. Lazily (re)created per test
# since the DB is dropped/recreated between tests.
TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_USER_EMAIL = "test@example.com"


def _fake_current_user(db=Depends(get_db)) -> Profile:
    profile = db.query(Profile).filter(Profile.id == TEST_USER_ID).first()
    if not profile:
        profile = Profile(id=TEST_USER_ID, email=TEST_USER_EMAIL, is_approved=True)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


app.dependency_overrides[get_current_user] = _fake_current_user


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db():
    yield
    # Dispose pooled connections first; on Windows the sqlite file can't be
    # removed while the engine still holds an open handle to it. Best-effort:
    # if something still has it locked, it's a throwaway file and the next
    # session's drop_all/create_all will reset it anyway.
    from database.session import engine
    engine.dispose()
    try:
        if os.path.exists(_TEST_DB_PATH):
            os.remove(_TEST_DB_PATH)
    except PermissionError:
        pass
