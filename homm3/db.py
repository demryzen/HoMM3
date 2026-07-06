import sqlite3
from typing import Iterable

import pandas as pd

from homm3.params import DB_PATH


class DataBase:
    @staticmethod
    def request(request: str) -> pd.DataFrame:
        connect = sqlite3.connect(DB_PATH)
        cursor = connect.cursor()
        cursor.execute(request)
        records = cursor.fetchall()
        col_names = [x[0] for x in cursor.description]
        cursor.close()

        df = pd.DataFrame(columns=col_names)
        for i, row in enumerate(records):
            df.loc[i] = pd.Series(dict(zip(col_names, row)))
        return df

    @staticmethod
    def find_units(
        name: str | None = None,
        homes: Iterable[str] | str | None = None,
        exclude_homes: Iterable[str] | str | None = None,
        tiers: Iterable[int] | int | None = None,
        exclude_tiers: Iterable[int] | int | None = None,
        grades: Iterable[int] | int | None = None,
        exclude_grades: Iterable[int] | int | None = None,
        movements: Iterable[str] | str | None = None,
        exclude_movements: Iterable[str] | str | None = None,
        entities: Iterable[str] | str | None = None,
        exclude_entities: Iterable[str] | str | None = None,
        has_shots: bool | None = None,
        abilities: Iterable[str] | str | None = None,
        exclude_abilities: Iterable[str] | str | None = None,
        source_names: Iterable[str] | str | None = None,
        exclude_source_names: Iterable[str] | str | None = None,
        min_attack: int | None = None,
        max_attack: int | None = None,
        min_defense: int | None = None,
        max_defense: int | None = None,
        min_health: int | None = None,
        max_health: int | None = None,
        min_speed: int | None = None,
        max_speed: int | None = None,
        order_by: str = "home, tier, grade, name",
    ) -> pd.DataFrame:
        def as_list(value):
            if value is None:
                return None
            if isinstance(value, (str, int)):
                return [value]
            return list(value)

        def normalize_text_values(values):
            values = as_list(values)
            if values is None:
                return None
            return [str(value).lower() for value in values]

        def normalize_int_values(values):
            values = as_list(values)
            if values is None:
                return None
            return [int(value) for value in values]

        def add_in_filter(column: str, values, negate: bool = False, lower: bool = False):
            values = normalize_text_values(values) if lower else normalize_int_values(values)
            if not values:
                return

            placeholders = ", ".join(["?"] * len(values))
            op = "NOT IN" if negate else "IN"
            if lower:
                where.append(f"LOWER({column}) {op} ({placeholders})")
            else:
                where.append(f"{column} {op} ({placeholders})")
            params.extend(values)

        def add_range_filter(column: str, min_value: int | None = None, max_value: int | None = None):
            if min_value is not None:
                where.append(f"{column} >= ?")
                params.append(min_value)
            if max_value is not None:
                where.append(f"{column} <= ?")
                params.append(max_value)

        where = []
        params = []

        if name:
            where.append("LOWER(name) LIKE ?")
            params.append(f"%{name.lower()}%")

        add_in_filter("home", homes, lower=True)
        add_in_filter("home", exclude_homes, negate=True, lower=True)

        add_in_filter("tier", tiers)
        add_in_filter("tier", exclude_tiers, negate=True)

        add_in_filter("grade", grades)
        add_in_filter("grade", exclude_grades, negate=True)

        add_in_filter("movement", movements, lower=True)
        add_in_filter("movement", exclude_movements, negate=True, lower=True)

        add_in_filter("entity", entities, lower=True)
        add_in_filter("entity", exclude_entities, negate=True, lower=True)

        add_in_filter("source_name", source_names, lower=True)
        add_in_filter("source_name", exclude_source_names, negate=True, lower=True)

        if has_shots is True:
            where.append("shots > 0")
        elif has_shots is False:
            where.append("shots = 0")

        for ability in normalize_text_values(abilities) or []:
            where.append("LOWER(COALESCE(abilities, '')) LIKE ?")
            params.append(f"%{ability}%")

        for ability in normalize_text_values(exclude_abilities) or []:
            where.append("LOWER(COALESCE(abilities, '')) NOT LIKE ?")
            params.append(f"%{ability}%")

        add_range_filter("attack", min_attack, max_attack)
        add_range_filter("defense", min_defense, max_defense)
        add_range_filter("health", min_health, max_health)
        add_range_filter("speed", min_speed, max_speed)

        allowed_order_columns = {
            "name",
            "attack",
            "defense",
            "damage_min",
            "damage_max",
            "health",
            "speed",
            "growth",
            "size",
            "movement",
            "cost",
            "home",
            "shots",
            "entity",
            "abilities",
            "tier",
            "grade",
            "upgrade",
            "source_name",
            "source_version",
        }

        order_parts = []
        for part in order_by.split(","):
            part = part.strip()
            if not part:
                continue

            tokens = part.split()
            column = tokens[0]
            direction = tokens[1].upper() if len(tokens) > 1 else ""

            if column not in allowed_order_columns:
                raise ValueError(f"Unknown order_by column: {column}")

            if direction and direction not in {"ASC", "DESC"}:
                raise ValueError(f"Invalid order_by direction: {direction}")

            order_parts.append(f"{column} {direction}".strip())

        query = "SELECT * FROM Units"
        if where:
            query += " WHERE " + " AND ".join(where)
        if order_parts:
            query += " ORDER BY " + ", ".join(order_parts)

        connect = sqlite3.connect(DB_PATH)
        try:
            return pd.read_sql_query(query, connect, params=params)
        finally:
            connect.close()
