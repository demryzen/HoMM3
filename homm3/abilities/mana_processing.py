from homm3.abilities import Ability, register_ability


@register_ability
class MagicDampingAbility(Ability):
    name = "MagicDamping"
    main_schema = {
        "val": "Int",
    }


@register_ability
class MagicDrainAbility(Ability):
    name = "MagicDrain"
    main_schema = {
        "val": "Int",
    }


@register_ability
class MagicChannelAbility(Ability):
    name = "MagicChannel"
    main_schema = {
        "val": "Int",
    }


@register_ability
class MagicBracingAbility(Ability):
    name = "MagicBracing"
    main_schema = {
        "val": "Int",
    }