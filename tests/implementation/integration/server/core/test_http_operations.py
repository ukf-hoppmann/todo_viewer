from fastapi import FastAPI
from starlette.testclient import TestClient


def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_health(app: FastAPI) -> None:
    with client(app) as c:
        r = c.get("/api/core/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    assert r.headers["x-request-id"]


def test_request_id_from_client_is_kept_and_bad_ones_replaced(app: FastAPI) -> None:
    with client(app) as c:
        assert c.get("/api/core/health", headers={"X-Request-ID": "abc-1"}).headers["x-request-id"] == "abc-1"
        assert c.get("/api/core/health", headers={"X-Request-ID": "bad id!"}).headers["x-request-id"] != "bad id!"


def test_get_operation_reads_query_parameters(app: FastAPI) -> None:
    with client(app) as c:
        assert c.get("/api/example/greet", params={"name": "Ada"}).json() == {"text": "Hallo Ada"}
        assert c.get("/api/example/greet", params={"name": "Ada", "shout": "true"}).json() == {"text": "HALLO ADA"}


def test_list_output(app: FastAPI) -> None:
    with client(app) as c:
        assert c.get("/api/example/items").json() == [{"uid": "i1", "title": "Erstes", "version": 1}]


def test_write_operation_combines_path_and_body(app: FastAPI) -> None:
    with client(app) as c:
        r = c.put("/api/example/items/i1", json={"title": "Neu", "version": 1})
        assert r.status_code == 200 and r.json() == {"uid": "i1", "title": "Neu", "version": 2}
        assert c.get("/api/example/items").json()[0]["title"] == "Neu"


def test_domain_errors_have_code_message_details(app: FastAPI) -> None:
    with client(app) as c:
        missing = c.put("/api/example/items/zzz", json={"title": "x", "version": 1})
        conflict = c.put("/api/example/items/i1", json={"title": "x", "version": 99})
    assert missing.status_code == 404
    assert missing.json() == {"code": "not_found", "message": "Item zzz gibt es nicht", "details": {"uid": "zzz"}}
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "version_conflict" and conflict.json()["details"] == {"current": 1}


def test_invalid_request_uses_the_error_format(app: FastAPI) -> None:
    with client(app) as c:
        r = c.get("/api/example/greet")
        body_r = c.put("/api/example/items/i1", json={"title": "x"})
    for response in (r, body_r):
        assert response.status_code == 422
        assert response.json()["code"] == "validation_error"
        assert response.json()["details"]["errors"]


def test_unknown_route_and_wrong_method_use_the_error_format(app: FastAPI) -> None:
    with client(app) as c:
        assert c.get("/api/example/nope").json()["code"] == "not_found"
        r = c.post("/api/example/greet")
    assert r.status_code == 405 and r.json()["code"] == "method_not_allowed"


def test_unexpected_exception_becomes_internal_error_without_leaking(app: FastAPI) -> None:
    with client(app) as c:
        r = c.get("/api/example/crash")
    assert r.status_code == 500
    assert r.json() == {"code": "internal_error", "message": "Interner Fehler", "details": {}}


def test_openapi_lists_operations_with_schemas_and_error_format(app: FastAPI) -> None:
    with client(app) as c:
        schema = c.get("/openapi.json").json()
    paths = schema["paths"]
    assert {"/api/core/health", "/api/core/events", "/api/example/greet", "/api/example/items/{uid}"} <= set(paths)
    greet = paths["/api/example/greet"]["get"]
    assert greet["summary"] == "Grüßt jemanden" and greet["operationId"] == "example_greet"
    assert {p["name"] for p in greet["parameters"]} == {"name", "shout"}
    put = paths["/api/example/items/{uid}"]["put"]
    body_ref = put["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    body = schema["components"]["schemas"][body_ref.rsplit("/", 1)[1]]
    assert set(body["properties"]) == {"title", "version", "tags"} and set(body["required"]) == {"title", "version"}
    assert put["responses"]["4XX"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorBody"
    }
    assert "422" not in put["responses"]
    assert "HTTPValidationError" not in schema["components"]["schemas"]
    assert set(schema["components"]["schemas"]["ErrorBody"]["properties"]) == {"code", "message", "details"}
