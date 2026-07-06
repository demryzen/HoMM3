from typing import Any

from homm3.arguments import parse_argument


class Parametrized:
    name = "Parametrized"
    main_schema: dict[str, Any] = {}
    secondary_schema: dict[str, Any] = {}
    default_params: dict[str, Any] = {}
    priority: int | None = None

    def __init__(self, params: dict[str, Any] | None = None):
        merged = {}
        merged.update(self.default_params)
        merged.update(params or {})
        self.params = merged

        for name in self.schema:
            if name not in self.params:
                raise ValueError(f"Missing param {self.name}.{name}!")

        for name, value in list(self.params.items()):
            if name not in self.schema:
                raise ValueError(f"Unknown param {self.name}.{name}!")
            self.params[name] = parse_argument(value, self.schema[name])

    @property
    def schema(self) -> dict[str, Any]:
        return self.main_schema | self.secondary_schema

    @classmethod
    def from_params(cls, params: dict[str, Any] | None = None):
        return cls(params=params)

    def __getitem__(self, name: str) -> Any:
        return self.params[name]

    def __str__(self) -> str:
        values = []
        for name in self.main_schema:
            if name in self.params:
                values.append(f"{name}={self.params[name]}")
        if not values:
            return self.name
        return f"{self.name}({', '.join(values)})"
