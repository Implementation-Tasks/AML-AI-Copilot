"""
OpenSanctions API Client — generated from openapi.json (yente 5.4.0)
====================================================================
Source spec: src/tools/opensanctions_openapi.json

Endpoints implemented (from openapi.json paths):
  POST /match/{dataset}                          → match()
  GET  /search/{dataset}                         → search()
  GET  /entities/{entity_id}                     → get_entity()
  GET  /entities/{entity_id}/adjacent            → get_adjacent()
  GET  /entities/{entity_id}/adjacent/{prop}     → get_adjacent_by_property()
  GET  /statements                               → get_statements()
  GET  /catalog                                  → get_catalog()
  GET  /algorithms                               → get_algorithms()
  GET  /healthz                                  → health_check()

Authentication: Authorization: ApiKey <key>   (header-based, per spec)
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Typed result helpers (mirrors openapi.json components/schemas)
# ────────────────────────────────────────────────────────────────────────────

class ScoredEntity:
    """Maps to ScoredEntityResponse schema in openapi.json."""
    def __init__(self, raw: dict):
        self.id: str                  = raw.get("id", "")
        self.caption: str             = raw.get("caption", "")
        self.schema: str              = raw.get("schema", "")
        self.score: float             = raw.get("score", 0.0)
        self.match: bool              = raw.get("match", False)
        self.datasets: list[str]      = raw.get("datasets", [])
        self.topics: list[str]        = raw.get("properties", {}).get("topics", [])
        self.properties: dict         = raw.get("properties", {})
        self.explanations: dict       = raw.get("explanations", {})
        self.source_url: str = (
            f"https://www.opensanctions.org/entities/{self.id}" if self.id else ""
        )

    def __repr__(self):
        return f"<ScoredEntity id={self.id!r} caption={self.caption!r} score={self.score:.2f} match={self.match}>"


class MatchResult:
    """Maps to EntityMatches schema — one query's results."""
    def __init__(self, query_key: str, raw: dict):
        self.query_key  = query_key
        self.status: int            = raw.get("status", 200)
        self.results: list[ScoredEntity] = [
            ScoredEntity(r) for r in raw.get("results", [])
        ]
        self.total: int = raw.get("total", {}).get("value", 0)

    @property
    def has_matches(self) -> bool:
        return any(e.match for e in self.results)

    @property
    def best(self) -> Optional[ScoredEntity]:
        if not self.results:
            return None
        return max(self.results, key=lambda e: e.score)


# ────────────────────────────────────────────────────────────────────────────
# Main client
# ────────────────────────────────────────────────────────────────────────────

class OpenSanctionsClient:
    """
    Thin, typed wrapper around the OpenSanctions API (yente 5.4.0).
    All methods map 1-to-1 with paths in openapi.json.

    Usage:
        from src.tools.opensanctions_client import OpenSanctionsClient
        client = OpenSanctionsClient(api_key="your_key")
        results = client.match_person(name="Nguyen Van A", birth_date="1975-01-01")
    """

    BASE_URL = "https://api.opensanctions.org"

    def __init__(self, api_key: str, timeout: float = 15.0):
        if not api_key:
            raise ValueError("OPENSANCTIONS_API_KEY is required. Set it in .env")
        self._headers = {
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._timeout = timeout

    # ── Internal ──────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(url, headers=self._headers, params=params or {})
            resp.raise_for_status()
            return resp.json()

    def _post(self, path: str, body: dict, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                url, headers=self._headers, json=body, params=params or {}
            )
            resp.raise_for_status()
            return resp.json()

    # ── POST /match/{dataset} ─────────────────────────────────────────────

    def match(
        self,
        queries: dict[str, dict],
        dataset: str = "default",
        *,
        limit: int = 5,
        threshold: float = 0.7,
        algorithm: str = "best",
        topics: list[str] | None = None,
        exclude_schema: list[str] | None = None,
        weights: dict | None = None,
        config: dict | None = None,
    ) -> dict[str, MatchResult]:
        """
        POST /match/{dataset}

        Batch entity matching. queries dict keys are free-form labels,
        values must follow EntityExample schema from openapi.json:
          {
            "schema": "Person" | "Company" | "Organization" | ...,
            "properties": {"name": [...], "birthDate": [...], ...}
          }

        Returns: dict of label → MatchResult
        """
        body: dict[str, Any] = {"queries": queries}
        if weights:
            body["weights"] = weights
        if config:
            body["config"] = config

        params: dict[str, Any] = {
            "limit": limit,
            "threshold": threshold,
            "algorithm": algorithm,
        }
        if topics:
            params["topics"] = topics
        if exclude_schema:
            params["exclude_schema"] = exclude_schema

        raw = self._post(f"/match/{dataset}", body=body, params=params)
        return {
            key: MatchResult(key, val)
            for key, val in raw.get("responses", {}).items()
        }

    # ── Convenience wrappers around /match ───────────────────────────────

    def match_person(
        self,
        name: str,
        *,
        birth_date: str | None = None,
        nationality: str | None = None,
        id_number: str | None = None,
        address: str | None = None,
        dataset: str = "default",
        threshold: float = 0.7,
    ) -> MatchResult:
        """Screen a single natural person against the dataset."""
        props: dict[str, list] = {"name": [name]}
        if birth_date:
            props["birthDate"] = [birth_date]
        if nationality:
            props["nationality"] = [nationality]
        if id_number:
            props["idNumber"] = [id_number]
        if address:
            props["address"] = [address]

        results = self.match(
            queries={"person": {"schema": "Person", "properties": props}},
            dataset=dataset,
            threshold=threshold,
        )
        return results["person"]

    def match_company(
        self,
        name: str,
        *,
        jurisdiction: str | None = None,
        registration_number: str | None = None,
        address: str | None = None,
        incorporation_date: str | None = None,
        dataset: str = "default",
        threshold: float = 0.7,
    ) -> MatchResult:
        """Screen a single company against the dataset."""
        props: dict[str, list] = {"name": [name]}
        if jurisdiction:
            props["jurisdiction"] = [jurisdiction]
        if registration_number:
            props["registrationNumber"] = [registration_number]
        if address:
            props["address"] = [address]
        if incorporation_date:
            props["incorporationDate"] = [incorporation_date]

        results = self.match(
            queries={"company": {"schema": "Company", "properties": props}},
            dataset=dataset,
            threshold=threshold,
        )
        return results["company"]

    def match_wallet(
        self,
        wallet_address: str,
        dataset: str = "default",
        threshold: float = 0.6,
    ) -> MatchResult:
        """
        Screen a crypto wallet/address.
        Uses LegalEntity schema since wallets aren't Person or Company.
        """
        results = self.match(
            queries={
                "wallet": {
                    "schema": "LegalEntity",
                    "properties": {"name": [wallet_address]},
                }
            },
            dataset=dataset,
            threshold=threshold,
        )
        return results["wallet"]

    # ── GET /search/{dataset} ─────────────────────────────────────────────

    def search(
        self,
        q: str,
        dataset: str = "default",
        *,
        schema: str = "Thing",
        countries: list[str] | None = None,
        topics: list[str] | None = None,
        limit: int = 10,
        offset: int = 0,
        fuzzy: bool = False,
        facets: list[str] | None = None,
    ) -> dict:
        """
        GET /search/{dataset}

        Simple text search. Good for user-facing search boxes.
        For precise AML screening, use match() instead.

        Returns: SearchResponse (see openapi.json SearchResponse schema)
        """
        params: dict[str, Any] = {
            "q": q,
            "schema": schema,
            "limit": limit,
            "offset": offset,
            "fuzzy": fuzzy,
        }
        if countries:
            params["countries"] = countries
        if topics:
            params["topics"] = topics
        if facets:
            params["facets"] = facets

        return self._get(f"/search/{dataset}", params=params)

    # ── GET /entities/{entity_id} ─────────────────────────────────────────

    def get_entity(self, entity_id: str, nested: bool = True) -> dict:
        """
        GET /entities/{entity_id}

        Retrieve full entity record by ID.
        nested=True includes adjacent entities (passports, sanctions, family).
        Follows HTTP 308 redirects automatically (merged entities).
        """
        return self._get(f"/entities/{entity_id}", params={"nested": nested})

    # ── GET /entities/{entity_id}/adjacent ───────────────────────────────

    def get_adjacent(
        self,
        entity_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """
        GET /entities/{entity_id}/adjacent  (Beta)

        Paginated adjacent entities for a given entity.
        Returns: EntityAdjacentResponse
        """
        return self._get(
            f"/entities/{entity_id}/adjacent",
            params={"limit": limit, "offset": offset},
        )

    # ── GET /entities/{entity_id}/adjacent/{property_name} ───────────────

    def get_adjacent_by_property(
        self,
        entity_id: str,
        property_name: str,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """
        GET /entities/{entity_id}/adjacent/{property_name}  (Beta)

        Paginated results for a single adjacency property.
        Examples for property_name: "address", "ownershipOwner"
        """
        return self._get(
            f"/entities/{entity_id}/adjacent/{property_name}",
            params={"limit": limit, "offset": offset},
        )

    # ── GET /statements ───────────────────────────────────────────────────

    def get_statements(
        self,
        *,
        dataset: str | None = None,
        entity_id: str | None = None,
        canonical_id: str | None = None,
        prop: str | None = None,
        value: str | None = None,
        schema: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """
        GET /statements

        Raw statement-level access. Free to use (no billing).
        Useful to trace which source dataset made a specific claim.
        Returns: StatementResponse
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if dataset:
            params["dataset"] = dataset
        if entity_id:
            params["entity_id"] = entity_id
        if canonical_id:
            params["canonical_id"] = canonical_id
        if prop:
            params["prop"] = prop
        if value:
            params["value"] = value
        if schema:
            params["schema"] = schema

        return self._get("/statements", params=params)

    # ── GET /catalog ──────────────────────────────────────────────────────

    def get_catalog(self) -> dict:
        """
        GET /catalog

        Returns all indexed datasets with metadata.
        Useful to see which sanctions lists are currently loaded.
        """
        return self._get("/catalog")

    # ── GET /algorithms ───────────────────────────────────────────────────

    def get_algorithms(self) -> dict:
        """
        GET /algorithms

        Returns supported scoring algorithms and their feature weights.
        Options: logic-v2 (best), name-based, name-qualified, logic-v1, regression-v1
        """
        return self._get("/algorithms")

    # ── GET /healthz ──────────────────────────────────────────────────────

    def health_check(self) -> bool:
        """GET /healthz — returns True if service is up."""
        try:
            resp = self._get("/healthz")
            return resp.get("status") == "ok"
        except Exception:
            return False
