from enum import Enum, auto


class HoMMEnum(Enum):
    def __str__(self) -> str:
        class_name = self.__class__.__name__
        return super().__str__().replace(f"{class_name}.", "")

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_str(cls, s: str) -> "HoMMEnum":
        return cls[s]


class Resource(HoMMEnum):
    Gold = auto()
    Wood = auto()
    Ore = auto()
    Mercury = auto()
    Sulfur = auto()
    Crystal = auto()
    Gems = auto()


class UnitHome(HoMMEnum):
    Castle = auto()
    Rampart = auto()
    Tower = auto()
    Inferno = auto()
    Necropolis = auto()
    Dungeon = auto()
    Stronghold = auto()
    Fortress = auto()
    Conflux = auto()
    Cove = auto()
    Factory = auto()
    Bulwark = auto()
    Neutral = auto()
    Cathedral = auto()


class UnitEntity(HoMMEnum):
    Living = auto()
    Bloodless = auto()
    Unliving = auto()
    Undead = auto()
    Mechanical = auto()


class UnitMovement(HoMMEnum):
    Ground = auto()
    Flying = auto()
    Underground = auto()
    Teleport = auto()


class UnitAction(HoMMEnum):
    Move = auto()
    Strike = auto()
    MoveAndStrike = auto()
    Shoot = auto()
    Defense = auto()
    Wait = auto()
    UseAbility = auto()


class Status(HoMMEnum):
    Neutral = auto()
    Positive = auto()
    Negative = auto()


class EffectType(HoMMEnum):
    Pure = auto()
    Physical = auto()
    Magical = auto()


class EffectElement(HoMMEnum):
    No = auto()
    Air = auto()
    Fire = auto()
    Water = auto()
    Earth = auto()


class EffectDomain(HoMMEnum):
    Mind = auto()
    Cold = auto()


class SpellMastery(HoMMEnum):
    No = auto()
    Basic = auto()
    Advanced = auto()
    Expert = auto()


class ActionType(HoMMEnum):
    Move = auto()
    Strike = auto()
    MoveAndStrike = auto()
    Shoot = auto()
    Defense = auto()
    Wait = auto()
    UseAbility = auto()


class AttackType(HoMMEnum):
    Melee = auto()
    Ranged = auto()
    Special = auto()


class AttackOrder(HoMMEnum):
    Regular = auto()
    Retaliation = auto()
    Preemptive = auto()
    Additional = auto()


class EventType(HoMMEnum):
    BattleStarted = auto()
    BattleEnded = auto()

    RoundStarted = auto()
    RoundEnded = auto()

    # TurnQueued = auto()
    TurnStarted = auto()
    TurnSkipped = auto()
    TurnEnded = auto()

    ActionSelected = auto()
    ActionStarted = auto()
    ActionEnded = auto()

    # MoveStarted = auto()
    StackMoved = auto()
    # MoveEnded = auto()
    #
    # AttackDeclared = auto()
    AttackStarted = auto()
    # AttackTargetsResolved = auto()
    AttackEnded = auto()
    #
    # RetaliationChecked = auto()
    # RetaliationStarted = auto()
    # RetaliationEnded = auto()
    #
    # DamageCalculationStarted = auto()
    # DamageCalculated = auto()
    # DamageApplying = auto()
    DamageApplied = auto()
    #
    # EffectApplying = auto()
    EffectApplied = auto()
    EffectBlocked = auto()
    #
    # StateApplying = auto()
    # StateApplied = auto()
    # StateProlonged = auto()
    # StateRemoved = auto()
    # StateExpired = auto()
    #
    StackHealed = auto()
    # StackResurrected = auto()
    StackDied = auto()
    StackWaited = auto()
    StackDefended = auto()
    StackReborn = auto()
    UnitsDied = auto()

    MoraleChecked = auto()
    GoodMoraleTriggered = auto()
    BadMoraleTriggered = auto()

    ShotsChanged = auto()
    RuneLevelIncreased = auto()

    StateApplied = auto()
    StateRemoved = auto()
    StateAlreadyExists = auto()
    StateProlonged = auto()
