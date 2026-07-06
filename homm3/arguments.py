from typing import Any

from homm3.values import Value
from homm3.filters import filter_from_str, Filter
from homm3.enums import AttackType, SpellMastery


ARGUMENTS = {}


def register_argument(name: str):
    def decorator(cls: type["Argument"]):
        ARGUMENTS[name] = cls
        return cls
    return decorator


def argument_class(spec: Any) -> type["Argument"] | type:
    if isinstance(spec, str):
        if spec not in ARGUMENTS:
            raise ValueError(f"Unknown argument type: {spec}!")
        return ARGUMENTS[spec]
    return spec


def parse_argument(value: Any, spec: Any) -> Any:
    cls = argument_class(spec)
    if isinstance(cls, type) and issubclass(cls, Argument):
        return cls.parse(value)
    if not isinstance(value, cls):
        expected = getattr(cls, "__name__", str(cls))
        actual = type(value).__name__
        raise TypeError(f"Expected {expected}, got {actual}")
    return value


def validate_argument(value: Any, spec: Any) -> Any:
    cls = argument_class(spec)
    if isinstance(cls, type) and issubclass(cls, Argument):
        return cls.validate(value)
    if not isinstance(value, cls):
        expected = getattr(cls, "__name__", str(cls))
        actual = type(value).__name__
        raise TypeError(f"Expected {expected}, got {actual}")
    return value


class Argument:
    @staticmethod
    def parse(value: Any) -> Any:
        return value


@register_argument("Value")
class ValueArgument(Argument):
    @staticmethod
    def parse(value: Any) -> Value:
        if isinstance(value, Value):
            return value
        raise TypeError(f"Expected Value, got {type(value).__name__}!")


@register_argument("Int")
class IntArgument(Argument):
    @staticmethod
    def parse(value: Any) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value)
        raise TypeError(f"Expected int-compatible value, got {type(value).__name__}!")


@register_argument("Float")
class FloatArgument(Argument):
    @staticmethod
    def parse(value: Any) -> float:
        if isinstance(value, float | int):
            return float(value)
        if isinstance(value, str):
            return float(value)
        raise TypeError(f"Expected float-compatible value, got {type(value).__name__}!")


@register_argument("Str")
class StrArgument(Argument):
    @staticmethod
    def parse(value: Any) -> str:
        if isinstance(value, str):
            return value
        raise TypeError(f"Expected str, got {type(value).__name__}!")


@register_argument("Bool")
class BoolArgument(Argument):
    @staticmethod
    def parse(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value == "True":
            return True
        if value == "False":
            return False
        raise TypeError(f"Expected bool, got {type(value).__name__}!")


@register_argument("Int|Str")
class IntOrStrArgument(Argument):
    @staticmethod
    def parse(value: Any) -> int | str:
        if isinstance(value, (int, str)):
            return value
        raise TypeError(f"Expected int or str, got {type(value).__name__}!")


@register_argument("ImmunityArg")
class ImmunityArgument(Argument):
    @staticmethod
    def parse(value: Any):
        if isinstance(value, Filter):
            return value

        if isinstance(value, str):
            parsed = filter_from_str(value)
            if parsed is not None:
                return parsed
            return value

        raise TypeError(f"Expected immunity argument, got {type(value).__name__}!")


@register_argument("Probability")
class ProbabilityArgument(Argument):
    @staticmethod
    def parse(value: Any) -> float:
        if isinstance(value, str):
            value = float(value)
        if not isinstance(value, (int, float)):
            raise TypeError(f"Expected probability, got {type(value).__name__}!")
        value = float(value)
        if value > 1:
            value /= 100
        if not 0 <= value <= 1:
            raise ValueError("Probability must be in [0, 1] or [0, 100]")
        return value


@register_argument("Effect")
class EffectArgument(Argument):
    @staticmethod
    def parse(value: Any):
        from homm3.effects import Effect, effect_from_str
        if isinstance(value, Effect):
            return value
        if isinstance(value, str):
            return effect_from_str(value)
        raise TypeError(f"Expected effect declaration, got {type(value).__name__}!")


@register_argument("AttackType")
class AttackTypeArgument(Argument):
    @staticmethod
    def parse(value: Any):
        if isinstance(value, AttackType):
            return value
        if value == "Shoot":
            return AttackType.Ranged
        if isinstance(value, str):
            return AttackType.from_str(value)
        raise TypeError(f"Expected attack type, got {type(value).__name__}!")


@register_argument("AttackTarget")
class AttackTargetArgument(Argument):
    values = {"Attacker", "Defender"}

    @classmethod
    def parse(cls, value: Any) -> str:
        if isinstance(value, str) and value in cls.values:
            return value
        raise ValueError(f"Expected target in {sorted(cls.values)}, got {value!r}")


@register_argument("AttackMoment")
class MomentArgument(Argument):
    values = {"Before", "After"}

    @classmethod
    def parse(cls, value: Any) -> str:
        if isinstance(value, str) and value in cls.values:
            return value
        raise ValueError(f"Expected moment in {sorted(cls.values)}, got {value!r}")


@register_argument("Mastery")
class SpellMasteryArgument(Argument):
    @staticmethod
    def parse(value: Any):
        if isinstance(value, SpellMastery):
            return value
        if isinstance(value, str):
            return SpellMastery.from_str(value)
        raise TypeError(f"Expected spell mastery or str, got {type(value).__name__}!")


@register_argument("DispelArg")
class DispelArgument(Argument):
    values = {"Positive", "Negative", "All"}

    @classmethod
    def parse(cls, value: Any) -> str:
        if isinstance(value, str) and value in cls.values:
            return value
        raise ValueError(f"Expected dispel mode in {sorted(cls.values)}, got {value!r}")
