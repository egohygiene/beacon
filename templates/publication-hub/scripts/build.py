#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate and render the versioned publication-hub contract with the stdlib."""

from __future__ import annotations

import argparse
import hashlib
import html
import ipaddress
import json
import os
import posixpath
import re
import shutil
import tempfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

SOURCE_CATALOG_SCHEMA = "beacon.publication-hub-source/v1"
SITE_SCHEMA = "beacon.publication-hub/v1"
SCHEMA_VERSION = "1.0.0"
OWNERSHIP_MARKER = ".beacon-publication-hub-owned"
OWNERSHIP_VALUE = "beacon.publication-hub/v1\n"
CHECKSUM_FILE = "SHA256SUMS"
CORE_ROUTES = {
    "": ("hub", "home", "index.html"),
    "downloads/": ("downloads", "downloads", "downloads/index.html"),
    "manifest.webmanifest": (
        "web-manifest",
        "web-manifest",
        "manifest.webmanifest",
    ),
    "site.json": ("catalog", "site-json", "site.json"),
    CHECKSUM_FILE: ("checksum", "sha256sums", CHECKSUM_FILE),
}
RESERVED_ROUTE_IDS = {record[1] for record in CORE_ROUTES.values()}
STATUSES = {"planned", "draft", "available", "superseded", "withdrawn"}
SITE_STAGES = {"draft", "published", "archived"}
THEMES = {"neutral", "egohygiene"}
PROFILE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCHEMA_PATH = PROFILE_ROOT / "contracts" / "publication-hub.schema.json"
PUBLIC_SCHEMA_PATH = PROFILE_ROOT / "contracts" / "publication-site.schema.json"
IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MEDIA_TYPE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*$"
)
TOKEN_NAME = re.compile(r"^--[a-z][a-z0-9-]*$")
SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9._~-]+$")
FULL_REVISION = re.compile(r"^[0-9a-f]{40}$")
IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
FORBIDDEN_PLANNED_FIELDS = {
    "artifacts",
    "identifiers",
    "manifest",
    "manifests",
    "published_at",
    "publication_date",
    "date_published",
    "release",
    "release_url",
    "version",
    "doi",
    "issue",
    "issue_number",
    "cover",
    "cover_url",
    "zenodo",
    "checksum",
    "sha256",
    "bytes",
    "preview",
    "provenance",
    "source",
}

THEME_TOKENS = {
    "neutral": {
        "--hub-background": "#f4f1ea",
        "--hub-surface": "#ffffff",
        "--hub-ink": "#191725",
        "--hub-muted": "#625f6d",
        "--hub-accent": "#176b66",
        "--hub-accent-ink": "#ffffff",
        "--hub-border": "#d8d2c7",
        "--hub-planned": "#755a13",
        "--hub-draft": "#7251a5",
        "--hub-available": "#176b66",
        "--hub-withdrawn": "#963c42",
        "--hub-radius": "1.25rem",
        "--hub-shadow": "0 1.25rem 3rem rgba(25, 23, 37, 0.10)",
    },
    "egohygiene": {
        "--hub-background": "#100c17",
        "--hub-surface": "#1d1727",
        "--hub-ink": "#f7f2ff",
        "--hub-muted": "#c9bdd9",
        "--hub-accent": "#8be4cf",
        "--hub-accent-ink": "#10221e",
        "--hub-border": "#49385d",
        "--hub-planned": "#f1c56e",
        "--hub-draft": "#c8a6ff",
        "--hub-available": "#8be4cf",
        "--hub-withdrawn": "#ff9da6",
        "--hub-radius": "1.5rem",
        "--hub-shadow": "0 1.5rem 4rem rgba(0, 0, 0, 0.34)",
    },
}


class ContractError(RuntimeError):
    """Raised when a source or staged publication contract is unsafe."""


class _DuplicateKeyError(ValueError):
    """Internal duplicate-key signal for strict JSON parsing."""


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object while rejecting duplicate keys."""
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
        _DuplicateKeyError,
    ) as error:
        raise ContractError(f"invalid JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ContractError(f"expected a JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    """Write canonical, stable, human-readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _schema_type_matches(value: Any, expected: str) -> bool:
    """Implement the JSON types used by the bundled 2020-12 schemas."""
    return {
        "array": lambda item: isinstance(item, list),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "null": lambda item: item is None,
        "number": lambda item: isinstance(item, (int, float))
        and not isinstance(item, bool),
        "object": lambda item: isinstance(item, dict),
        "string": lambda item: isinstance(item, str),
    }.get(expected, lambda _item: False)(value)


def _schema_ref(root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ContractError(f"schema uses unsupported external reference: {reference}")
    current: Any = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise ContractError(f"schema has unresolved reference: {reference}")
        current = current[token]
    if not isinstance(current, dict):
        raise ContractError(f"schema reference is not an object: {reference}")
    return current


def _schema_passes(value: Any, schema: dict[str, Any], root: dict[str, Any]) -> bool:
    try:
        _validate_schema_value(value, schema, root, "$")
    except ContractError:
        return False
    return True


def _validate_schema_value(
    value: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    field: str,
) -> None:
    """Validate the deliberately small JSON Schema subset used by this profile."""
    if "$ref" in schema:
        _validate_schema_value(value, _schema_ref(root, schema["$ref"]), root, field)
        return
    for subschema in schema.get("allOf", []):
        _validate_schema_value(value, subschema, root, field)
    if "anyOf" in schema:
        if not any(_schema_passes(value, subschema, root) for subschema in schema["anyOf"]):
            raise ContractError(f"{field} does not match any allowed schema shape")
    if "oneOf" in schema:
        matches = sum(
            _schema_passes(value, subschema, root) for subschema in schema["oneOf"]
        )
        if matches != 1:
            raise ContractError(f"{field} must match exactly one schema shape")
    if "not" in schema and _schema_passes(value, schema["not"], root):
        raise ContractError(f"{field} matches a forbidden schema shape")
    if "if" in schema and _schema_passes(value, schema["if"], root):
        if "then" in schema:
            _validate_schema_value(value, schema["then"], root, field)
    elif "else" in schema:
        _validate_schema_value(value, schema["else"], root, field)

    expected = schema.get("type")
    if expected is not None:
        expected_types = [expected] if isinstance(expected, str) else expected
        if not isinstance(expected_types, list) or not any(
            isinstance(item, str) and _schema_type_matches(value, item)
            for item in expected_types
        ):
            raise ContractError(f"{field} has the wrong JSON type")
    if "const" in schema and value != schema["const"]:
        raise ContractError(f"{field} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{field} is not one of the allowed values")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ContractError(f"{field} is shorter than the schema minimum")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, value) is None:
            raise ContractError(f"{field} does not match its schema pattern")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ContractError(f"{field} is below the schema minimum")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ContractError(f"{field} has too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ContractError(f"{field} has too many items")
        if schema.get("uniqueItems"):
            canonical = [
                json.dumps(item, sort_keys=True, allow_nan=False) for item in value
            ]
            if len(canonical) != len(set(canonical)):
                raise ContractError(f"{field} must contain unique items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema_value(item, item_schema, root, f"{field}[{index}]")
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise ContractError(f"{field} is missing schema keys: {', '.join(missing)}")
        property_names = schema.get("propertyNames")
        if isinstance(property_names, dict):
            for key in value:
                _validate_schema_value(key, property_names, root, f"{field} key")
        properties = schema.get("properties", {})
        for key, child in value.items():
            if key in properties:
                _validate_schema_value(child, properties[key], root, f"{field}.{key}")
            elif schema.get("additionalProperties") is False:
                raise ContractError(f"{field} has unsupported schema key: {key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                _validate_schema_value(
                    child, schema["additionalProperties"], root, f"{field}.{key}"
                )


def validate_schema_document(
    value: Any, schema_path: Path, field: str = "document"
) -> None:
    """Validate one value against a bundled, local-only JSON Schema document."""
    if schema_path.is_symlink():
        raise ContractError(f"schema cannot be a symlink: {schema_path}")
    schema = read_json(schema_path)
    _validate_schema_value(value, schema, schema, field)


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{field} must be an array")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_string(mapping: dict[str, Any], key: str, field: str) -> str | None:
    if key not in mapping:
        return None
    return _string(mapping[key], f"{field}.{key}")


def _identifier(value: Any, field: str) -> str:
    identifier = _string(value, field)
    if not IDENTIFIER.fullmatch(identifier):
        raise ContractError(f"{field} must be lowercase kebab-case")
    return identifier


def _validate_keys(
    mapping: dict[str, Any],
    *,
    required: set[str],
    optional: set[str],
    field: str,
) -> None:
    missing = sorted(required - mapping.keys())
    if missing:
        raise ContractError(f"{field} is missing required keys: {', '.join(missing)}")
    unknown = sorted(mapping.keys() - required - optional)
    if unknown:
        raise ContractError(f"{field} has unsupported keys: {', '.join(unknown)}")


def _extensions(value: Any, field: str) -> dict[str, Any]:
    extensions = _mapping(value, field)
    for key in extensions:
        _identifier(key, f"{field} key")
    return extensions


def _reject_reserved_extension_keys(
    value: Any, reserved: set[str], field: str
) -> None:
    """Prevent extension nesting from bypassing a lifecycle invariant."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in reserved:
                raise ContractError(f"{field} cannot carry reserved publication key {key}")
            _reject_reserved_extension_keys(child, reserved, f"{field}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_reserved_extension_keys(child, reserved, f"{field}[{index}]")


def normalize_base_url(value: Any, field: str) -> str:
    """Normalize one safe HTTPS base URL, preserving repository subpaths."""
    raw, parsed, hostname = validate_https_url(value, field)
    if parsed.query or parsed.fragment:
        raise ContractError(f"{field} cannot contain credentials, query, or fragment")
    if "\\" in parsed.path or "%2e" in parsed.path.lower() or "%2f" in parsed.path.lower():
        raise ContractError(f"{field} contains an ambiguous encoded path")
    segments = [segment for segment in parsed.path.split("/") if segment]
    if any(segment in {".", ".."} or not SAFE_SEGMENT.fullmatch(segment) for segment in segments):
        raise ContractError(f"{field} contains an unsafe path segment")
    path = "/" + "/".join(segments) if segments else "/"
    if not path.endswith("/"):
        path += "/"
    host = hostname
    return urlunsplit(("https", host, path, "", ""))


def validate_https_url(value: Any, field: str) -> tuple[str, Any, str]:
    """Validate an HTTPS URL targets a public DNS host on the standard port."""
    raw = _string(value, field)
    if any(
        character.isspace() or ord(character) < 32 or ord(character) == 127
        for character in raw
    ):
        raise ContractError(f"{field} cannot contain whitespace or control characters")
    try:
        parsed = urlsplit(raw)
        hostname_value = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ContractError(f"{field} is not a valid HTTPS URL") from error
    if parsed.scheme.lower() != "https" or not parsed.netloc or not hostname_value:
        raise ContractError(f"{field} must be an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise ContractError(f"{field} cannot contain credentials")
    if port not in {None, 443}:
        raise ContractError(f"{field} must use the standard HTTPS port")
    hostname = hostname_value.lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ContractError(f"{field} must use a public DNS hostname")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ContractError(f"{field} cannot use an IP literal")
    try:
        hostname.encode("ascii")
    except UnicodeEncodeError as error:
        raise ContractError(f"{field} hostname must be ASCII/punycode") from error
    labels = hostname.split(".")
    if (
        len(labels) < 2
        or len(hostname) > 253
        or any(
            len(label) > 63
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
            for label in labels
        )
    ):
        raise ContractError(f"{field} must use a valid public DNS hostname")
    return raw, parsed, hostname


def _route_segments(value: Any, field: str) -> list[str]:
    raw = _string(value, field)
    if raw.startswith("/") or "\\" in raw or "?" in raw or "#" in raw:
        raise ContractError(f"{field} must be a relative route")
    segments = [segment for segment in raw.strip("/").split("/") if segment]
    if not segments:
        raise ContractError(f"{field} cannot be the root route")
    for segment in segments:
        if (
            segment in {".", ".."}
            or "%2e" in segment.lower()
            or "%2f" in segment.lower()
            or not SAFE_SEGMENT.fullmatch(segment)
        ):
            raise ContractError(f"{field} contains an unsafe path segment")
    return segments


def normalize_page_route(value: Any, field: str) -> str:
    """Return a normalized directory route ending in a slash."""
    return "/".join(_route_segments(value, field)) + "/"


def normalize_file_route(value: Any, field: str) -> str:
    """Return a normalized file route without a trailing slash."""
    route = normalize_relative_file(value, field)
    if "." not in PurePosixPath(route).name:
        raise ContractError(f"{field} must include a file extension")
    return route


def normalize_relative_file(value: Any, field: str) -> str:
    """Return a safe relative file path, including extensionless control files."""
    raw = _string(value, field)
    if raw.endswith("/"):
        raise ContractError(f"{field} must name a file, not a directory")
    route = "/".join(_route_segments(raw, field))
    return route


def normalize_public_route(value: Any, field: str) -> str:
    """Normalize a public URL route that may identify a page or a file."""
    raw = _string(value, field)
    return (
        normalize_page_route(raw, field)
        if raw.endswith("/")
        else normalize_file_route(raw, field)
    )


def public_url(base_url: str | None, route: str) -> str | None:
    """Join a normalized safe route to a normalized base URL."""
    return None if base_url is None else urljoin(base_url, route)


def _safe_relative_source(value: Any, field: str) -> str:
    source = _string(value, field)
    path = PurePosixPath(source)
    if (
        path.is_absolute()
        or "\\" in source
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ContractError(f"{field} must be a normalized relative file path")
    return path.as_posix()


def resolve_source(project: Path, relative: str, field: str) -> Path:
    """Resolve a regular, non-empty project file without following symlinks."""
    current = project
    for segment in PurePosixPath(relative).parts:
        current = current / segment
        if current.is_symlink():
            raise ContractError(f"{field} cannot traverse a symlink: {relative}")
    try:
        resolved = current.resolve(strict=True)
    except OSError as error:
        raise ContractError(f"{field} does not exist: {relative}") from error
    if project != resolved and project not in resolved.parents:
        raise ContractError(f"{field} escapes the project: {relative}")
    if not resolved.is_file():
        raise ContractError(f"{field} must reference a regular file: {relative}")
    if resolved.stat().st_size <= 0:
        raise ContractError(f"{field} cannot reference an empty file: {relative}")
    return resolved


def _asset(
    value: Any,
    field: str,
    project: Path,
    output_route: str,
) -> dict[str, Any]:
    asset = _mapping(value, field)
    _validate_keys(
        asset,
        required={"source", "alt"},
        optional={"extensions"},
        field=field,
    )
    source = _safe_relative_source(asset["source"], f"{field}.source")
    suffix = PurePosixPath(source).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        raise ContractError(f"{field}.source must use a supported web image format")
    result = {
        "source": source,
        "source_path": resolve_source(project, source, f"{field}.source"),
        "alt": _string(asset["alt"], f"{field}.alt"),
        "route": f"{output_route}{suffix}",
    }
    if "extensions" in asset:
        result["extensions"] = _extensions(asset["extensions"], f"{field}.extensions")
    return result


def _copy_contract(value: Any, field: str, allowed: set[str]) -> dict[str, str]:
    copy = _mapping(value, field)
    unknown = sorted(copy.keys() - allowed)
    if unknown:
        raise ContractError(f"{field} has unsupported keys: {', '.join(unknown)}")
    return {key: _string(item, f"{field}.{key}") for key, item in copy.items()}


def _styles(value: Any, field: str, project: Path) -> dict[str, Any]:
    styles = _mapping(value, field)
    _validate_keys(
        styles,
        required=set(),
        optional={"tokens", "custom_css", "extensions"},
        field=field,
    )
    result: dict[str, Any] = {"tokens": {}}
    if "tokens" in styles:
        tokens = _mapping(styles["tokens"], f"{field}.tokens")
        for name, raw_value in tokens.items():
            if not TOKEN_NAME.fullmatch(name):
                raise ContractError(f"{field}.tokens has invalid custom property {name}")
            token = _string(raw_value, f"{field}.tokens.{name}")
            lowered = token.lower()
            if (
                len(token) > 200
                or any(character in token for character in ";{}<>\r\n")
                or "url(" in lowered
                or "@import" in lowered
                or "/*" in token
            ):
                raise ContractError(f"{field}.tokens.{name} contains unsafe CSS")
            result["tokens"][name] = token
    if "custom_css" in styles:
        source = _safe_relative_source(styles["custom_css"], f"{field}.custom_css")
        if PurePosixPath(source).suffix.lower() != ".css":
            raise ContractError(f"{field}.custom_css must reference a CSS file")
        result["custom_css"] = source
        result["custom_css_path"] = resolve_source(
            project, source, f"{field}.custom_css"
        )
    if "extensions" in styles:
        result["extensions"] = _extensions(
            styles["extensions"], f"{field}.extensions"
        )
    return result


def _resource(
    value: Any,
    field: str,
    project: Path,
    *,
    allow_aliases: bool,
) -> dict[str, Any]:
    resource = _mapping(value, field)
    optional = {"aliases", "extensions", "route"} if allow_aliases else {
        "extensions",
        "route",
    }
    _validate_keys(
        resource,
        required={"id", "label", "source", "path", "media_type"},
        optional=optional,
        field=field,
    )
    identifier = _identifier(resource["id"], f"{field}.id")
    source = _safe_relative_source(resource["source"], f"{field}.source")
    output_path = normalize_file_route(resource["path"], f"{field}.path")
    default_route = (
        output_path[: -len("index.html")]
        if output_path.endswith("/index.html")
        else output_path
    )
    result: dict[str, Any] = {
        "id": identifier,
        "label": _string(resource["label"], f"{field}.label"),
        "source": source,
        "source_path": resolve_source(project, source, f"{field}.source"),
        "path": output_path,
        "route": normalize_public_route(
            resource.get("route", default_route), f"{field}.route"
        ),
        "media_type": _string(resource["media_type"], f"{field}.media_type").lower(),
        "aliases": [],
    }
    allowed_routes = {output_path}
    if output_path.endswith("/index.html"):
        allowed_routes.add(output_path[: -len("index.html")])
    if result["route"] not in allowed_routes:
        raise ContractError(
            f"{field}.route must match path or its index-page directory route"
        )
    if not MEDIA_TYPE.fullmatch(result["media_type"]):
        raise ContractError(f"{field}.media_type is not a valid media type")
    if "aliases" in resource:
        aliases = _list(resource["aliases"], f"{field}.aliases")
        seen_aliases: set[str] = set()
        for index, alias_value in enumerate(aliases):
            alias = normalize_file_route(alias_value, f"{field}.aliases[{index}]")
            if "/" in alias:
                raise ContractError(f"{field}.aliases[{index}] must be a root alias")
            if alias in seen_aliases:
                raise ContractError(f"{field} repeats root alias {alias}")
            seen_aliases.add(alias)
        result["aliases"] = sorted(seen_aliases)
    if "extensions" in resource:
        result["extensions"] = _extensions(
            resource["extensions"], f"{field}.extensions"
        )
    return result


def _identifiers(value: Any, field: str) -> list[dict[str, str]]:
    identifiers = _list(value, field)
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw_identifier in enumerate(identifiers):
        item_field = f"{field}[{index}]"
        item = _mapping(raw_identifier, item_field)
        _validate_keys(
            item,
            required={"scheme", "value"},
            optional={"url"},
            field=item_field,
        )
        normalized = {
            "scheme": _identifier(item["scheme"], f"{item_field}.scheme"),
            "value": _string(item["value"], f"{item_field}.value"),
        }
        if "url" in item:
            url = _string(item["url"], f"{item_field}.url")
            validate_https_url(url, f"{item_field}.url")
            normalized["url"] = url
        identity = (normalized["scheme"], normalized["value"])
        if identity in seen:
            raise ContractError(f"{field} repeats {identity[0]}:{identity[1]}")
        seen.add(identity)
        result.append(normalized)
    return result


def _reference(value: Any, field: str) -> dict[str, str]:
    reference = _mapping(value, field)
    _validate_keys(
        reference,
        required={"label"},
        optional={"media_type", "resource_id", "url"},
        field=field,
    )
    if ("url" in reference) == ("resource_id" in reference):
        raise ContractError(f"{field} must declare exactly one of url or resource_id")
    result = {"label": _string(reference["label"], f"{field}.label")}
    if "url" in reference:
        url = _string(reference["url"], f"{field}.url")
        validate_https_url(url, f"{field}.url")
        result["url"] = url
    else:
        result["resource_id"] = _identifier(
            reference["resource_id"], f"{field}.resource_id"
        )
    if "media_type" in reference:
        media_type = _string(reference["media_type"], f"{field}.media_type").lower()
        if not MEDIA_TYPE.fullmatch(media_type):
            raise ContractError(f"{field}.media_type is not a valid media type")
        result["media_type"] = media_type
    return result


def _source_record(value: Any, field: str) -> dict[str, str]:
    source = _mapping(value, field)
    _validate_keys(
        source,
        required={"repository", "revision"},
        optional={"path"},
        field=field,
    )
    repository = _string(source["repository"], f"{field}.repository")
    validate_https_url(repository, f"{field}.repository")
    result = {
        "repository": repository,
        "revision": _string(source["revision"], f"{field}.revision"),
    }
    if "path" in source:
        result["path"] = _safe_relative_source(source["path"], f"{field}.path")
    return result


def _accessibility(value: Any, field: str) -> dict[str, Any]:
    accessibility = _mapping(value, field)
    _validate_keys(
        accessibility,
        required={"summary", "features"},
        optional={"conformance", "report_url"},
        field=field,
    )
    features = [
        _string(item, f"{field}.features[{index}]")
        for index, item in enumerate(_list(accessibility["features"], f"{field}.features"))
    ]
    if not features or len(features) != len(set(features)):
        raise ContractError(f"{field}.features must be non-empty and unique")
    result: dict[str, Any] = {
        "summary": _string(accessibility["summary"], f"{field}.summary"),
        "features": features,
    }
    if "conformance" in accessibility:
        result["conformance"] = _string(
            accessibility["conformance"], f"{field}.conformance"
        )
    if "report_url" in accessibility:
        result["report"] = _reference(
            {"label": "Accessibility report", "url": accessibility["report_url"]},
            f"{field}.report_url",
        )
    return result


class OutputRegistry:
    """Reject output collisions, including file/directory prefix collisions."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def add(self, path: str, owner: str) -> None:
        normalized = PurePosixPath(path).as_posix()
        if normalized.startswith("../") or normalized.startswith("/"):
            raise ContractError(f"unsafe planned output path: {path}")
        for existing, existing_owner in self.files.items():
            if (
                normalized == existing
                or normalized.startswith(existing + "/")
                or existing.startswith(normalized + "/")
            ):
                raise ContractError(
                    f"output collision between {owner} ({normalized}) and "
                    f"{existing_owner} ({existing})"
                )
        self.files[normalized] = owner


def load_catalog(
    project: Path,
    theme_override: str | None = None,
    source_revision_override: str | None = None,
    *,
    require_deployable_revision: bool = False,
) -> dict[str, Any]:
    """Load, normalize, and validate one project-owned source catalog."""
    project = project.resolve(strict=True)
    catalog_path = project / "publication-hub.json"
    if catalog_path.is_symlink():
        raise ContractError("publication-hub.json cannot be a symlink")
    catalog = read_json(catalog_path)
    validate_schema_document(catalog, SOURCE_SCHEMA_PATH, "catalog")
    _validate_keys(
        catalog,
        required={"schema", "schema_version", "site", "slots"},
        optional={"$schema", "extensions"},
        field="catalog",
    )
    if (
        catalog["schema"] != SOURCE_CATALOG_SCHEMA
        or catalog["schema_version"] != SCHEMA_VERSION
    ):
        raise ContractError(
            f"catalog must use {SOURCE_CATALOG_SCHEMA} and schema_version {SCHEMA_VERSION}"
        )
    if "extensions" in catalog:
        _extensions(catalog["extensions"], "catalog.extensions")

    raw_site = _mapping(catalog["site"], "site")
    _validate_keys(
        raw_site,
        required={
            "id",
            "title",
            "description",
            "language",
            "stage",
            "publisher",
            "canonical_base_url",
        },
        optional={
            "artwork",
            "brand",
            "copy",
            "extensions",
            "fallback_base_url",
            "repository",
            "revision",
            "styles",
            "theme",
        },
        field="site",
    )
    theme = theme_override or raw_site.get("theme", "neutral")
    if theme not in THEMES:
        raise ContractError(f"site.theme must be one of: {', '.join(sorted(THEMES))}")
    language = _string(raw_site["language"], "site.language")
    if not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", language):
        raise ContractError("site.language must be a valid language tag")
    canonical = normalize_base_url(raw_site["canonical_base_url"], "site.canonical_base_url")
    fallback = (
        normalize_base_url(raw_site["fallback_base_url"], "site.fallback_base_url")
        if raw_site.get("fallback_base_url") is not None
        else None
    )
    if fallback is not None and canonical == fallback:
        raise ContractError("canonical and fallback base URLs must be distinct")
    site: dict[str, Any] = {
        "id": _identifier(raw_site["id"], "site.id"),
        "title": _string(raw_site["title"], "site.title"),
        "description": _string(raw_site["description"], "site.description"),
        "language": language,
        "stage": _string(raw_site["stage"], "site.stage"),
        "publisher": _string(raw_site["publisher"], "site.publisher"),
        "canonical_base_url": canonical,
        "fallback_base_url": fallback,
        "theme": theme,
        "copy": {},
        "styles": {"tokens": {}},
    }
    if site["stage"] not in SITE_STAGES:
        raise ContractError(
            f"site.stage must be one of: {', '.join(sorted(SITE_STAGES))}"
        )
    for key in ("repository",):
        value = _optional_string(raw_site, key, "site")
        if value is not None:
            if key == "repository":
                validate_https_url(value, "site.repository")
            site[key] = value
    source_revision = (
        (source_revision_override or "").strip()
        or os.environ.get("SOURCE_REVISION", "").strip()
        or str(raw_site.get("revision", "")).strip()
        or "WORKING_TREE"
    )
    if source_revision != "WORKING_TREE" and not FULL_REVISION.fullmatch(source_revision):
        raise ContractError(
            "source revision must be WORKING_TREE or a full lowercase 40-character commit SHA"
        )
    site["revision"] = source_revision
    if "copy" in raw_site:
        site["copy"] = _copy_contract(
            raw_site["copy"],
            "site.copy",
            {
                "downloads_heading",
                "downloads_introduction",
                "eyebrow",
                "footer",
                "heading",
                "introduction",
            },
        )
    if "styles" in raw_site:
        site["styles"] = _styles(raw_site["styles"], "site.styles", project)
    if "brand" in raw_site:
        brand = _mapping(raw_site["brand"], "site.brand")
        _validate_keys(
            brand,
            required=set(),
            optional={"logo", "extensions"},
            field="site.brand",
        )
        site["brand"] = {}
        if "logo" in brand:
            site["brand"]["logo"] = _asset(
                brand["logo"], "site.brand.logo", project, "assets/brand/logo"
            )
        if "extensions" in brand:
            site["brand"]["extensions"] = _extensions(
                brand["extensions"], "site.brand.extensions"
            )
    if "artwork" in raw_site:
        site["artwork"] = _asset(
            raw_site["artwork"], "site.artwork", project, "assets/brand/artwork"
        )
    if "extensions" in raw_site:
        site["extensions"] = _extensions(raw_site["extensions"], "site.extensions")

    raw_slots = _list(catalog["slots"], "slots")
    slots: list[dict[str, Any]] = []
    slot_ids: set[str] = set()
    slot_routes: set[str] = set()
    for index, raw_slot_value in enumerate(raw_slots):
        field = f"slots[{index}]"
        raw_slot = _mapping(raw_slot_value, field)
        _validate_keys(
            raw_slot,
            required={"id", "kind", "title", "summary", "status"},
            optional={
                "artifacts",
                "accessibility",
                "artwork",
                "copy",
                "extensions",
                "identifiers",
                "landing",
                "manifests",
                "order",
                "preview",
                "provenance",
                "release",
                "route",
                "superseded_by",
                "source",
                "version",
                "visible",
                "withdrawal_notice",
            },
            field=field,
        )
        identifier = _identifier(raw_slot["id"], f"{field}.id")
        if identifier in RESERVED_ROUTE_IDS:
            raise ContractError(f"{field}.id is reserved by the public route contract")
        if identifier in slot_ids:
            raise ContractError(f"slots repeats id {identifier}")
        slot_ids.add(identifier)
        status = _string(raw_slot["status"], f"{field}.status")
        if status not in STATUSES:
            raise ContractError(
                f"{field}.status must be one of: {', '.join(sorted(STATUSES))}"
            )
        if status == "planned":
            forbidden = sorted(FORBIDDEN_PLANNED_FIELDS & raw_slot.keys())
            if forbidden:
                raise ContractError(
                    f"{field} is planned and cannot carry: {', '.join(forbidden)}"
                )
        if status in {"draft", "withdrawn"} and (
            "artifacts" in raw_slot or "manifests" in raw_slot
        ):
            raise ContractError(f"{field} status {status} cannot publish resources")
        if status == "available" and (
            "version" not in raw_slot or not raw_slot.get("artifacts")
        ):
            raise ContractError(f"{field} available slots require version and artifacts")
        if status == "available" and "source" not in raw_slot:
            raise ContractError(f"{field} available slots require a pinned source revision")
        if status == "superseded" and "superseded_by" not in raw_slot:
            raise ContractError(f"{field} superseded slots require superseded_by")
        if status == "withdrawn" and "withdrawal_notice" not in raw_slot:
            raise ContractError(f"{field} withdrawn slots require withdrawal_notice")
        route = normalize_page_route(raw_slot.get("route", f"{identifier}/"), f"{field}.route")
        if route in slot_routes:
            raise ContractError(f"slots repeats normalized route {route}")
        slot_routes.add(route)
        order = raw_slot.get("order", index * 10)
        if isinstance(order, bool) or not isinstance(order, int):
            raise ContractError(f"{field}.order must be an integer")
        visible = raw_slot.get("visible", True)
        if not isinstance(visible, bool):
            raise ContractError(f"{field}.visible must be a boolean")
        slot: dict[str, Any] = {
            "id": identifier,
            "kind": _identifier(raw_slot["kind"], f"{field}.kind"),
            "title": _string(raw_slot["title"], f"{field}.title"),
            "summary": _string(raw_slot["summary"], f"{field}.summary"),
            "status": status,
            "route": route,
            "order": order,
            "visible": visible,
            "artifacts": [],
            "manifests": [],
            "copy": {},
            "landing": {"mode": "generated"},
        }
        for key in ("version", "superseded_by", "withdrawal_notice"):
            value = _optional_string(raw_slot, key, field)
            if value is not None:
                slot[key] = value
        if "copy" in raw_slot:
            slot["copy"] = _copy_contract(
                raw_slot["copy"],
                f"{field}.copy",
                {"availability", "eyebrow"},
            )
        if "source" in raw_slot:
            slot["source"] = _source_record(raw_slot["source"], f"{field}.source")
        if "provenance" in raw_slot:
            references = _list(raw_slot["provenance"], f"{field}.provenance")
            slot["provenance"] = [
                _reference(reference, f"{field}.provenance[{reference_index}]")
                for reference_index, reference in enumerate(references)
            ]
        if "preview" in raw_slot:
            slot["preview"] = _reference(raw_slot["preview"], f"{field}.preview")
        if "accessibility" in raw_slot:
            slot["accessibility"] = _accessibility(
                raw_slot["accessibility"], f"{field}.accessibility"
            )
        if "landing" in raw_slot:
            landing = _mapping(raw_slot["landing"], f"{field}.landing")
            _validate_keys(
                landing,
                required={"mode"},
                optional={"resource_id"},
                field=f"{field}.landing",
            )
            mode = _string(landing["mode"], f"{field}.landing.mode")
            if mode not in {"generated", "resource"}:
                raise ContractError(f"{field}.landing.mode must be generated or resource")
            slot["landing"] = {"mode": mode}
            if mode == "resource":
                slot["landing"]["resource_id"] = _identifier(
                    landing.get("resource_id"), f"{field}.landing.resource_id"
                )
            elif "resource_id" in landing:
                raise ContractError(
                    f"{field}.landing.resource_id is only valid for resource mode"
                )
        if "identifiers" in raw_slot:
            slot["identifiers"] = _identifiers(
                raw_slot["identifiers"], f"{field}.identifiers"
            )
        if "release" in raw_slot:
            release = _mapping(raw_slot["release"], f"{field}.release")
            _validate_keys(
                release,
                required={"url"},
                optional={"published_at"},
                field=f"{field}.release",
            )
            release_url = _string(release["url"], f"{field}.release.url")
            validate_https_url(release_url, f"{field}.release.url")
            slot["release"] = {"url": release_url}
            if "published_at" in release:
                published = _string(
                    release["published_at"], f"{field}.release.published_at"
                )
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", published):
                    raise ContractError(
                        f"{field}.release.published_at must use YYYY-MM-DD"
                    )
                slot["release"]["published_at"] = published
        if "artwork" in raw_slot:
            slot["artwork"] = _asset(
                raw_slot["artwork"],
                f"{field}.artwork",
                project,
                f"assets/slots/{identifier}/artwork",
            )
        if "artifacts" in raw_slot:
            resources = _list(raw_slot["artifacts"], f"{field}.artifacts")
            slot["artifacts"] = [
                _resource(
                    resource,
                    f"{field}.artifacts[{resource_index}]",
                    project,
                    allow_aliases=True,
                )
                for resource_index, resource in enumerate(resources)
            ]
        if "manifests" in raw_slot:
            resources = _list(raw_slot["manifests"], f"{field}.manifests")
            slot["manifests"] = [
                _resource(
                    resource,
                    f"{field}.manifests[{resource_index}]",
                    project,
                    allow_aliases=False,
                )
                for resource_index, resource in enumerate(resources)
            ]
        resource_ids: set[str] = set()
        resources_by_id: dict[str, dict[str, Any]] = {}
        for resource_group in (slot["artifacts"], slot["manifests"]):
            for resource in resource_group:
                if resource["id"] in resource_ids:
                    raise ContractError(f"{field} repeats resource id {resource['id']}")
                resource_ids.add(resource["id"])
                resources_by_id[resource["id"]] = resource
        if slot["landing"]["mode"] == "resource":
            landing_id = slot["landing"]["resource_id"]
            landing_resource = resources_by_id.get(landing_id)
            if landing_resource is None:
                raise ContractError(f"{field}.landing references unknown resource {landing_id}")
            if landing_resource["media_type"] != "text/html":
                raise ContractError(f"{field}.landing resource must use text/html")
            if landing_resource["path"] != f"{slot['route']}index.html":
                raise ContractError(
                    f"{field}.landing resource must own {slot['route']}index.html"
                )
            if landing_resource["route"] != slot["route"]:
                raise ContractError(
                    f"{field}.landing resource public route must be {slot['route']}"
                )
            if landing_resource["aliases"]:
                raise ContractError(
                    f"{field}.landing resource cannot declare root aliases"
                )
            if landing_id not in {resource["id"] for resource in slot["artifacts"]}:
                raise ContractError(
                    f"{field}.landing resource must be an artifact, not a manifest"
                )
        if "extensions" in raw_slot:
            slot["extensions"] = _extensions(
                raw_slot["extensions"], f"{field}.extensions"
            )
            if status == "planned":
                _reject_reserved_extension_keys(
                    slot["extensions"],
                    FORBIDDEN_PLANNED_FIELDS,
                    f"{field}.extensions",
                )
        slots.append(slot)

    slots.sort(key=lambda item: (item["order"], item["id"]))
    if any(slot["status"] == "available" for slot in slots) or require_deployable_revision:
        if not FULL_REVISION.fullmatch(source_revision):
            raise ContractError(
                "available slots and deployment builds require a full lowercase source revision"
            )
    for slot in slots:
        if slot["status"] == "available" and not FULL_REVISION.fullmatch(
            slot["source"]["revision"]
        ):
            raise ContractError(
                f"available slot {slot['id']} requires a full lowercase source revision"
            )
    result = {
        "schema": SOURCE_CATALOG_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "catalog_path": catalog_path,
        "catalog_sha256": sha256_file(catalog_path),
        "site": site,
        "slots": slots,
    }
    if "extensions" in catalog:
        result["extensions"] = catalog["extensions"]
    plan_outputs(result)
    return result


def plan_outputs(catalog: dict[str, Any]) -> OutputRegistry:
    """Plan every public file and reject collisions before rendering."""
    registry = OutputRegistry()
    public_routes: dict[str, tuple[str, str]] = {
        "": ("index.html", "hub landing"),
        "downloads/": ("downloads/index.html", "downloads landing"),
        "site.json": ("site.json", "public catalog"),
        "manifest.webmanifest": ("manifest.webmanifest", "web application manifest"),
        CHECKSUM_FILE: (CHECKSUM_FILE, "checksum inventory"),
    }
    for path, owner in {
        "index.html": "hub landing",
        "downloads/index.html": "downloads landing",
        "assets/site.css": "base stylesheet",
        "manifest.webmanifest": "web application manifest",
        "site.json": "public catalog",
        CHECKSUM_FILE: "checksum inventory",
    }.items():
        registry.add(path, owner)
    site = catalog["site"]
    if site.get("styles", {}).get("custom_css"):
        registry.add("assets/custom.css", "custom stylesheet")
    for key in ("brand", "artwork"):
        if key == "brand":
            asset = site.get("brand", {}).get("logo")
        else:
            asset = site.get("artwork")
        if asset:
            registry.add(asset["route"], f"site {key}")
    for slot in catalog["slots"]:
        if not slot["visible"]:
            continue
        if slot["landing"]["mode"] == "generated":
            registry.add(f"{slot['route']}index.html", f"slot {slot['id']}")
        if slot["route"] in public_routes:
            raise ContractError(f"slot {slot['id']} collides with public route {slot['route']}")
        public_routes[slot["route"]] = (
            f"{slot['route']}index.html",
            f"slot {slot['id']}",
        )
        if slot.get("artwork"):
            registry.add(slot["artwork"]["route"], f"slot {slot['id']} artwork")
        for group_name in ("artifacts", "manifests"):
            for resource in slot[group_name]:
                registry.add(resource["path"], f"slot {slot['id']} {resource['id']}")
                landing_owner = (
                    slot["landing"]["mode"] == "resource"
                    and slot["landing"].get("resource_id") == resource["id"]
                    and resource["route"] == slot["route"]
                )
                if resource["route"] in public_routes and not landing_owner:
                    prior = public_routes[resource["route"]][1]
                    raise ContractError(
                        f"slot {slot['id']} resource {resource['id']} public route "
                        f"collides with {prior}: {resource['route']}"
                    )
                if not landing_owner:
                    public_routes[resource["route"]] = (
                        resource["path"],
                        f"slot {slot['id']} resource {resource['id']}",
                    )
                for alias in resource["aliases"]:
                    registry.add(alias, f"slot {slot['id']} {resource['id']} alias")
                    if alias in public_routes:
                        raise ContractError(f"root alias collides with public route {alias}")
                    public_routes[alias] = (
                        alias,
                        f"slot {slot['id']} resource {resource['id']} alias",
                    )
    return registry


def catalog_source_paths(catalog: dict[str, Any]) -> list[Path]:
    """Return every local source file consumed by a hub build."""
    paths: list[Path] = []
    site = catalog["site"]
    for asset in (
        site.get("brand", {}).get("logo"),
        site.get("artwork"),
    ):
        if asset:
            paths.append(asset["source_path"])
    if site.get("styles", {}).get("custom_css_path"):
        paths.append(site["styles"]["custom_css_path"])
    for slot in catalog["slots"]:
        if slot.get("artwork"):
            paths.append(slot["artwork"]["source_path"])
        for group_name in ("artifacts", "manifests"):
            paths.extend(resource["source_path"] for resource in slot[group_name])
    return paths


def _relative_href(current_route: str, target_route: str, *, page: bool = False) -> str:
    start = current_route.rstrip("/") or "."
    target = target_route.rstrip("/") if page else target_route
    target = target or "."
    relative = posixpath.relpath(target, start=start)
    if page:
        return (relative if relative != "." else ".") + "/"
    return relative


def _asset_href(current_route: str, asset: dict[str, Any] | None) -> str | None:
    return None if not asset else _relative_href(current_route, asset["route"])


def _status_label(status: str) -> str:
    return status.replace("-", " ").title()


def _page_shell(
    catalog: dict[str, Any],
    route: str,
    title: str,
    description: str,
    body: str,
    structured_data: dict[str, Any],
) -> str:
    site = catalog["site"]
    visible_slots = [slot for slot in catalog["slots"] if slot["visible"]]
    home_href = _relative_href(route, "", page=True)
    downloads_href = _relative_href(route, "downloads/", page=True)
    css_href = _relative_href(route, "assets/site.css")
    custom_css = ""
    if site["styles"].get("custom_css"):
        custom_href = _relative_href(route, "assets/custom.css")
        custom_css = f'  <link rel="stylesheet" href="{html.escape(custom_href)}">\n'
    nav_items = [f'<a href="{html.escape(home_href)}">Home</a>']
    nav_items.extend(
        f'<a href="{html.escape(_relative_href(route, slot["route"], page=True))}">'
        f'{html.escape(slot["title"])}</a>'
        for slot in visible_slots
    )
    nav_items.append(f'<a href="{html.escape(downloads_href)}">Downloads</a>')
    logo = site.get("brand", {}).get("logo")
    logo_html = ""
    if logo:
        logo_html = (
            f'<img class="brand-logo" src="{html.escape(_asset_href(route, logo) or "")}" '
            f'alt="{html.escape(logo["alt"])}" width="56" height="56">'
        )
    canonical = public_url(site["canonical_base_url"], route)
    manifest_href = _relative_href(route, "manifest.webmanifest")
    social_asset = site.get("artwork") or logo
    social_image = (
        public_url(site["canonical_base_url"], social_asset["route"])
        if social_asset
        else None
    )
    og_image_meta = (
        f'  <meta property="og:image" content="{html.escape(social_image)}">\n'
        if social_image
        else ""
    )
    structured_data = dict(structured_data)
    structured_data["@context"] = "https://schema.org"
    structured_data["url"] = canonical
    structured_json = json.dumps(
        structured_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    structured_json = (
        structured_json.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    footer = site["copy"].get(
        "footer", f"Published by {site['publisher']} from a product-owned catalog."
    )
    return (
        "<!doctype html>\n"
        f'<html lang="{html.escape(site["language"])}">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{html.escape(title)} · {html.escape(site['title'])}</title>\n"
        f'  <meta name="description" content="{html.escape(description)}">\n'
        f'  <link rel="canonical" href="{html.escape(canonical)}">\n'
        f'  <link rel="manifest" href="{html.escape(manifest_href)}">\n'
        f'  <meta property="og:type" content="website">\n'
        f'  <meta property="og:title" content="{html.escape(title)}">\n'
        f'  <meta property="og:description" content="{html.escape(description)}">\n'
        f'  <meta property="og:url" content="{html.escape(canonical)}">\n'
        f"{og_image_meta}"
        f'  <link rel="stylesheet" href="{html.escape(css_href)}">\n'
        f"{custom_css}"
        f'  <script type="application/ld+json">{structured_json}</script>\n'
        "</head>\n"
        f'<body data-theme="{html.escape(site["theme"])}">\n'
        '  <a class="skip-link" href="#main-content">Skip to main content</a>\n'
        '  <header class="site-header">\n'
        f'    <a class="brand" href="{html.escape(home_href)}">{logo_html}'
        f'<span>{html.escape(site["title"])}</span></a>\n'
        f'    <nav aria-label="Publication navigation">{"".join(nav_items)}</nav>\n'
        "  </header>\n"
        f'  <main id="main-content">{body}</main>\n'
        f"  <footer><p>{html.escape(footer)}</p></footer>\n"
        "</body>\n"
        "</html>\n"
    )


def _hub_body(catalog: dict[str, Any]) -> str:
    site = catalog["site"]
    copy = site["copy"]
    artwork = site.get("artwork")
    art_html = ""
    if artwork:
        art_html = (
            f'<img class="hero-art" src="{html.escape(_asset_href("", artwork) or "")}" '
            f'alt="{html.escape(artwork["alt"])}">'
        )
    cards: list[str] = []
    for slot in catalog["slots"]:
        if not slot["visible"]:
            continue
        href = _relative_href("", slot["route"], page=True)
        cards.append(
            f'<article class="slot-card status-{html.escape(slot["status"])}">'
            f'<p class="status">{html.escape(_status_label(slot["status"]))}</p>'
            f'<h3><a href="{html.escape(href)}">{html.escape(slot["title"])}</a></h3>'
            f'<p>{html.escape(slot["summary"])}</p>'
            f'<p class="slot-kind">{html.escape(slot["kind"].replace("-", " ").title())}</p>'
            "</article>"
        )
    if not cards:
        cards.append(
            '<article class="slot-card"><p class="status">Catalog</p>'
            '<h2>No publication slots yet</h2>'
            '<p>The project has not announced a paper, magazine, or other publication slot.</p></article>'
        )
    return (
        '<section class="hero">'
        '<div class="hero-copy">'
        f'<p class="eyebrow">{html.escape(copy.get("eyebrow", "Publication collection"))}</p>'
        f'<h1>{html.escape(copy.get("heading", site["title"]))}</h1>'
        f'<p class="lede">{html.escape(copy.get("introduction", site["description"]))}</p>'
        f'<p><a class="button" href="{html.escape(_relative_href("", "downloads/", page=True))}">'
        "Browse verified downloads</a></p>"
        "</div>"
        f"{art_html}"
        "</section>"
        '<section aria-labelledby="publications-heading">'
        '<div class="section-heading"><p class="eyebrow">Catalog</p>'
        '<h2 id="publications-heading">Publication slots</h2></div>'
        f'<div class="slot-grid">{"".join(cards)}</div>'
        "</section>"
    )


def _resource_entry_html(current_route: str, resource: dict[str, Any]) -> str:
    href = _relative_href(
        current_route, resource["route"], page=resource["route"].endswith("/")
    )
    download_attribute = (
        "" if resource["media_type"] == "text/html" or resource["route"].endswith("/") else " download"
    )
    return (
        "<li>"
        f'<a href="{html.escape(href)}"{download_attribute}>{html.escape(resource["label"])}</a>'
        f'<span>{html.escape(resource["media_type"])} · {resource["bytes"]:,} bytes</span>'
        f'<code>sha256:{html.escape(resource["sha256"])}</code>'
        "</li>"
    )


def _slot_body(slot: dict[str, Any]) -> str:
    artwork = slot.get("artwork")
    artwork_html = ""
    if artwork:
        artwork_html = (
            f'<img class="slot-art" src="{html.escape(_asset_href(slot["route"], artwork) or "")}" '
            f'alt="{html.escape(artwork["alt"])}">'
        )
    details = ""
    if slot.get("version"):
        details += f'<dt>Version</dt><dd>{html.escape(slot["version"])}</dd>'
    details += f'<dt>Status</dt><dd>{html.escape(_status_label(slot["status"]))}</dd>'
    resources = slot["artifacts"] + slot["manifests"]
    if resources:
        resource_html = (
            '<section aria-labelledby="downloads-heading"><h2 id="downloads-heading">Downloads</h2>'
            f'<ul class="resource-list">{"".join(_resource_entry_html(slot["route"], item) for item in resources)}</ul>'
            "</section>"
        )
    else:
        availability = slot["copy"].get("availability") or {
            "planned": "This publication is planned. No artifact or release has been claimed.",
            "draft": "This publication remains a draft. No public artifact has been released.",
            "withdrawn": slot.get("withdrawal_notice", "This publication was withdrawn."),
        }.get(slot["status"], "No downloadable artifact is currently listed.")
        resource_html = (
            '<section class="availability" aria-labelledby="availability-heading">'
            '<h2 id="availability-heading">Availability</h2>'
            f"<p>{html.escape(availability)}</p></section>"
        )
    identifiers_html = ""
    if slot.get("identifiers"):
        items = []
        for identifier in slot["identifiers"]:
            label = f"{identifier['scheme'].upper()}: {identifier['value']}"
            if identifier.get("url"):
                items.append(
                    f'<li><a href="{html.escape(identifier["url"])}">{html.escape(label)}</a></li>'
                )
            else:
                items.append(f"<li>{html.escape(label)}</li>")
        identifiers_html = (
            '<section aria-labelledby="identifiers-heading"><h2 id="identifiers-heading">Identifiers</h2>'
            f'<ul>{"".join(items)}</ul></section>'
        )
    source_html = ""
    if slot.get("source"):
        source = slot["source"]
        path = f" · {html.escape(source['path'])}" if source.get("path") else ""
        source_html = (
            '<section aria-labelledby="source-heading"><h2 id="source-heading">Source revision</h2>'
            f'<p><a href="{html.escape(source["repository"])}">Repository</a> · '
            f'<code>{html.escape(source["revision"])}</code>{path}</p></section>'
        )
    provenance_html = ""
    if slot.get("provenance"):
        provenance_html = (
            '<section aria-labelledby="provenance-heading"><h2 id="provenance-heading">Provenance</h2><ul>'
            + "".join(
                f'<li><a href="{html.escape(reference["url"])}">{html.escape(reference["label"])}</a></li>'
                for reference in slot["provenance"]
            )
            + "</ul></section>"
        )
    preview_html = ""
    if slot.get("preview"):
        preview = slot["preview"]
        preview_html = (
            '<section aria-labelledby="preview-heading"><h2 id="preview-heading">Preview</h2>'
            f'<p><a href="{html.escape(preview["url"])}">{html.escape(preview["label"])}</a></p></section>'
        )
    accessibility_html = ""
    if slot.get("accessibility"):
        accessibility = slot["accessibility"]
        feature_items = "".join(
            f"<li>{html.escape(feature)}</li>" for feature in accessibility["features"]
        )
        report = ""
        if accessibility.get("report"):
            report = (
                f'<p><a href="{html.escape(accessibility["report"]["url"])}">'
                "Accessibility report</a></p>"
            )
        accessibility_html = (
            '<section aria-labelledby="accessibility-heading"><h2 id="accessibility-heading">Accessibility</h2>'
            f'<p>{html.escape(accessibility["summary"])}</p><ul>{feature_items}</ul>{report}</section>'
        )
    return (
        '<article class="slot-detail">'
        f'<p class="status status-{html.escape(slot["status"])}">{html.escape(_status_label(slot["status"]))}</p>'
        f'<h1>{html.escape(slot["title"])}</h1>'
        f'<p class="lede">{html.escape(slot["summary"])}</p>'
        f'{artwork_html}<dl class="metadata">{details}</dl>'
        f"{resource_html}{identifiers_html}{source_html}{provenance_html}{preview_html}{accessibility_html}"
        "</article>"
    )


def _hub_structured_data(catalog: dict[str, Any]) -> dict[str, Any]:
    site = catalog["site"]
    return {
        "@type": "CollectionPage",
        "name": site["title"],
        "description": site["description"],
        "inLanguage": site["language"],
        "publisher": {"@type": "Organization", "name": site["publisher"]},
        "hasPart": [
            {
                "@type": "CreativeWork",
                "name": slot["title"],
                "url": public_url(site["canonical_base_url"], slot["route"]),
                "creativeWorkStatus": slot["status"],
            }
            for slot in catalog["slots"]
            if slot["visible"]
        ],
    }


def _slot_structured_data(catalog: dict[str, Any], slot: dict[str, Any]) -> dict[str, Any]:
    site = catalog["site"]
    data: dict[str, Any] = {
        "@type": "CreativeWork",
        "name": slot["title"],
        "description": slot["summary"],
        "creativeWorkStatus": slot["status"],
        "inLanguage": site["language"],
        "isPartOf": {"@type": "CollectionPage", "url": site["canonical_base_url"]},
    }
    if slot.get("version"):
        data["version"] = slot["version"]
    if slot.get("identifiers"):
        data["identifier"] = [
            {"@type": "PropertyValue", "propertyID": item["scheme"], "value": item["value"]}
            for item in slot["identifiers"]
        ]
    resources = slot["artifacts"] + slot["manifests"]
    if resources:
        data["distribution"] = [
            {
                "@type": "DataDownload",
                "name": resource["label"],
                "contentUrl": resource["url"],
                "encodingFormat": resource["media_type"],
                "contentSize": resource["bytes"],
                "sha256": resource["sha256"],
            }
            for resource in resources
        ]
    if slot.get("accessibility"):
        data["accessibilitySummary"] = slot["accessibility"]["summary"]
        data["accessibilityFeature"] = slot["accessibility"]["features"]
    return data


def _downloads_structured_data(catalog: dict[str, Any]) -> dict[str, Any]:
    site = catalog["site"]
    resources = [
        resource
        for slot in catalog["slots"]
        if slot["visible"]
        for resource in slot["artifacts"] + slot["manifests"]
    ]
    return {
        "@type": "CollectionPage",
        "name": site["copy"].get("downloads_heading", "Verified downloads"),
        "description": site["copy"].get(
            "downloads_introduction", "Published files and verification data."
        ),
        "hasPart": [
            {
                "@type": "DataDownload",
                "name": resource["label"],
                "contentUrl": resource["url"],
                "encodingFormat": resource["media_type"],
                "contentSize": resource["bytes"],
                "sha256": resource["sha256"],
            }
            for resource in resources
        ],
    }


def _downloads_body(catalog: dict[str, Any]) -> str:
    site = catalog["site"]
    copy = site["copy"]
    sections: list[str] = []
    for slot in catalog["slots"]:
        if not slot["visible"]:
            continue
        resources = slot["artifacts"] + slot["manifests"]
        if not resources:
            continue
        sections.append(
            f'<section aria-labelledby="downloads-{html.escape(slot["id"])}">'
            f'<h2 id="downloads-{html.escape(slot["id"])}">{html.escape(slot["title"])}</h2>'
            f'<ul class="resource-list">{"".join(_resource_entry_html("downloads/", item) for item in resources)}</ul>'
            "</section>"
        )
    if not sections:
        sections.append(
            '<section class="availability" aria-labelledby="no-downloads">'
            '<h2 id="no-downloads">No published artifacts yet</h2>'
            "<p>Draft and planned slots intentionally do not expose fabricated download routes.</p>"
            "</section>"
        )
    return (
        '<header class="page-heading">'
        '<p class="eyebrow">Artifact inventory</p>'
        f'<h1>{html.escape(copy.get("downloads_heading", "Verified downloads"))}</h1>'
        f'<p class="lede">{html.escape(copy.get("downloads_introduction", "Published files and their verification data."))}</p>'
        "</header>"
        + "".join(sections)
    )


def _stylesheet(tokens: dict[str, str]) -> str:
    variables = "\n".join(f"  {name}: {value};" for name, value in sorted(tokens.items()))
    return f""":root {{
{variables}
  color-scheme: light dark;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
}}
* {{ box-sizing: border-box; }}
html {{ background: var(--hub-background); color: var(--hub-ink); scroll-behavior: smooth; }}
body {{ margin: 0; min-height: 100vh; background: radial-gradient(circle at top right, color-mix(in srgb, var(--hub-accent) 16%, transparent), transparent 30rem), var(--hub-background); line-height: 1.65; }}
a {{ color: var(--hub-accent); text-underline-offset: 0.2em; }}
a:focus-visible, button:focus-visible {{ outline: 0.2rem solid var(--hub-accent); outline-offset: 0.25rem; }}
.skip-link {{ position: absolute; left: 1rem; top: -8rem; z-index: 10; padding: 0.75rem 1rem; background: var(--hub-accent); color: var(--hub-accent-ink); }}
.skip-link:focus {{ top: 1rem; }}
.site-header, main, footer {{ width: min(72rem, calc(100% - 2rem)); margin-inline: auto; }}
.site-header {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding-block: 1.25rem; }}
.brand {{ display: inline-flex; align-items: center; gap: 0.75rem; color: var(--hub-ink); font-weight: 800; text-decoration: none; }}
.brand-logo {{ border-radius: 50%; }}
nav {{ display: flex; flex-wrap: wrap; gap: 0.9rem; }}
nav a {{ color: var(--hub-ink); }}
main {{ padding-block: clamp(2rem, 8vw, 6rem); }}
.hero {{ display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(14rem, 0.75fr); align-items: center; gap: 3rem; margin-bottom: 5rem; }}
.hero-art, .slot-art {{ display: block; width: 100%; max-height: 32rem; object-fit: cover; border-radius: var(--hub-radius); box-shadow: var(--hub-shadow); }}
.eyebrow, .status, .slot-kind {{ color: var(--hub-muted); font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }}
h1, h2, h3 {{ line-height: 1.12; text-wrap: balance; }}
h1 {{ margin: 0.25rem 0 1rem; font-size: clamp(2.7rem, 8vw, 6.5rem); letter-spacing: -0.055em; }}
h2 {{ font-size: clamp(1.5rem, 4vw, 2.35rem); }}
h3 {{ font-size: clamp(1.25rem, 3vw, 1.8rem); }}
.lede {{ max-width: 46rem; color: var(--hub-muted); font-size: clamp(1.05rem, 2vw, 1.35rem); }}
.button {{ display: inline-block; margin-top: 1rem; padding: 0.8rem 1.1rem; border-radius: 999px; background: var(--hub-accent); color: var(--hub-accent-ink); font-weight: 800; text-decoration: none; }}
.section-heading, .page-heading {{ margin-bottom: 2rem; }}
.slot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr)); gap: 1rem; }}
.slot-card, .availability, .resource-list li {{ border: 1px solid var(--hub-border); border-radius: var(--hub-radius); background: var(--hub-surface); box-shadow: var(--hub-shadow); }}
.slot-card {{ padding: clamp(1.25rem, 4vw, 2rem); }}
.slot-card h3 {{ margin-block: 0.45rem; }}
.slot-card h3 a {{ color: var(--hub-ink); }}
.status-planned {{ color: var(--hub-planned); }}
.status-draft {{ color: var(--hub-draft); }}
.status-available {{ color: var(--hub-available); }}
.status-withdrawn {{ color: var(--hub-withdrawn); }}
.slot-detail {{ max-width: 54rem; }}
.metadata {{ display: grid; grid-template-columns: max-content 1fr; gap: 0.4rem 1rem; margin-block: 2rem; }}
.metadata dt {{ font-weight: 800; }}
.metadata dd {{ margin: 0; }}
.availability {{ margin-block: 2rem; padding: 1.5rem; }}
.resource-list {{ display: grid; gap: 0.75rem; padding: 0; list-style: none; }}
.resource-list li {{ display: grid; gap: 0.2rem; padding: 1.25rem; }}
.resource-list span, .resource-list code {{ color: var(--hub-muted); overflow-wrap: anywhere; }}
footer {{ border-top: 1px solid var(--hub-border); padding-block: 2rem; color: var(--hub-muted); }}
@media (max-width: 48rem) {{
  .site-header {{ align-items: flex-start; flex-direction: column; }}
  .hero {{ grid-template-columns: 1fr; }}
  h1 {{ font-size: clamp(2.5rem, 15vw, 4.5rem); }}
}}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
"""


def _copy_asset(asset: dict[str, Any], site_directory: Path) -> None:
    destination = site_directory / PurePosixPath(asset["route"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(asset["source_path"], destination)


def _publish_resource(
    resource: dict[str, Any], site_directory: Path, site: dict[str, Any]
) -> dict[str, Any]:
    destination = site_directory / PurePosixPath(resource["path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(resource["source_path"], destination)
    digest = sha256_file(destination)
    size = destination.stat().st_size
    aliases: list[dict[str, str]] = []
    for alias in resource["aliases"]:
        alias_path = site_directory / alias
        shutil.copyfile(destination, alias_path)
        aliases.append(
            {
                "path": alias,
                "url": public_url(site["canonical_base_url"], alias),
                "fallback_url": public_url(site["fallback_base_url"], alias),
            }
        )
    result: dict[str, Any] = {
        "id": resource["id"],
        "label": resource["label"],
        "media_type": resource["media_type"],
        "path": resource["path"],
        "route": resource["route"],
        "bytes": size,
        "sha256": digest,
        "url": public_url(site["canonical_base_url"], resource["route"]),
        "fallback_url": public_url(site["fallback_base_url"], resource["route"]),
        "aliases": aliases,
    }
    if resource.get("extensions"):
        result["extensions"] = resource["extensions"]
    return result


def _resolve_reference(
    reference: dict[str, str], resources: dict[str, dict[str, Any]], field: str
) -> dict[str, Any]:
    """Resolve an external reference or a declared local staged resource."""
    if reference.get("url"):
        return dict(reference)
    resource_id = reference["resource_id"]
    resource = resources.get(resource_id)
    if resource is None:
        raise ContractError(f"{field} references unknown resource {resource_id}")
    return {
        "label": reference["label"],
        "resource_id": resource_id,
        "url": resource["url"],
        "fallback_url": resource["fallback_url"],
        "media_type": resource["media_type"],
        "path": resource["path"],
        "bytes": resource["bytes"],
        "sha256": resource["sha256"],
    }


def _public_site_record(site: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "title",
        "description",
        "language",
        "stage",
        "publisher",
        "theme",
        "canonical_base_url",
        "fallback_base_url",
        "repository",
        "revision",
    )
    result = {key: site[key] for key in keys if key in site}
    if site.get("extensions"):
        result["extensions"] = site["extensions"]
    return result


def render_site(catalog: dict[str, Any], output_root: Path) -> None:
    """Render a complete public site tree into an empty owned workspace."""
    site_directory = output_root / "site"
    site_directory.mkdir(parents=True)
    (output_root / OWNERSHIP_MARKER).write_text(OWNERSHIP_VALUE, encoding="utf-8")
    site = catalog["site"]
    tokens = dict(THEME_TOKENS[site["theme"]])
    tokens.update(site["styles"]["tokens"])
    css_path = site_directory / "assets" / "site.css"
    css_path.parent.mkdir(parents=True)
    css_path.write_text(_stylesheet(tokens), encoding="utf-8")
    if site["styles"].get("custom_css_path"):
        shutil.copyfile(site["styles"]["custom_css_path"], site_directory / "assets/custom.css")
    logo = site.get("brand", {}).get("logo")
    if logo:
        _copy_asset(logo, site_directory)
    if site.get("artwork"):
        _copy_asset(site["artwork"], site_directory)
    web_manifest: dict[str, Any] = {
        "name": site["title"],
        "short_name": site["title"][:32],
        "description": site["description"],
        "id": "./",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": tokens["--hub-background"],
        "theme_color": tokens["--hub-accent"],
    }
    if logo:
        web_manifest["icons"] = [
            {
                "src": logo["route"].removeprefix("assets/"),
                "type": "image/svg+xml"
                if logo["route"].endswith(".svg")
                else f"image/{PurePosixPath(logo['route']).suffix.lstrip('.')}",
                "sizes": "any",
            }
        ]
        web_manifest["icons"][0]["src"] = f"./{logo['route']}"
    write_json(site_directory / "manifest.webmanifest", web_manifest)

    public_slots: list[dict[str, Any]] = []
    resource_routes: list[dict[str, Any]] = []
    for slot in catalog["slots"]:
        if not slot["visible"]:
            continue
        if slot.get("artwork"):
            _copy_asset(slot["artwork"], site_directory)
        public_slot: dict[str, Any] = {
            "id": slot["id"],
            "kind": slot["kind"],
            "title": slot["title"],
            "summary": slot["summary"],
            "status": slot["status"],
            "order": slot["order"],
            "route": slot["route"],
            "url": public_url(site["canonical_base_url"], slot["route"]),
            "fallback_url": public_url(site["fallback_base_url"], slot["route"]),
        }
        for key in (
            "version",
            "identifiers",
            "source",
            "accessibility",
            "release",
            "superseded_by",
            "withdrawal_notice",
            "extensions",
        ):
            if slot.get(key):
                public_slot[key] = slot[key]
        for group_name in ("artifacts", "manifests"):
            published = [
                _publish_resource(resource, site_directory, site)
                for resource in slot[group_name]
            ]
            if published:
                public_slot[group_name] = published
                for item in published:
                    is_landing = (
                        slot["landing"]["mode"] == "resource"
                        and slot["landing"].get("resource_id") == item["id"]
                    )
                    if not is_landing:
                        route_record = {
                            "kind": group_name[:-1],
                            "id": f"{slot['id']}:{item['id']}",
                            "path": item["route"],
                            "url": item["url"],
                            "fallback_url": item["fallback_url"],
                        }
                        default_file = (
                            f"{item['route']}index.html"
                            if item["route"].endswith("/")
                            else item["route"]
                        )
                        if item["path"] != default_file:
                            route_record["file"] = item["path"]
                        resource_routes.append(route_record)
                    resource_routes.extend(
                        {
                            "kind": "artifact-alias",
                            "id": f"{slot['id']}:{item['id']}",
                            "path": alias["path"],
                            "url": alias["url"],
                            "fallback_url": alias["fallback_url"],
                        }
                        for alias in item["aliases"]
                    )
        published_resources = {
            resource["id"]: resource
            for group_name in ("artifacts", "manifests")
            for resource in public_slot.get(group_name, [])
        }
        if slot.get("provenance"):
            public_slot["provenance"] = [
                _resolve_reference(
                    reference, published_resources, f"slot {slot['id']} provenance"
                )
                for reference in slot["provenance"]
            ]
        if slot.get("preview"):
            public_slot["preview"] = _resolve_reference(
                slot["preview"], published_resources, f"slot {slot['id']} preview"
            )
        public_slot["landing"] = dict(slot["landing"])
        public_slots.append(public_slot)
        slot["artifacts"] = public_slot.get("artifacts", [])
        slot["manifests"] = public_slot.get("manifests", [])
        slot["provenance"] = public_slot.get("provenance", [])
        if public_slot.get("preview"):
            slot["preview"] = public_slot["preview"]

    routes = [
        {
            "kind": "hub",
            "id": "home",
            "path": "",
            "url": site["canonical_base_url"],
            "fallback_url": site["fallback_base_url"],
        },
        {
            "kind": "downloads",
            "id": "downloads",
            "path": "downloads/",
            "url": public_url(site["canonical_base_url"], "downloads/"),
            "fallback_url": public_url(site["fallback_base_url"], "downloads/"),
        },
        {
            "kind": "catalog",
            "id": "site-json",
            "path": "site.json",
            "url": public_url(site["canonical_base_url"], "site.json"),
            "fallback_url": public_url(site["fallback_base_url"], "site.json"),
        },
        {
            "kind": "web-manifest",
            "id": "web-manifest",
            "path": "manifest.webmanifest",
            "url": public_url(site["canonical_base_url"], "manifest.webmanifest"),
            "fallback_url": public_url(site["fallback_base_url"], "manifest.webmanifest"),
        },
        {
            "kind": "checksum",
            "id": "sha256sums",
            "path": CHECKSUM_FILE,
            "url": public_url(site["canonical_base_url"], CHECKSUM_FILE),
            "fallback_url": public_url(site["fallback_base_url"], CHECKSUM_FILE),
        },
    ]
    routes.extend(
        {
            "kind": "slot",
            "id": slot["id"],
            "path": slot["route"],
            "url": public_url(site["canonical_base_url"], slot["route"]),
            "fallback_url": public_url(site["fallback_base_url"], slot["route"]),
        }
        for slot in public_slots
    )
    for resource_route in resource_routes:
        routes.append(resource_route)
    routes.sort(key=lambda item: (item["path"], item["kind"], item["id"]))
    source: dict[str, Any] = {"catalog_sha256": catalog["catalog_sha256"]}
    for key in ("repository", "revision"):
        if site.get(key):
            source[key] = site[key]
    public_catalog: dict[str, Any] = {
        "schema": SITE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "site": _public_site_record(site),
        "routes": routes,
        "slots": public_slots,
    }
    if catalog.get("extensions"):
        public_catalog["extensions"] = catalog["extensions"]

    (site_directory / "index.html").write_text(
        _page_shell(
            catalog,
            "",
            site["title"],
            site["description"],
            _hub_body(catalog),
            _hub_structured_data(catalog),
        ),
        encoding="utf-8",
    )
    for slot in catalog["slots"]:
        if not slot["visible"]:
            continue
        if slot["landing"]["mode"] != "generated":
            continue
        destination = site_directory / PurePosixPath(slot["route"]) / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            _page_shell(
                catalog,
                slot["route"],
                slot["title"],
                slot["summary"],
                _slot_body(slot),
                _slot_structured_data(catalog, slot),
            ),
            encoding="utf-8",
        )
    downloads_path = site_directory / "downloads" / "index.html"
    downloads_path.parent.mkdir(parents=True, exist_ok=True)
    downloads_path.write_text(
        _page_shell(
            catalog,
            "downloads/",
            site["copy"].get("downloads_heading", "Verified downloads"),
            site["copy"].get("downloads_introduction", site["description"]),
            _downloads_body(catalog),
            _downloads_structured_data(catalog),
        ),
        encoding="utf-8",
    )
    write_json(site_directory / "site.json", public_catalog)
    validate_html_links(site_directory)
    write_checksums(site_directory)


class LinkCollector(HTMLParser):
    """Collect local link targets and element identifiers from HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: list[str] = []
        self.tags: list[str] = []
        self.html_languages: list[str] = []
        self.canonicals: list[str] = []
        self.manifests: list[str] = []
        self.open_graph: dict[str, list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(attributes["id"] or "")
        if tag == "html" and attributes.get("lang"):
            self.html_languages.append(attributes["lang"] or "")
        if tag == "link" and attributes.get("rel") == "canonical":
            self.canonicals.append(attributes.get("href") or "")
        if tag == "link" and attributes.get("rel") == "manifest":
            self.manifests.append(attributes.get("href") or "")
        if tag == "meta" and str(attributes.get("property", "")).startswith("og:"):
            property_name = attributes.get("property") or ""
            self.open_graph.setdefault(property_name, []).append(
                attributes.get("content") or ""
            )
        for name in ("href", "src"):
            if attributes.get(name):
                self.links.append(attributes[name] or "")


def _resolve_local_link(site: Path, page: Path, link: str) -> tuple[Path | None, str]:
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme == "https" and parsed.netloc:
            validate_https_url(link, f"external link in {page}")
            return None, ""
        if parsed.scheme == "mailto" and not parsed.netloc and parsed.path:
            return None, ""
        raise ContractError(f"unsafe external link in {page}: {link}")
    if parsed.path.startswith("/") or "\\" in parsed.path:
        raise ContractError(f"root-relative or ambiguous local link in {page}: {link}")
    if "%" in parsed.path:
        raise ContractError(f"encoded local links are not permitted in {page}: {link}")
    relative_page = page.relative_to(site)
    target_relative = PurePosixPath(relative_page.parent.as_posix()) / parsed.path
    normalized = posixpath.normpath(target_relative.as_posix())
    if normalized == ".." or normalized.startswith("../"):
        raise ContractError(f"local link escapes the site in {page}: {link}")
    if parsed.path.endswith("/"):
        normalized = (
            "index.html"
            if normalized == "."
            else posixpath.join(normalized, "index.html")
        )
    elif normalized == ".":
        normalized = "index.html"
    target = site / PurePosixPath(normalized)
    try:
        target.relative_to(site)
    except ValueError as error:
        raise ContractError(f"local link escapes the site in {page}: {link}") from error
    if target.is_dir():
        target /= "index.html"
    return target, parsed.fragment


def validate_html_links(site: Path) -> None:
    """Reject inaccessible generated pages and broken local links/fragments."""
    public_catalog = read_json(site / "site.json")
    public_site = _mapping(public_catalog.get("site"), "site catalog.site")
    expected_language = _string(public_site.get("language"), "site catalog.site.language")
    route_urls_by_file: dict[str, str] = {}
    for route_value in _list(public_catalog.get("routes"), "site catalog.routes"):
        route = _mapping(route_value, "site catalog route")
        public_path = route.get("path", "")
        physical = route.get("file")
        if physical is None:
            physical = (
                "index.html"
                if public_path == ""
                else f"{public_path}index.html"
                if str(public_path).endswith("/")
                else public_path
            )
        route_urls_by_file[str(physical)] = str(route.get("url", ""))
    pages = sorted(site.rglob("*.html"))
    parsed_pages: dict[Path, LinkCollector] = {}
    for page in pages:
        if page.is_symlink():
            raise ContractError(f"public HTML cannot be a symlink: {page}")
        text = page.read_text(encoding="utf-8")
        collector = LinkCollector()
        collector.feed(text)
        parsed_pages[page] = collector
        for required in ("html", "title", "main", "h1"):
            if collector.tags.count(required) != 1:
                raise ContractError(
                    f"generated page {page} must contain exactly one <{required}>"
                )
        if collector.html_languages != [expected_language]:
            raise ContractError(f"generated page {page} has an invalid language marker")
        if len(collector.ids) != len(set(collector.ids)):
            raise ContractError(f"generated page {page} repeats an element id")
        if 'href="#main-content"' not in text or 'id="main-content"' not in text:
            raise ContractError(f"generated page {page} is missing its skip-link contract")
        relative_page = page.relative_to(site).as_posix()
        expected_url = route_urls_by_file.get(relative_page)
        if expected_url is None:
            raise ContractError(f"generated page {page} is absent from the route catalog")
        if collector.canonicals != [expected_url]:
            raise ContractError(f"generated page {page} canonical URL disagrees with site.json")
        page_parent = PurePosixPath(relative_page).parent.as_posix()
        current_route = "" if page_parent == "." else f"{page_parent}/"
        expected_manifest = _relative_href(current_route, "manifest.webmanifest")
        if collector.manifests != [expected_manifest]:
            raise ContractError(f"generated page {page} has an invalid web-manifest link")
        for required_property in ("og:title", "og:description", "og:type", "og:url"):
            if len(collector.open_graph.get(required_property, [])) != 1:
                raise ContractError(
                    f"generated page {page} must carry one {required_property} marker"
                )
        if collector.open_graph["og:url"] != [expected_url]:
            raise ContractError(f"generated page {page} Open Graph URL disagrees with site.json")
        structured_blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.DOTALL
        )
        if len(structured_blocks) != 1:
            raise ContractError(f"generated page {page} must carry one JSON-LD block")
        try:
            structured = json.loads(
                structured_blocks[0],
                object_pairs_hook=_strict_object,
                parse_constant=_reject_json_constant,
            )
        except (ValueError, json.JSONDecodeError, _DuplicateKeyError) as error:
            raise ContractError(f"generated page {page} has invalid JSON-LD") from error
        if (
            not isinstance(structured, dict)
            or structured.get("@context") != "https://schema.org"
            or not structured.get("@type")
            or structured.get("url") != expected_url
        ):
            raise ContractError(f"generated page {page} has incomplete JSON-LD")
    for page, collector in parsed_pages.items():
        for link in collector.links:
            target, fragment = _resolve_local_link(site, page, link)
            if target is None:
                continue
            if not target.is_file() or target.is_symlink():
                raise ContractError(f"broken local link in {page}: {link}")
            if fragment and target.suffix.lower() == ".html":
                target_collector = parsed_pages.get(target)
                if target_collector is None:
                    target_collector = LinkCollector()
                    target_collector.feed(target.read_text(encoding="utf-8"))
                if fragment not in target_collector.ids:
                    raise ContractError(f"broken local fragment in {page}: {link}")


def public_files(site: Path) -> list[Path]:
    """Return every regular public file except the checksum inventory itself."""
    result: list[Path] = []
    for path in site.rglob("*"):
        if path.is_symlink():
            raise ContractError(f"public output cannot contain symlinks: {path}")
        if path.is_file() and path.name != CHECKSUM_FILE:
            if path.stat().st_size <= 0:
                raise ContractError(f"public output cannot contain empty files: {path}")
            result.append(path)
    return sorted(result, key=lambda path: path.relative_to(site).as_posix())


def write_checksums(site: Path) -> None:
    """Write a complete, sorted SHA-256 inventory for the public tree."""
    lines = [
        f"{sha256_file(path)}  {path.relative_to(site).as_posix()}"
        for path in public_files(site)
    ]
    (site / CHECKSUM_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_checksums(site: Path) -> None:
    """Verify checksum coverage, ordering, paths, and file bytes."""
    checksum_path = site / CHECKSUM_FILE
    if not checksum_path.is_file() or checksum_path.is_symlink():
        raise ContractError(f"missing {CHECKSUM_FILE}")
    expected_files = [path.relative_to(site).as_posix() for path in public_files(site)]
    lines = checksum_path.read_text(encoding="utf-8").splitlines()
    entries: list[tuple[str, str]] = []
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\r\n]+)", line)
        if not match:
            raise ContractError(f"invalid {CHECKSUM_FILE} line: {line!r}")
        digest, relative = match.groups()
        normalized = PurePosixPath(relative).as_posix()
        if normalized != relative or relative.startswith("/") or ".." in PurePosixPath(relative).parts:
            raise ContractError(f"unsafe checksum path: {relative}")
        entries.append((digest, relative))
    listed_files = [relative for _, relative in entries]
    if listed_files != sorted(set(listed_files)):
        raise ContractError(f"{CHECKSUM_FILE} paths must be unique and sorted")
    if listed_files != expected_files:
        raise ContractError(f"{CHECKSUM_FILE} does not exactly cover the public tree")
    for digest, relative in entries:
        if sha256_file(site / PurePosixPath(relative)) != digest:
            raise ContractError(f"checksum mismatch: {relative}")


def _public_file(
    site_directory: Path, value: Any, field: str, *, require_extension: bool = True
) -> tuple[str, Path]:
    relative = (
        normalize_file_route(value, field)
        if require_extension
        else normalize_relative_file(value, field)
    )
    target = site_directory / PurePosixPath(relative)
    if target.is_symlink():
        raise ContractError(f"{field} cannot reference a symlink")
    return relative, target


def _validate_public_reference(
    reference_value: Any,
    resources: dict[str, dict[str, Any]],
    field: str,
) -> None:
    """Verify an external reference or its exact local resource projection."""
    reference = _mapping(reference_value, field)
    _string(reference.get("label"), f"{field}.label")
    validate_https_url(reference.get("url"), f"{field}.url")
    if "media_type" in reference and not MEDIA_TYPE.fullmatch(reference["media_type"]):
        raise ContractError(f"{field}.media_type is invalid")
    resource_id = reference.get("resource_id")
    if resource_id is None:
        local_only = {"fallback_url", "path", "bytes", "sha256"} & reference.keys()
        if local_only:
            raise ContractError(f"{field} external reference carries local resource data")
        return
    resource_id = _identifier(resource_id, f"{field}.resource_id")
    resource = resources.get(resource_id)
    if resource is None:
        raise ContractError(f"{field} references unknown resource {resource_id}")
    for key in (
        "url",
        "fallback_url",
        "media_type",
        "path",
        "bytes",
        "sha256",
    ):
        if reference.get(key) != resource.get(key):
            raise ContractError(f"{field}.{key} disagrees with resource {resource_id}")


def _default_route_file(route: str) -> str:
    if route == "":
        return "index.html"
    return f"{route}index.html" if route.endswith("/") else route


def validate_public_catalog(
    site_directory: Path, *, require_deployable_revision: bool = False
) -> None:
    """Validate the complete renderer-neutral public projection and its bytes."""
    catalog_path = site_directory / "site.json"
    if catalog_path.is_symlink():
        raise ContractError("public site.json cannot be a symlink")
    catalog = read_json(catalog_path)
    validate_schema_document(catalog, PUBLIC_SCHEMA_PATH, "site catalog")
    if catalog["schema"] != SITE_SCHEMA or catalog["schema_version"] != SCHEMA_VERSION:
        raise ContractError(f"site.json must use {SITE_SCHEMA} at {SCHEMA_VERSION}")

    site = _mapping(catalog["site"], "site catalog.site")
    canonical = normalize_base_url(
        site["canonical_base_url"], "site catalog.site.canonical_base_url"
    )
    fallback = (
        normalize_base_url(
            site["fallback_base_url"], "site catalog.site.fallback_base_url"
        )
        if site["fallback_base_url"] is not None
        else None
    )
    if canonical != site["canonical_base_url"] or (
        fallback is not None and fallback != site["fallback_base_url"]
    ):
        raise ContractError("site catalog base URLs must already be normalized")
    if fallback is not None and canonical == fallback:
        raise ContractError("site catalog canonical and fallback bases must be distinct")
    _identifier(site["id"], "site catalog.site.id")
    _string(site["title"], "site catalog.site.title")
    _string(site["description"], "site catalog.site.description")
    _string(site["publisher"], "site catalog.site.publisher")
    language = _string(site["language"], "site catalog.site.language")
    if not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", language):
        raise ContractError("site catalog has an invalid language tag")
    if site["stage"] not in SITE_STAGES or site["theme"] not in THEMES:
        raise ContractError("site catalog has an invalid stage or theme")
    if "repository" in site:
        validate_https_url(site["repository"], "site catalog.site.repository")

    source = _mapping(catalog["source"], "site catalog.source")
    revision = _string(source["revision"], "site catalog.source.revision")
    if revision != "WORKING_TREE" and not FULL_REVISION.fullmatch(revision):
        raise ContractError("site catalog source revision is not pinned or WORKING_TREE")
    if site["revision"] != revision:
        raise ContractError("site catalog source and site revisions disagree")
    if not re.fullmatch(r"[0-9a-f]{64}", source["catalog_sha256"]):
        raise ContractError("site catalog source digest is invalid")
    if "repository" in source:
        validate_https_url(source["repository"], "site catalog.source.repository")
    if site.get("repository") != source.get("repository"):
        raise ContractError("site catalog source and site repositories disagree")

    route_values = _list(catalog["routes"], "site catalog.routes")
    if route_values != sorted(
        route_values, key=lambda item: (item["path"], item["kind"], item["id"])
    ):
        raise ContractError("site catalog routes must use deterministic path/kind/id order")
    actual_routes: dict[str, dict[str, Any]] = {}
    route_ids: dict[str, list[str]] = {}
    for index, route_value in enumerate(route_values):
        field = f"site catalog.routes[{index}]"
        route = _mapping(route_value, field)
        kind = _identifier(route["kind"], f"{field}.kind")
        route_id = _string(route["id"], f"{field}.id")
        raw_path = route["path"]
        if raw_path == "":
            path = ""
        elif raw_path.endswith("/"):
            path = normalize_page_route(raw_path, f"{field}.path")
        else:
            path = normalize_relative_file(raw_path, f"{field}.path")
        if path != raw_path or path in actual_routes:
            raise ContractError(f"{field}.path is repeated or not normalized")
        if route["url"] != public_url(canonical, path):
            raise ContractError(f"{field}.url disagrees with the canonical base")
        if route["fallback_url"] != public_url(fallback, path):
            raise ContractError(f"{field}.fallback_url disagrees with the fallback base")
        physical = route.get("file", _default_route_file(path))
        physical, target = _public_file(
            site_directory, physical, f"{field}.file", require_extension=False
        )
        if ("file" in route) != (physical != _default_route_file(path)):
            raise ContractError(f"{field}.file must appear only for a non-default entrypoint")
        if not target.is_file() or target.is_symlink() or target.stat().st_size <= 0:
            raise ContractError(f"site catalog route is not a non-empty staged file: {path}")
        actual_routes[path] = {
            "kind": kind,
            "id": route_id,
            "file": physical,
        }
        route_ids.setdefault(route_id, []).append(kind)

    expected_routes = {
        path: {"kind": kind, "id": route_id, "file": physical}
        for path, (kind, route_id, physical) in CORE_ROUTES.items()
    }
    slots = _list(catalog["slots"], "site catalog.slots")
    if slots != sorted(slots, key=lambda item: (item["order"], item["id"])):
        raise ContractError("site catalog slots must use deterministic order/id order")
    slot_ids: set[str] = set()
    slot_routes: set[str] = set()
    has_available_slot = False
    for slot_index, slot_value in enumerate(slots):
        field = f"site catalog.slots[{slot_index}]"
        slot = _mapping(slot_value, field)
        slot_id = _identifier(slot["id"], f"{field}.id")
        if slot_id in slot_ids or slot_id in RESERVED_ROUTE_IDS:
            raise ContractError(f"{field}.id is repeated or reserved")
        slot_ids.add(slot_id)
        _identifier(slot["kind"], f"{field}.kind")
        _string(slot["title"], f"{field}.title")
        _string(slot["summary"], f"{field}.summary")
        status = slot["status"]
        if status not in STATUSES:
            raise ContractError(f"{field} has invalid status: {status}")
        has_available_slot |= status == "available"
        if status == "planned":
            forbidden = FORBIDDEN_PLANNED_FIELDS & slot.keys()
            if forbidden:
                raise ContractError("site catalog planned slot carries publication data")
            if slot.get("extensions"):
                _reject_reserved_extension_keys(
                    slot["extensions"], FORBIDDEN_PLANNED_FIELDS, f"{field}.extensions"
                )
        if status in {"draft", "withdrawn"} and (
            "artifacts" in slot or "manifests" in slot
        ):
            raise ContractError(f"{field} status {status} cannot publish resources")
        if status == "available" and (
            not slot.get("version") or not slot.get("source") or not slot.get("artifacts")
        ):
            raise ContractError(f"{field} available slots require version, source, artifacts")
        if status == "superseded" and not slot.get("superseded_by"):
            raise ContractError(f"{field} superseded slot is missing superseded_by")
        if status == "withdrawn" and not slot.get("withdrawal_notice"):
            raise ContractError(f"{field} withdrawn slot is missing withdrawal_notice")

        slot_route = normalize_page_route(slot["route"], f"{field}.route")
        if slot_route != slot["route"] or slot_route in slot_routes:
            raise ContractError(f"{field}.route is repeated or not normalized")
        slot_routes.add(slot_route)
        if slot["url"] != public_url(canonical, slot_route) or slot[
            "fallback_url"
        ] != public_url(fallback, slot_route):
            raise ContractError(f"{field} public URLs disagree with its route")
        expected_routes[slot_route] = {
            "kind": "slot",
            "id": slot_id,
            "file": f"{slot_route}index.html",
        }
        if "source" in slot:
            slot_source = _mapping(slot["source"], f"{field}.source")
            validate_https_url(slot_source["repository"], f"{field}.source.repository")
            slot_revision = _string(slot_source["revision"], f"{field}.source.revision")
            if slot_revision != "WORKING_TREE" and not FULL_REVISION.fullmatch(slot_revision):
                raise ContractError(f"{field}.source.revision is invalid")
            if status == "available" and not FULL_REVISION.fullmatch(slot_revision):
                raise ContractError(f"{field} available source revision is not pinned")
            if "path" in slot_source:
                _safe_relative_source(slot_source["path"], f"{field}.source.path")
        for identifier_index, identifier_value in enumerate(slot.get("identifiers", [])):
            identifier_field = f"{field}.identifiers[{identifier_index}]"
            identifier = _mapping(identifier_value, identifier_field)
            _identifier(identifier["scheme"], f"{identifier_field}.scheme")
            _string(identifier["value"], f"{identifier_field}.value")
            if "url" in identifier:
                validate_https_url(identifier["url"], f"{identifier_field}.url")
        if "release" in slot:
            release = _mapping(slot["release"], f"{field}.release")
            validate_https_url(release["url"], f"{field}.release.url")

        resources: dict[str, dict[str, Any]] = {}
        for group_name in ("artifacts", "manifests"):
            for resource_index, resource_value in enumerate(slot.get(group_name, [])):
                resource_field = f"{field}.{group_name}[{resource_index}]"
                resource = _mapping(resource_value, resource_field)
                if group_name == "manifests" and resource["aliases"]:
                    raise ContractError(f"{resource_field} cannot declare aliases")
                resource_id = _identifier(resource["id"], f"{resource_field}.id")
                if resource_id in resources:
                    raise ContractError(f"{field} repeats resource id {resource_id}")
                relative, resource_path = _public_file(
                    site_directory, resource["path"], f"{resource_field}.path"
                )
                route = normalize_public_route(resource["route"], f"{resource_field}.route")
                index_route = (
                    f"{PurePosixPath(relative).parent.as_posix()}/"
                    if PurePosixPath(relative).name == "index.html"
                    and PurePosixPath(relative).parent.as_posix() != "."
                    else ""
                )
                if route not in {relative, index_route}:
                    raise ContractError(
                        f"{resource_field}.route does not map to its physical path"
                    )
                if resource["url"] != public_url(canonical, route) or resource[
                    "fallback_url"
                ] != public_url(fallback, route):
                    raise ContractError(f"{resource_field} public URLs are invalid")
                if (
                    not resource_path.is_file()
                    or resource_path.is_symlink()
                    or resource_path.stat().st_size <= 0
                ):
                    raise ContractError(f"{resource_field} is not a non-empty staged file")
                if resource["bytes"] != resource_path.stat().st_size:
                    raise ContractError(f"{resource_field} byte count mismatch")
                if resource["sha256"] != sha256_file(resource_path):
                    raise ContractError(f"{resource_field} digest mismatch")
                if not MEDIA_TYPE.fullmatch(resource["media_type"]):
                    raise ContractError(f"{resource_field} media type is invalid")
                resources[resource_id] = resource
                is_landing = (
                    slot["landing"]["mode"] == "resource"
                    and slot["landing"].get("resource_id") == resource_id
                )
                if is_landing:
                    if (
                        resource["media_type"] != "text/html"
                        or relative != f"{slot_route}index.html"
                        or route != slot_route
                        or resource["aliases"]
                    ):
                        raise ContractError(f"{resource_field} is not a valid slot landing")
                    expected_routes[slot_route]["file"] = relative
                else:
                    if route in expected_routes:
                        raise ContractError(f"{resource_field}.route collides with another route")
                    expected_routes[route] = {
                        "kind": group_name[:-1],
                        "id": f"{slot_id}:{resource_id}",
                        "file": relative,
                    }
                for alias_index, alias_value in enumerate(resource["aliases"]):
                    alias_field = f"{resource_field}.aliases[{alias_index}]"
                    alias = _mapping(alias_value, alias_field)
                    alias_relative, alias_path = _public_file(
                        site_directory, alias["path"], f"{alias_field}.path"
                    )
                    if "/" in alias_relative or alias_relative in expected_routes:
                        raise ContractError(f"{alias_field} is not a unique root alias")
                    if alias["url"] != public_url(canonical, alias_relative) or alias[
                        "fallback_url"
                    ] != public_url(fallback, alias_relative):
                        raise ContractError(f"{alias_field} public URLs are invalid")
                    if (
                        not alias_path.is_file()
                        or alias_path.is_symlink()
                        or alias_path.stat().st_size != resource_path.stat().st_size
                        or sha256_file(alias_path) != resource["sha256"]
                    ):
                        raise ContractError(f"{alias_field} does not preserve artifact bytes")
                    expected_routes[alias_relative] = {
                        "kind": "artifact-alias",
                        "id": f"{slot_id}:{resource_id}",
                        "file": alias_relative,
                    }
        if slot["landing"]["mode"] == "resource":
            landing_id = slot["landing"].get("resource_id")
            artifact_ids = {
                resource["id"] for resource in slot.get("artifacts", [])
            }
            if landing_id not in artifact_ids:
                raise ContractError(
                    f"{field}.landing must reference an artifact resource"
                )
        for reference_index, reference in enumerate(slot.get("provenance", [])):
            _validate_public_reference(
                reference, resources, f"{field}.provenance[{reference_index}]"
            )
        if "preview" in slot:
            _validate_public_reference(slot["preview"], resources, f"{field}.preview")
        if "accessibility" in slot and "report" in slot["accessibility"]:
            _validate_public_reference(
                slot["accessibility"]["report"], resources, f"{field}.accessibility.report"
            )

    if actual_routes != expected_routes:
        missing = sorted(expected_routes.keys() - actual_routes.keys())
        extra = sorted(actual_routes.keys() - expected_routes.keys())
        mismatched = sorted(
            path
            for path in expected_routes.keys() & actual_routes.keys()
            if expected_routes[path] != actual_routes[path]
        )
        raise ContractError(
            "site catalog route registry disagrees with slots/resources "
            f"(missing={missing}, extra={extra}, mismatched={mismatched})"
        )
    for route_id, kinds in route_ids.items():
        if len(kinds) > 1 and not (
            kinds.count("artifact") == 1
            and len(kinds) > 1
            and all(kind in {"artifact", "artifact-alias"} for kind in kinds)
        ):
            raise ContractError(f"site catalog route id collision: {route_id}")
        if "artifact-alias" in kinds and "artifact" not in kinds:
            raise ContractError(f"artifact alias route lacks its canonical artifact: {route_id}")
    if (has_available_slot or require_deployable_revision) and not FULL_REVISION.fullmatch(
        revision
    ):
        raise ContractError("available or deployable site catalog requires a full revision")

    manifest = read_json(site_directory / "manifest.webmanifest")
    _validate_keys(
        manifest,
        required={
            "name",
            "short_name",
            "description",
            "id",
            "start_url",
            "scope",
            "display",
            "background_color",
            "theme_color",
        },
        optional={"icons"},
        field="manifest.webmanifest",
    )
    if manifest["id"] != "./" or manifest["start_url"] != "./" or manifest["scope"] != "./":
        raise ContractError("manifest.webmanifest is not repository-subpath safe")
    if manifest["display"] != "standalone":
        raise ContractError("manifest.webmanifest display contract is invalid")
    for icon_index, icon_value in enumerate(manifest.get("icons", [])):
        icon_field = f"manifest.icons[{icon_index}]"
        icon = _mapping(icon_value, icon_field)
        _validate_keys(
            icon,
            required={"src", "type", "sizes"},
            optional=set(),
            field=icon_field,
        )
        source_value = _string(icon["src"], f"{icon_field}.src")
        if not source_value.startswith("./"):
            raise ContractError("manifest icon source must be relative")
        _, icon_path = _public_file(site_directory, source_value[2:], f"{icon_field}.src")
        if not icon_path.is_file() or icon_path.is_symlink():
            raise ContractError("manifest icon is not staged")


def validate_output(
    output_root: Path,
    *,
    require_deployable_revision: bool = False,
    expected_catalog: dict[str, Any] | None = None,
) -> None:
    """Validate ownership, public metadata, links, resources, and checksums."""
    output_root = output_root.resolve(strict=True)
    marker = output_root / OWNERSHIP_MARKER
    if not marker.is_file() or marker.is_symlink():
        raise ContractError(f"unowned publication-hub output: {output_root}")
    if marker.read_text(encoding="utf-8") != OWNERSHIP_VALUE:
        raise ContractError(f"invalid publication-hub ownership marker: {marker}")
    site_directory = output_root / "site"
    if not site_directory.is_dir() or site_directory.is_symlink():
        raise ContractError(f"missing public site directory: {site_directory}")
    validate_public_catalog(
        site_directory, require_deployable_revision=require_deployable_revision
    )
    if expected_catalog is not None:
        public = read_json(site_directory / "site.json")
        expected_site = expected_catalog["site"]
        expected = {
            "catalog_sha256": expected_catalog["catalog_sha256"],
            "revision": expected_site["revision"],
            "theme": expected_site["theme"],
            "id": expected_site["id"],
            "canonical_base_url": expected_site["canonical_base_url"],
            "fallback_base_url": expected_site["fallback_base_url"],
        }
        actual = {
            "catalog_sha256": public["source"]["catalog_sha256"],
            "revision": public["source"]["revision"],
            "theme": public["site"]["theme"],
            "id": public["site"]["id"],
            "canonical_base_url": public["site"]["canonical_base_url"],
            "fallback_base_url": public["site"]["fallback_base_url"],
        }
        if actual != expected:
            raise ContractError(
                "staged publication hub does not match the current source catalog, "
                "effective theme, or source revision"
            )
    validate_html_links(site_directory)
    validate_checksums(site_directory)


def _resolve_output(project: Path, output: Path) -> Path:
    output = output.expanduser()
    if not output.is_absolute():
        output = project / output
    output = Path(os.path.abspath(output))
    if output in {Path("/"), project} or project not in output.parents:
        raise ContractError(f"output must be a child of the project: {output}")
    current = project
    relative = output.relative_to(project)
    for segment in relative.parts:
        current /= segment
        if current.exists() and current.is_symlink():
            raise ContractError(f"output cannot traverse a symlink: {output}")
    return output


def _is_owned_output(output: Path) -> bool:
    marker = output / OWNERSHIP_MARKER
    return (
        marker.is_file()
        and not marker.is_symlink()
        and marker.read_text(encoding="utf-8") == OWNERSHIP_VALUE
    )


def build_project(
    project: Path,
    output: Path,
    theme: str | None = None,
    source_revision: str | None = None,
    *,
    require_deployable_revision: bool = False,
) -> Path:
    """Build in a sibling workspace and atomically replace only owned output."""
    project = project.resolve(strict=True)
    output = _resolve_output(project, output)
    if output.exists() and (not output.is_dir() or not _is_owned_output(output)):
        raise ContractError(f"refusing to replace unowned output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".publication-hub-build-", dir=output.parent))
    backup: Path | None = None
    try:
        catalog = load_catalog(
            project,
            theme,
            source_revision,
            require_deployable_revision=require_deployable_revision,
        )
        for source_path in catalog_source_paths(catalog):
            if source_path == output or output in source_path.parents:
                raise ContractError(
                    f"publication source cannot depend on generated output: {source_path}"
                )
        render_site(catalog, temporary)
        validate_output(
            temporary,
            require_deployable_revision=require_deployable_revision,
            expected_catalog=catalog,
        )
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix=".publication-hub-backup-", dir=output.parent))
            backup.rmdir()
            os.replace(output, backup)
        try:
            os.replace(temporary, output)
        except BaseException:
            if backup is not None and backup.exists() and not output.exists():
                os.replace(backup, output)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
            backup = None
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        if backup is not None and backup.exists():
            if not output.exists():
                os.replace(backup, output)
            else:
                shutil.rmtree(backup)
    return output


def clean_output(project: Path, output: Path) -> None:
    """Remove only a child output carrying the exact ownership marker."""
    project = project.resolve(strict=True)
    output = _resolve_output(project, output)
    if not output.exists():
        return
    if not output.is_dir() or not _is_owned_output(output):
        raise ContractError(f"refusing to clean unowned output: {output}")
    shutil.rmtree(output)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "validate"))
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--theme", choices=sorted(THEMES))
    parser.add_argument("--source-revision")
    parser.add_argument(
        "--revision-policy", choices=("local", "deployment"), default="local"
    )
    return parser.parse_args()


def main() -> int:
    """Run the direct product-owned build or validation adapter."""
    arguments = _parse_arguments()
    project = Path(arguments.project)
    output = Path(arguments.output)
    require_deployable = arguments.revision_policy == "deployment"
    if arguments.command == "build":
        built = build_project(
            project,
            output,
            arguments.theme,
            arguments.source_revision,
            require_deployable_revision=require_deployable,
        )
        print(f"Built publication hub at {built / 'site'}")
    else:
        if not output.is_absolute():
            output = project / output
        validate_output(output, require_deployable_revision=require_deployable)
        print(f"Validated publication hub at {output / 'site'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as error:
        raise SystemExit(f"ERROR: {error}") from error
