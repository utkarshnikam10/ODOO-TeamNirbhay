import uuid
from fastapi.testclient import TestClient


def _random_suffix() -> str:
    return uuid.uuid4().hex[:6]


def test_registration_success(client: TestClient) -> None:
    """Test successful user registration returns 201 and never exposes password hash."""
    uid = _random_suffix()
    payload = {
        "email": f"sarah_{uid}@stocksense.io",
        "username": f"sarah_{uid}",
        "password": "StrongPassword123!",
        "full_name": "Sarah Connor",
        "role": "manager",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == f"sarah_{uid}@stocksense.io"
    assert data["username"] == f"sarah_{uid}"
    assert data["role"] == "manager"
    assert data["is_active"] is True
    assert "id" in data

    # Requirement 6: Never return password hashes
    assert "password" not in data
    assert "hashed_password" not in data


def test_registration_duplicate_email(client: TestClient) -> None:
    """Test duplicate email registration is rejected with 409 Conflict."""
    uid = _random_suffix()
    payload = {
        "email": f"dup_{uid}@stocksense.io",
        "username": f"user_one_{uid}",
        "password": "Password123!",
    }
    # Register first user
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt to register second user with same email
    payload_dup = {
        "email": f"dup_{uid}@stocksense.io",
        "username": f"user_two_{uid}",
        "password": "Password456!",
    }
    res2 = client.post("/auth/register", json=payload_dup)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_login_success(client: TestClient) -> None:
    """Test user login returns valid JWT bearer token."""
    uid = _random_suffix()
    email = f"john_{uid}@stocksense.io"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "username": f"john_{uid}",
            "password": "LoginSecret123!",
        },
    )

    # Login
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "LoginSecret123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_invalid_password(client: TestClient) -> None:
    """Test login with incorrect password returns 401 Unauthorized."""
    uid = _random_suffix()
    email = f"alice_{uid}@stocksense.io"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "username": f"alice_{uid}",
            "password": "CorrectPassword123!",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_protected_endpoint_without_token(client: TestClient) -> None:
    """Test accessing protected GET /auth/me without token returns 401 Unauthorized."""
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert "validate credentials" in response.json()["detail"].lower()


def test_protected_endpoint_invalid_token(client: TestClient) -> None:
    """Test accessing protected route with malformed token returns 401 Unauthorized."""
    headers = {"Authorization": "Bearer completely.invalid.jwt.token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert "validate credentials" in response.json()["detail"].lower()


def test_protected_endpoint_success(client: TestClient) -> None:
    """Test authenticated user can access GET /auth/me profile."""
    uid = _random_suffix()
    email = f"bob_{uid}@stocksense.io"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "username": f"bob_{uid}",
            "password": "BobPassword123!",
            "full_name": "Bob Me",
        },
    )
    login_res = client.post(
        "/auth/login",
        json={"email": email, "password": "BobPassword123!"},
    )
    token = login_res.json()["access_token"]

    # Access /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == email
    assert data["username"] == f"bob_{uid}"
    assert data["full_name"] == "Bob Me"
    assert "password" not in data
    assert "hashed_password" not in data


def test_forgot_and_reset_password_flow(client: TestClient) -> None:
    """Test full OTP password reset architecture."""
    uid = _random_suffix()
    email = f"reset_{uid}@stocksense.io"

    # 1. Register
    client.post(
        "/auth/register",
        json={
            "email": email,
            "username": f"reset_{uid}",
            "password": "InitialPassword123!",
        },
    )

    # 2. Forgot password request
    forgot_res = client.post(
        "/auth/forgot-password",
        json={"email": email},
    )
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.json()
    otp_code = forgot_data.get("otp_code")
    assert otp_code is not None

    # 3. Reset password using OTP
    reset_res = client.post(
        "/auth/reset-password",
        json={
            "email": email,
            "otp_code": otp_code,
            "new_password": "NewUpdatedPassword456!",
        },
    )
    assert reset_res.status_code == 200
    assert "successfully reset" in reset_res.json()["message"].lower()

    # 4. Old password should now fail
    old_login = client.post(
        "/auth/login",
        json={"email": email, "password": "InitialPassword123!"},
    )
    assert old_login.status_code == 401

    # 5. New password should succeed
    new_login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "NewUpdatedPassword456!",
        },
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()


def test_reset_password_invalid_otp(client: TestClient) -> None:
    """Test password reset with invalid OTP code returns 400 Bad Request."""
    uid = _random_suffix()
    email = f"wrong_{uid}@stocksense.io"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "username": f"wrong_{uid}",
            "password": "InitialPassword123!",
        },
    )
    client.post("/auth/forgot-password", json={"email": email})

    response = client.post(
        "/auth/reset-password",
        json={
            "email": email,
            "otp_code": "000000",
            "new_password": "AnotherPassword123!",
        },
    )
    assert response.status_code == 400
    assert "invalid or expired" in response.json()["detail"].lower()
