from homm3.enums import EffectType, EffectDomain, EffectElement, UnitEntity
from homm3.registry import parse_string


class Filter:
    name = "Filter"

    def matches(self, target) -> bool:
        return False


class SpellFilter(Filter):
    name = "Spell"

    def __init__(
        self,
        levels: list[int] | None = None,
        domains: list[EffectDomain] | None = None,
        elements: list[EffectElement] | None = None,
    ):
        self.levels = set(levels or [])
        self.domains = set(domains or [])
        self.elements = set(elements or [])

    @classmethod
    def from_args(cls, args: list):
        levels = []
        domains = []
        elements = []

        for item in args:
            if isinstance(item, int):
                levels.append(item)
                continue

            domain = getattr(EffectDomain, str(item), None)
            if domain is not None:
                domains.append(domain)
                continue

            element = getattr(EffectElement, str(item), None)
            if element is not None:
                elements.append(element)
                continue

            raise ValueError(f"Unknown Spell filter argument: {item}")

        return cls(levels=levels, domains=domains, elements=elements)

    def matches(self, effect) -> bool:
        if effect.effect_type != EffectType.Magical:
            return False

        if self.levels:
            if getattr(effect, "ignore_spell_level_immunity", False):
                if (not self.domains) and (not self.elements):
                    return False
            elif effect.level not in self.levels:
                return False

        if self.domains and not any(domain in self.domains for domain in effect.domains):
            return False

        if self.elements and effect.element not in self.elements:
            return False

        return True

    def __str__(self):
        args = [str(level) for level in sorted(self.levels)]
        args += [domain.name for domain in sorted(self.domains, key=lambda x: x.name)]
        args += [element.name for element in sorted(self.elements, key=lambda x: x.name)]
        return f"{self.name}({','.join(args)})"


class EntityFilter(Filter):
    name = "Entity"

    def __init__(self, entities):
        self.entities = set(entities)

    @classmethod
    def from_args(cls, args: list):
        entities = []
        for item in args:
            entity = getattr(UnitEntity, str(item), None)
            if entity is None:
                raise ValueError(f"Unknown Entity filter argument: {item}")
            entities.append(entity)
        return cls(entities)

    def matches(self, stack) -> bool:
        return stack.unit.entity in self.entities


FILTERS = {
    "Spells": SpellFilter,
    "Entity": EntityFilter,
}


def filter_from_str(text: str) -> Filter | None:
    name, args = parse_string(text)
    cls = FILTERS.get(name)
    if cls is None:
        return None
    return cls.from_args(args)