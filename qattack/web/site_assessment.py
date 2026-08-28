
"""
Safe Website Security Assessment.

Performs bounded, non-destructive assessment against an authorized
website target.

Current checks
--------------
- HTTPS usage
- HTTP status
- Final URL after bounded redirects
- TLS version
- TLS negotiated cipher
- TLS certificate subject
- TLS certificate issuer
- TLS certificate validity
- TLS certificate public-key algorithm
- TLS certificate public-key size / parameters
- TLS certificate signature algorithm
- Cryptographic inventory
- Quantum-risk classification
- Security headers
- Cookies
- Page title
- HTML forms
- Password inputs
- Script count
- Link count

Safety
------
This module does NOT:

- exploit vulnerabilities
- bypass authentication
- brute-force credentials
- submit destructive payloads
- modify target data
- perform unbounded crawling

The implementation includes:

- URL validation
- private/local IP rejection
- bounded response size
- timeout limits
- redirect limits
- public-certificate-only inspection
"""

from __future__ import annotations

import ipaddress
import re
import socket
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from html import unescape
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import (
    dsa,
    ec,
    ed25519,
    ed448,
    rsa,
)

from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)

from qattack.web.crypto_inventory import (
    build_crypto_inventory,
)

from qattack.web.quantum_risk import (
    risk_from_inventory,
)


# =====================================================================
# CONSTANTS
# =====================================================================

DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_MAX_REDIRECTS = 3

USER_AGENT = (
    "QuantumSecurityAssessment/0.3 "
    "(authorized-security-assessment)"
)

SECURITY_HEADERS = {
    "strict-transport-security": "HSTS",
    "content-security-policy": "CSP",
    "x-frame-options": "X-Frame-Options",
    "x-content-type-options": "X-Content-Type-Options",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
}


# =====================================================================
# DATA MODEL
# =====================================================================


@dataclass(frozen=True)
class WebsiteAssessment:
    """Structured result of a website security assessment."""

    target_url: str
    final_url: str

    status_code: int
    content_type: str
    content_length: int

    title: str | None

    https: bool

    tls: dict[str, Any]

    crypto_inventory: dict[str, Any]

    quantum_risk: dict[str, Any]

    security_headers: dict[str, Any]

    cookies: dict[str, Any]

    page: dict[str, Any]

    warnings: list[str]

    errors: list[str]

    def summary(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "target_url": self.target_url,
            "final_url": self.final_url,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "content_length": self.content_length,
            "title": self.title,
            "https": self.https,
            "tls": self.tls,
            "crypto_inventory": self.crypto_inventory,
            "quantum_risk": self.quantum_risk,
            "security_headers": self.security_headers,
            "cookies": self.cookies,
            "page": self.page,
            "warnings": self.warnings,
            "errors": self.errors,
        }


# =====================================================================
# URL SAFETY
# =====================================================================


def _is_public_ip(value: str) -> bool:
    """Return True when an IP address is globally routable."""

    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False

    return (
        not address.is_private
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
    )


def _resolve_host_public(hostname: str) -> None:
    """
    Resolve a hostname and reject private/local destinations.

    This protects a public assessment service from basic SSRF targets.
    """

    if not hostname:
        raise ValueError(
            "Target URL must contain a hostname."
        )

    lowered = hostname.lower().rstrip(".")

    blocked_names = {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
    }

    if lowered in blocked_names:
        raise ValueError(
            "Localhost targets are not allowed."
        )

    try:
        literal = ipaddress.ip_address(lowered)
    except ValueError:
        literal = None

    if literal is not None:
        if not _is_public_ip(str(literal)):
            raise ValueError(
                "Private or local IP targets are not allowed."
            )

        return

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                lowered,
                None,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise ValueError(
            f"Unable to resolve target hostname: {hostname}"
        ) from exc

    if not addresses:
        raise ValueError(
            f"No addresses resolved for hostname: {hostname}"
        )

    blocked = [
        address
        for address in addresses
        if not _is_public_ip(address)
    ]

    if blocked:
        raise ValueError(
            "Target hostname resolves to a private/local address."
        )


def validate_target_url(
    target_url: str,
) -> str:
    """Validate and normalize an HTTP(S) target URL."""

    if not isinstance(target_url, str):
        raise TypeError(
            "target_url must be a string."
        )

    value = target_url.strip()

    if not value:
        raise ValueError(
            "target_url must not be empty."
        )

    parsed = urlparse(value)

    if parsed.scheme.lower() not in {
        "http",
        "https",
    }:
        raise ValueError(
            "Only http:// and https:// targets are supported."
        )

    if not parsed.hostname:
        raise ValueError(
            "Target URL must contain a hostname."
        )

    if parsed.username or parsed.password:
        raise ValueError(
            "Credentials in URLs are not allowed."
        )

    _resolve_host_public(
        parsed.hostname
    )

    if parsed.path == "":
        value = value.rstrip("/") + "/"

    return value


# =====================================================================
# REDIRECT CONTROL
# =====================================================================


class SafeRedirectHandler(
    HTTPRedirectHandler
):
    """
    Redirect handler with bounded and validated redirects.
    """

    def __init__(
        self,
        max_redirects: int,
    ) -> None:
        super().__init__()

        self.max_redirects = max_redirects
        self.count = 0

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> Request | None:

        self.count += 1

        if self.count > self.max_redirects:
            raise ValueError(
                "Maximum redirect limit exceeded."
            )

        validated = validate_target_url(
            urljoin(
                req.full_url,
                newurl,
            )
        )

        return super().redirect_request(
            req,
            fp,
            code,
            msg,
            headers,
            validated,
        )


# =====================================================================
# HTTP FETCH
# =====================================================================


def _read_response_body(
    response: Any,
    max_bytes: int,
) -> bytes:
    """Read at most max_bytes from the response."""

    chunks: list[bytes] = []
    total = 0

    while total < max_bytes:
        chunk = response.read(
            min(
                64 * 1024,
                max_bytes - total,
            )
        )

        if not chunk:
            break

        chunks.append(chunk)
        total += len(chunk)

    return b"".join(chunks)


def _fetch_page(
    target_url: str,
    timeout: int,
    max_bytes: int,
    max_redirects: int,
) -> tuple[
    int,
    str,
    Message,
    bytes,
]:
    """
    Fetch a target page with bounded resource usage.
    """

    handler = SafeRedirectHandler(
        max_redirects=max_redirects
    )

    opener = build_opener(
        handler
    )

    request = Request(
        target_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml;"
                "q=0.9,*/*;q=0.1"
            ),
            "Accept-Encoding": "identity",
        },
        method="GET",
    )

    try:
        response = opener.open(
            request,
            timeout=timeout,
        )

    except HTTPError as exc:
        body = _read_response_body(
            exc,
            max_bytes,
        )

        return (
            exc.code,
            exc.geturl(),
            exc.headers,
            body,
        )

    except URLError as exc:
        raise RuntimeError(
            f"Unable to reach target: {exc.reason}"
        ) from exc

    status = int(
        response.status
    )

    final_url = response.geturl()

    headers = response.headers

    body = _read_response_body(
        response,
        max_bytes,
    )

    return (
        status,
        final_url,
        headers,
        body,
    )


# =====================================================================
# CERTIFICATE HELPERS
# =====================================================================


def _certificate_name(
    value: Any,
) -> str | None:
    """Extract a certificate distinguished name."""

    if not value:
        return None

    parts: list[str] = []

    for group in value:
        for item in group:
            if (
                isinstance(item, tuple)
                and len(item) == 2
            ):
                key, val = item

                parts.append(
                    f"{key}={val}"
                )

    if not parts:
        return None

    return ", ".join(parts)


def _format_public_key(
    public_key: Any,
) -> dict[str, Any]:
    """
    Describe the certificate public key.

    Only public information is returned.
    """

    if isinstance(
        public_key,
        rsa.RSAPublicKey,
    ):
        return {
            "algorithm": "RSA",
            "key_size_bits": public_key.key_size,
            "quantum_vulnerable_class": True,
            "quantum_relevance": (
                "Shor-vulnerable public-key cryptography"
            ),
        }

    if isinstance(
        public_key,
        ec.EllipticCurvePublicKey,
    ):
        curve = public_key.curve

        return {
            "algorithm": "EC",
            "key_size_bits": public_key.key_size,
            "curve": curve.name,
            "quantum_vulnerable_class": True,
            "quantum_relevance": (
                "Shor-vulnerable elliptic-curve cryptography"
            ),
        }

    if isinstance(
        public_key,
        dsa.DSAPublicKey,
    ):
        return {
            "algorithm": "DSA",
            "key_size_bits": public_key.key_size,
            "quantum_vulnerable_class": True,
            "quantum_relevance": (
                "Shor-vulnerable public-key cryptography"
            ),
        }

    if isinstance(
        public_key,
        ed25519.Ed25519PublicKey,
    ):
        return {
            "algorithm": "Ed25519",
            "key_size_bits": None,
            "curve": "Ed25519",
            "quantum_vulnerable_class": True,
            "quantum_relevance": (
                "Quantum-vulnerable classical "
                "public-key signature primitive"
            ),
        }

    if isinstance(
        public_key,
        ed448.Ed448PublicKey,
    ):
        return {
            "algorithm": "Ed448",
            "key_size_bits": None,
            "curve": "Ed448",
            "quantum_vulnerable_class": True,
            "quantum_relevance": (
                "Quantum-vulnerable classical "
                "public-key signature primitive"
            ),
        }

    return {
        "algorithm": type(
            public_key
        ).__name__,
        "key_size_bits": getattr(
            public_key,
            "key_size",
            None,
        ),
        "curve": None,
        "quantum_vulnerable_class": None,
        "quantum_relevance": (
            "Unknown public-key primitive; "
            "requires further analysis"
        ),
    }


def inspect_certificate(
    tls_socket: ssl.SSLSocket,
) -> dict[str, Any]:
    """
    Inspect the peer certificate.

    Private key material is never accessed.
    """

    certificate_der = (
        tls_socket.getpeercert(
            binary_form=True
        )
    )

    certificate_info = (
        tls_socket.getpeercert()
    )

    if not certificate_der:
        return {
            "available": False,
            "subject": None,
            "issuer": None,
            "not_before": None,
            "not_after": None,
            "serial_number": None,
            "signature_algorithm": None,
            "public_key": None,
        }

    certificate = (
        x509.load_der_x509_certificate(
            certificate_der
        )
    )

    public_key = (
        certificate.public_key()
    )

    public_key_info = (
        _format_public_key(
            public_key
        )
    )

    signature_algorithm = None

    try:
        signature_hash = (
            certificate.signature_hash_algorithm
        )

        if signature_hash is not None:
            signature_algorithm = (
                signature_hash.name
            )

    except (ValueError, NotImplementedError):
        signature_algorithm = None

    not_before = None
    not_after = None

    try:
        not_before = (
            certificate.not_valid_before_utc.isoformat()
        )
    except AttributeError:
        try:
            not_before = (
                certificate.not_valid_before
                .replace(tzinfo=timezone.utc)
                .isoformat()
            )
        except Exception:
            not_before = None

    try:
        not_after = (
            certificate.not_valid_after_utc.isoformat()
        )
    except AttributeError:
        try:
            not_after = (
                certificate.not_valid_after
                .replace(tzinfo=timezone.utc)
                .isoformat()
            )
        except Exception:
            not_after = None

    return {
        "available": True,

        "subject": _certificate_name(
            certificate_info.get(
                "subject"
            )
        ),

        "issuer": _certificate_name(
            certificate_info.get(
                "issuer"
            )
        ),

        "not_before": not_before,

        "not_after": not_after,

        "serial_number": str(
            certificate.serial_number
        ),

        "signature_algorithm": (
            signature_algorithm
        ),

        "public_key": public_key_info,
    }


# =====================================================================
# TLS
# =====================================================================


def inspect_tls(
    target_url: str,
    timeout: int,
) -> dict[str, Any]:
    """
    Inspect TLS and certificate cryptography.
    """

    parsed = urlparse(
        target_url
    )

    if parsed.scheme.lower() != "https":
        return {
            "enabled": False,
            "version": None,
            "cipher": None,
            "cipher_protocol": None,
            "certificate": {
                "available": False,
            },
        }

    hostname = parsed.hostname

    if hostname is None:
        raise ValueError(
            "HTTPS target has no hostname."
        )

    port = parsed.port or 443

    context = ssl.create_default_context()

    with socket.create_connection(
        (hostname, port),
        timeout=timeout,
    ) as raw_socket:

        with context.wrap_socket(
            raw_socket,
            server_hostname=hostname,
        ) as tls_socket:

            cipher = (
                tls_socket.cipher()
            )

            certificate = (
                inspect_certificate(
                    tls_socket
                )
            )

            return {
                "enabled": True,

                "version": (
                    tls_socket.version()
                ),

                "cipher": (
                    cipher[0]
                    if cipher
                    else None
                ),

                "cipher_protocol": (
                    cipher[1]
                    if cipher
                    else None
                ),

                "certificate": certificate,
            }


# =====================================================================
# SECURITY HEADERS
# =====================================================================


def inspect_security_headers(
    headers: Message,
) -> dict[str, Any]:
    """Inspect important browser security headers."""

    normalized = {
        key.lower(): value
        for key, value in headers.items()
    }

    results: dict[str, Any] = {}

    present: list[str] = []
    missing: list[str] = []

    for header_name, display_name in (
        SECURITY_HEADERS.items()
    ):

        value = normalized.get(
            header_name
        )

        if value:
            present.append(
                display_name
            )

            results[display_name] = {
                "present": True,
                "value": value,
            }

        else:
            missing.append(
                display_name
            )

            results[display_name] = {
                "present": False,
                "value": None,
            }

    results["_summary"] = {
        "present_count": len(present),
        "missing_count": len(missing),
        "present": present,
        "missing": missing,
    }

    return results


# =====================================================================
# COOKIES
# =====================================================================


def inspect_cookies(
    headers: Message,
) -> dict[str, Any]:
    """Inspect Set-Cookie security attributes."""

    raw_cookies = headers.get_all(
        "Set-Cookie",
        [],
    )

    cookies: list[dict[str, Any]] = []

    for raw in raw_cookies:

        first_part = raw.split(
            ";",
            1,
        )[0]

        if "=" not in first_part:
            continue

        name = first_part.split(
            "=",
            1,
        )[0].strip()

        attributes = [
            part.strip().lower()
            for part in raw.split(";")
        ]

        cookies.append(
            {
                "name": name,

                "secure": (
                    "secure" in attributes
                ),

                "httponly": (
                    "httponly" in attributes
                ),

                "samesite": any(
                    item.startswith(
                        "samesite="
                    )
                    for item in attributes
                ),
            }
        )

    return {
        "count": len(cookies),
        "cookies": cookies,
    }


# =====================================================================
# HTML
# =====================================================================


def _decode_html(
    body: bytes,
    content_type: str,
) -> str:
    """Decode bounded HTML content."""

    charset = None

    match = re.search(
        r"charset=([^\s;]+)",
        content_type,
        flags=re.IGNORECASE,
    )

    if match:
        charset = (
            match.group(1)
            .strip("\"'")
        )

    candidates = [
        charset,
        "utf-8",
        "latin-1",
    ]

    for candidate in candidates:

        if not candidate:
            continue

        try:
            return body.decode(
                candidate,
                errors="replace",
            )
        except LookupError:
            continue

    return body.decode(
        "utf-8",
        errors="replace",
    )


def _extract_title(
    html_text: str,
) -> str | None:
    """Extract the HTML title."""

    match = re.search(
        r"<title[^>]*>(.*?)</title>",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return None

    title = re.sub(
        r"\s+",
        " ",
        match.group(1),
    ).strip()

    return unescape(title) or None


def inspect_page(
    body: bytes,
    content_type: str,
) -> dict[str, Any]:
    """Analyze bounded HTML page metadata."""

    content_type_lower = (
        content_type.lower()
    )

    if (
        "text/html"
        not in content_type_lower
        and "application/xhtml+xml"
        not in content_type_lower
    ):
        return {
            "html_analyzed": False,
            "title": None,
            "forms": 0,
            "password_inputs": 0,
            "scripts": 0,
            "links": 0,
        }

    html_text = _decode_html(
        body,
        content_type,
    )

    return {
        "html_analyzed": True,

        "title": _extract_title(
            html_text
        ),

        "forms": len(
            re.findall(
                r"<form\b",
                html_text,
                flags=re.IGNORECASE,
            )
        ),

        "password_inputs": len(
            re.findall(
                r'<input[^>]+type\s*=\s*["\']password',
                html_text,
                flags=re.IGNORECASE,
            )
        ),

        "scripts": len(
            re.findall(
                r"<script\b",
                html_text,
                flags=re.IGNORECASE,
            )
        ),

        "links": len(
            re.findall(
                r"<a\b",
                html_text,
                flags=re.IGNORECASE,
            )
        ),
    }


# =====================================================================
# MAIN ASSESSMENT
# =====================================================================


def assess_website(
    target_url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
) -> WebsiteAssessment:
    """
    Run a bounded passive assessment against an authorized site.
    """

    normalized_url = (
        validate_target_url(
            target_url
        )
    )

    if timeout <= 0:
        raise ValueError(
            "timeout must be positive."
        )

    if max_bytes <= 0:
        raise ValueError(
            "max_bytes must be positive."
        )

    if max_redirects < 0:
        raise ValueError(
            "max_redirects must be non-negative."
        )

    warnings: list[str] = []
    errors: list[str] = []

    # -------------------------------------------------------------
    # HTTP
    # -------------------------------------------------------------

    (
        status_code,
        final_url,
        headers,
        body,
    ) = _fetch_page(
        normalized_url,
        timeout,
        max_bytes,
        max_redirects,
    )

    content_type = headers.get(
        "Content-Type",
        "",
    )

    # -------------------------------------------------------------
    # TLS
    # -------------------------------------------------------------

    try:
        tls = inspect_tls(
            final_url,
            timeout,
        )

    except Exception as exc:
        tls = {
            "enabled": (
                urlparse(
                    final_url
                ).scheme.lower()
                == "https"
            ),
            "version": None,
            "cipher": None,
            "cipher_protocol": None,
            "certificate": {
                "available": False,
            },
        }

        warnings.append(
            f"TLS inspection failed: {exc}"
        )

    # -------------------------------------------------------------
    # Security headers
    # -------------------------------------------------------------

    security_headers = (
        inspect_security_headers(
            headers
        )
    )

    # -------------------------------------------------------------
    # Cookies
    # -------------------------------------------------------------

    cookies = inspect_cookies(
        headers
    )

    # -------------------------------------------------------------
    # Page analysis
    # -------------------------------------------------------------

    page = inspect_page(
        body,
        content_type,
    )

    # -------------------------------------------------------------
    # Transport status
    # -------------------------------------------------------------

    https_enabled = (
        urlparse(
            final_url
        ).scheme.lower()
        == "https"
    )

    if not https_enabled:
        warnings.append(
            "Final URL does not use HTTPS."
        )

    # -------------------------------------------------------------
    # HTTP status
    # -------------------------------------------------------------

    if status_code >= 400:
        warnings.append(
            f"Target returned HTTP status {status_code}."
        )

    # -------------------------------------------------------------
    # Security header warnings
    # -------------------------------------------------------------

    missing_headers = (
        security_headers[
            "_summary"
        ][
            "missing"
        ]
    )

    if missing_headers:
        warnings.append(
            "Missing security headers: "
            + ", ".join(
                missing_headers
            )
        )

    # -------------------------------------------------------------
    # Password field warning
    # -------------------------------------------------------------

    password_inputs = int(
        page.get(
            "password_inputs",
            0,
        )
    )

    if (
        password_inputs > 0
        and not https_enabled
    ):
        warnings.append(
            "Password input detected on "
            "a non-HTTPS page."
        )

    # -------------------------------------------------------------
    # Crypto inventory
    # -------------------------------------------------------------

    certificate = tls.get(
        "certificate",
        {},
    )

    crypto_inventory = (
        build_crypto_inventory(
            certificate
        )
    )

    # -------------------------------------------------------------
    # Quantum risk mapping
    # -------------------------------------------------------------

    quantum_risk = (
        risk_from_inventory(
            crypto_inventory
        )
    )

    # -------------------------------------------------------------
    # Quantum warning
    # -------------------------------------------------------------

    if (
        quantum_risk.get(
            "status"
        )
        == "not_post_quantum_secure"
    ):
        warnings.append(
            "Observed certificate public key "
            "belongs to a classical public-key "
            "cryptographic class that is not "
            "post-quantum secure."
        )

    # -------------------------------------------------------------
    # Certificate expiry warning
    # -------------------------------------------------------------

    days_until_expiry: int | None = None

    not_after = (
        certificate.get(
            "not_after"
        )
    )

    if not_after:

        try:
            expiry = datetime.fromisoformat(
                not_after.replace(
                    "Z",
                    "+00:00",
                )
            )

            days_until_expiry = (
                expiry
                - datetime.now(
                    timezone.utc
                )
            ).days

        except ValueError:
            days_until_expiry = None

    if (
        days_until_expiry is not None
        and days_until_expiry < 0
    ):
        warnings.append(
            "TLS certificate appears to be expired."
        )

    elif (
        days_until_expiry is not None
        and days_until_expiry <= 30
    ):
        warnings.append(
            "TLS certificate expires within 30 days."
        )

    title = page.get(
        "title"
    )

    # -------------------------------------------------------------
    # Build result
    # -------------------------------------------------------------

    return WebsiteAssessment(
        target_url=normalized_url,
        final_url=final_url,

        status_code=status_code,
        content_type=content_type,
        content_length=len(body),

        title=title,

        https=https_enabled,

        tls=tls,

        crypto_inventory=crypto_inventory,

        quantum_risk=quantum_risk,

        security_headers=security_headers,

        cookies=cookies,

        page=page,

        warnings=warnings,

        errors=errors,
    )


# =====================================================================
# EXPORTS
# =====================================================================

__all__ = [
    "WebsiteAssessment",
    "assess_website",
    "inspect_tls",
    "inspect_certificate",
    "inspect_security_headers",
    "inspect_cookies",
    "inspect_page",
    "validate_target_url",
]

