import re
import pkgutil
import importlib
from typing import Any
from dataclasses import dataclass


def split_args(text: str) -> list[str]:
    result = []
    depth, start = 0, 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            result.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        result.append(tail)
    return result


def parse_value(value: str) -> Any:
    value = value.strip()

    if re.fullmatch(r"-?\d+", value):
        return int(value)

    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)

    if value == "True":
        return True

    if value == "False":
        return False

    if value == "None":
        return None

    return value


def parse_string(text: str) -> tuple[str, list[Any]]:
    text = text.strip()
    match = re.fullmatch(r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\((?P<args>.*)\))?", text)

    if match is None:
        raise ValueError(f"Invalid object declaration: {text}")

    name = match.group("name")
    args_text = match.group("args")

    if args_text is None or not args_text.strip():
        return name, []

    args = [parse_value(item) for item in split_args(args_text)]
    return name, args


@dataclass
class Registry:
    base_cls: type
    package_name: str
    object_name: str

    def __post_init__(self):
        self._items = {}
        self._loaded = False

    def register(self, cls: type | None = None, *, name: str | None = None, aliases: tuple[str, ...] = ()):

        def decorator(target_cls: type):
            if not issubclass(target_cls, self.base_cls):
                raise TypeError(
                    f"{target_cls.__name__} must inherit from {self.base_cls.__name__}"
                )

            item_name = name or getattr(target_cls, "name", target_cls.__name__)
            self._register_name(item_name, target_cls)

            class_aliases = getattr(target_cls, "aliases", ())
            for alias in (*class_aliases, *aliases):
                self._register_name(alias, target_cls)

            return target_cls

        if cls is None:
            return decorator

        return decorator(cls)

    def _register_name(self, name: str, cls: type):
        existing = self._items.get(name)
        if existing is not None and existing is not cls:
            raise ValueError(
                f"Duplicate {self.object_name} registration '{name}': "
                f"{existing.__name__} and {cls.__name__}!"
            )
        self._items[name] = cls

    def load_modules(self):
        if self._loaded:
            return
        package = importlib.import_module(self.package_name)

        if not hasattr(package, "__path__"):
            self._loaded = True
            return
        for module in pkgutil.iter_modules(package.__path__):
            if module.name.startswith("_"):
                continue
            importlib.import_module(f"{self.package_name}.{module.name}")
        self._loaded = True

    def get(self, name: str) -> type | None:
        self.load_modules()
        return self._items.get(name)

    def create(self, name: str, params: dict[str, Any] | None = None):
        cls = self.get(name)
        if cls is None:
            raise ValueError(f"Unknown {self.object_name}: {name}!")
        if hasattr(cls, "from_params"):
            return cls.from_params(params)
        return cls(params=params)

    def names(self) -> tuple[str, ...]:
        self.load_modules()
        return tuple(sorted(self._items))
