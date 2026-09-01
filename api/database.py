"""SQLite persistence for imported recipes."""

import json
import os
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(
    os.getenv("RECIPES_DATABASE_PATH", Path(__file__).parent / "recipes.db")
)


def initialize_database() -> None:
    """Create the recipe table when the application starts for the first time."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_author TEXT,
                source_platform TEXT,
                recipe_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def save_recipe(recipe: dict) -> int:
    """Store a complete recipe document and return its generated identifier."""
    source = recipe["source"]
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT INTO recipes (
                title, source_url, source_author, source_platform, recipe_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                recipe["title"],
                source["url"],
                source.get("author"),
                source.get("platform"),
                json.dumps(recipe, ensure_ascii=False),
            ),
        )
    return int(cursor.lastrowid)


def list_recipes() -> list[dict]:
    """Return saved recipes from newest to oldest."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT id, recipe_json, created_at
            FROM recipes
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        {"id": row[0], "recipe": json.loads(row[1]), "created_at": row[2]}
        for row in rows
    ]


def get_recipe(recipe_id: int) -> dict | None:
    """Return one saved recipe, or None when its ID does not exist."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT id, recipe_json, created_at FROM recipes WHERE id = ?", (recipe_id,)
        ).fetchone()

    if row is None:
        return None
    return {"id": row[0], "recipe": json.loads(row[1]), "created_at": row[2]}


def update_recipe(recipe_id: int, recipe: dict) -> bool:
    """Replace a saved recipe and keep searchable columns in sync."""
    source = recipe["source"]
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE recipes
            SET title = ?, source_url = ?, source_author = ?, source_platform = ?,
                recipe_json = ?
            WHERE id = ?
            """,
            (
                recipe["title"],
                source["url"],
                source.get("author"),
                source.get("platform"),
                json.dumps(recipe, ensure_ascii=False),
                recipe_id,
            ),
        )
    return cursor.rowcount == 1
