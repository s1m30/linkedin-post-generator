import jwt
from passlib.context import CryptContext

from core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_jwks_client = None

# Tolerance for small clock differences between this server and Supabase,
# which otherwise surface as "The token is not yet valid (iat)".
_CLOCK_SKEW_LEEWAY_SECONDS = 60


class InvalidTokenError(Exception):
    pass


def _get_jwks_client() -> "jwt.PyJWKClient":
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(settings.SUPABASE_JWKS_URL)
    return _jwks_client


def verify_supabase_jwt(token: str) -> dict:
    """
    Verifies a Supabase-issued access token and returns its claims
    (notably "sub" = the user's UUID, "email").
    Supports either a legacy shared HS256 secret or a JWKS endpoint for
    newer asymmetric-key Supabase projects, depending on which is configured.
    """
    try:
        # Pick the verification method from the token's own algorithm so a
        # config with both values set still works for either project type.
        alg = jwt.get_unverified_header(token).get("alg")
        if alg == "HS256":
            if not settings.SUPABASE_JWT_SECRET:
                raise InvalidTokenError("Token is HS256 but SUPABASE_JWT_SECRET is not configured")
            claims = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                leeway=_CLOCK_SKEW_LEEWAY_SECONDS,
            )
        elif alg in ("RS256", "ES256"):
            if not settings.SUPABASE_JWKS_URL:
                raise InvalidTokenError(f"Token is {alg} but SUPABASE_JWKS_URL is not configured")
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience="authenticated",
                leeway=_CLOCK_SKEW_LEEWAY_SECONDS,
            )
        else:
            raise InvalidTokenError(f"Unsupported token algorithm: {alg}")
    except jwt.PyJWTError as e:
        raise InvalidTokenError(str(e)) from e

    if not claims.get("sub") or not claims.get("email"):
        raise InvalidTokenError("Token missing required claims")
    return claims


def verify_passphrase(raw_passphrase: str) -> bool:
    if not settings.APP_PASSPHRASE_HASH:
        return False
    return _pwd_context.verify(raw_passphrase, settings.APP_PASSPHRASE_HASH)
