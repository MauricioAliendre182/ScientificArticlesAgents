"""Persistent exact-query cache for paper search results."""

import hashlib
import re
from typing import Any

from psycopg import AsyncConnection
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb

from ..models.paper import Paper
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PaperCacheService:
    """Read and write paper search results in PostgreSQL."""

    def __init__(self, config: dict[str, Any], max_age_days: int = 30):
        self.conninfo = make_conninfo(
            host=config["host"],
            port=config["port"],
            dbname=config["database"],
            user=config["user"],
            password=config["password"],
        )
        self.max_age_days = max_age_days

    async def get(self, query: str) -> list[Paper]:
        """Return fresh cached papers for a normalized exact query."""
        normalized_query = self.normalize_query(query)
        if not normalized_query:
            return []

        connection = await AsyncConnection.connect(self.conninfo, autocommit=True)
        try:
            await self._ensure_table(connection)
            cursor = await connection.execute(
                """SELECT papers
                   FROM paper_search_cache
                   WHERE query_key = %s
                     AND fetched_at >= NOW() - (%s * INTERVAL '1 day')""",
                (self.query_key(normalized_query), self.max_age_days),
            )
            row = await cursor.fetchone()
            if row is None:
                return []
            return [Paper.model_validate(item) for item in row[0]]
        finally:
            await connection.close()

    async def put(self, query: str, papers: list[Paper]) -> None:
        """Store non-empty search results, refreshing the cache age."""
        normalized_query = self.normalize_query(query)
        if not normalized_query or not papers:
            return

        payload = [paper.model_dump(mode="json") for paper in papers]
        connection = await AsyncConnection.connect(self.conninfo, autocommit=True)
        try:
            await self._ensure_table(connection)
            await connection.execute(
                """INSERT INTO paper_search_cache
                       (query_key, normalized_query, papers, fetched_at)
                   VALUES (%s, %s, %s, NOW())
                   ON CONFLICT (query_key) DO UPDATE SET
                       normalized_query = EXCLUDED.normalized_query,
                       papers = EXCLUDED.papers,
                       fetched_at = EXCLUDED.fetched_at""",
                (self.query_key(normalized_query), normalized_query, Jsonb(payload)),
            )
        finally:
            await connection.close()

    @staticmethod
    def normalize_query(query: str) -> str:
        """Normalize case and whitespace for predictable exact matching."""
        return re.sub(r"\s+", " ", query).strip().casefold()

    @staticmethod
    def query_key(normalized_query: str) -> str:
        return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()

    @staticmethod
    async def _ensure_table(connection: AsyncConnection) -> None:
        await connection.execute(
            """CREATE TABLE IF NOT EXISTS paper_search_cache (
                   query_key TEXT PRIMARY KEY,
                   normalized_query TEXT NOT NULL,
                   papers JSONB NOT NULL,
                   fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
               )"""
        )