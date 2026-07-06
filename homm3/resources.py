from collections import Counter

from bidict import bidict

from homm3.enums import Resource
from homm3.params import USE_EMOJI


RESOURCE_TO_EMOJI = bidict({
    Resource.Gold: "💰",
    Resource.Wood: "🟤",
    Resource.Ore: "⚫",
    Resource.Mercury: "🟠",
    Resource.Sulfur: "🟡",
    Resource.Crystal: "🔴",
    Resource.Gems: "🔵",
})

RESOURCE_TO_SYMBOL = bidict({
    Resource.Gold: "",
    Resource.Wood: "W",
    Resource.Ore: "O",
    Resource.Mercury: "M",
    Resource.Sulfur: "S",
    Resource.Crystal: "C",
    Resource.Gems: "G",
})


class ResourcePool:
    def __init__(self):
        self._counter = Counter()

    @staticmethod
    def from_resource(resource: Resource, count: int = 1) -> "ResourcePool":
        pool = ResourcePool()
        pool[resource] = count
        return pool

    @staticmethod
    def from_str(s: str) -> "ResourcePool":
        pool = ResourcePool()
        for item in s.replace(" ", "").upper().split(";"):
            try:
                if item[-1].isalpha():
                    res = RESOURCE_TO_SYMBOL.inverse[item[-1]]
                    pool[res] = int(item[:-1])
                else:
                    pool[Resource.Gold] = int(item)
            except Exception as e:
                raise ValueError(f"Cannot parse resource string '{s}' during creating resource pool!\nError:\n{e}")
        return pool

    def __to_str(self, use_emoji: bool) -> str:
        map_dict = RESOURCE_TO_EMOJI if use_emoji else RESOURCE_TO_SYMBOL
        resources = [str(count) + map_dict[res] for res, count in self._counter.items()]
        return "; ".join(resources)

    def __str__(self) -> str:
        return self.__to_str(USE_EMOJI)

    def __repr__(self) -> str:
        return self.__to_str(use_emoji=False)

    def __getitem__(self, item: Resource):
        return self._counter[item]

    def __setitem__(self, key: Resource, value: int):
        self._counter[key] = value
