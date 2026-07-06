from abc import ABC, abstractmethod
from typing import Literal

import numpy as np


type ValueDataType = int | float
type ValueRoundMethod = Literal["ceil", "floor", "round", "no"]

BASE_VALUE_LABEL = "Base value"


class Expression(ABC):
    priority: int = 10

    def __init__(self, name: str | None = None):
        self.name = name
        self._parent = None

    @abstractmethod
    def total(self) -> ValueDataType:
        pass

    @abstractmethod
    def fmt(self, parent_priority: int = 0) -> str:
        pass

    def add(self, other: "Expression | ValueDataType") -> "Sum":
        old_parent = self._parent
        new_expr = Sum([self, _as_expression(other)], name=self.name)
        self.name = None
        if old_parent is not None:
            old_parent._replace_child(self, new_expr)
        return new_expr

    def mul(self, other: "Expression | ValueDataType") -> "Product":
        old_parent = self._parent
        new_expr = Product([self, _as_expression(other)], name=self.name)
        self.name = None
        if old_parent is not None:
            old_parent._replace_child(self, new_expr)
        return new_expr

    def apply(self, func: "Function") -> "Superposition":
        old_parent = self._parent
        new_expr = Superposition(self, func, name=self.name)
        self.name = None
        if old_parent is not None:
            old_parent._replace_child(self, new_expr)
        return new_expr

    def to_str(self, result: bool = False):
        s = self.fmt()
        if result:
            s = f"{fmt_value(self.total())} = {s}"
        return s

    def _replace_child(self, prev: "Expression", new: "Expression"):
        raise TypeError(f"{type(self).__name__} cannot replace children!")

    def __getitem__(self, name: str) -> "Expression | None":
        if self.name == name:
            return self
        return None

    def __str__(self) -> str:
        return self.to_str()

    def __add__(self, other: "Expression | ValueDataType") -> "Sum":
        return self.add(other)

    def __mul__(self, other: "Expression | ValueDataType") -> "Product":
        return self.mul(other)


class Term(Expression):
    priority: int = 100

    def __init__(
            self,
            value: ValueDataType,
            label: str | None = None,
            name: str | None = None
    ):
        super().__init__(name=name)
        self.value = value
        self.label = label

    def total(self) -> ValueDataType:
        return self.value

    def fmt(self, parent_priority: int = 0) -> str:
        value_str = fmt_value(self.value)
        if self.label is None:
            return value_str
        return f"{value_str} [{self.label}]"


class GroupedRandomValue(Expression):
    priority: int = 100

    def __init__(
            self,
            value_min: int,
            value_max: int,
            group_size: int,
            group_limit: int = 10,
            rng: np.random.Generator | None = None,
            label: str | None = None,
            name: str | None = None,
    ):
        super().__init__(name=name)

        self.value_min = value_min
        self.value_max = value_max
        self.group_size = group_size
        self.group_limit = group_limit
        self.label = label
        self.rng = np.random.default_rng() if rng is None else rng

        self.rnd_vals = self._generate()
        self.value = self._calculate_value()

    def _generate(self) -> np.ndarray:
        sample_size = min(self.group_size, self.group_limit)
        return self.rng.integers(
            self.value_min,
            self.value_max + 1,
            size=sample_size,
        )

    def _calculate_value(self) -> int:
        value = np.sum(self.rnd_vals)
        if self.group_size > self.group_limit:
            value = value * self.group_size / self.group_limit
            value = np.floor(value)
        return int(value)

    def total(self) -> ValueDataType:
        return self.value

    def fmt(self, parent_priority: int = 0) -> str:
        text = f"{self.group_size}xRandom({self.value_min},{self.value_max})"
        if self.label is not None:
            text += f" [{self.label}]"
        return text


class Group(Expression):
    def __init__(
            self,
            items: list[Expression | ValueDataType] | None = None,
            name: str | None = None
    ):
        super().__init__(name=name)
        self.items = [_as_expression(item) for item in (items or [])]
        for item in self.items:
            item._parent = self

    def apply(self, func: "Function") -> "Superposition":
        return super().apply(func)

    def _replace_child(self, prev: Expression, new: Expression):
        for i, item in enumerate(self.items):
            if item is prev:
                self.items[i] = new
                new._parent = self
                return
        raise ValueError("Child not found")

    def __getitem__(self, name: str) -> Expression | None:
        if self.name == name:
            return self
        for item in self.items:
            if (result := item[name]) is not None:
                return result
        return None


class Sum(Group):
    priority: int = 20

    def __init__(
            self,
            terms: list[Expression | ValueDataType] | None = None,
            name: str | None = None
    ):
        super().__init__(terms, name=name)

    @property
    def terms(self) -> list[Expression]:
        return self.items

    def add(self, term: Expression | ValueDataType) -> "Sum":
        term = _as_expression(term)
        term._parent = self
        self.items.append(term)
        return self

    def total(self) -> ValueDataType:
        return sum(term.total() for term in self.items)

    def fmt(self, parent_priority: int = 0) -> str:
        if len(self.terms) == 1:
            return self.terms[0].fmt(parent_priority)
        terms = []
        for i, term in enumerate(self.terms):
            term_str = term.fmt(self.priority)
            sign = "+"
            if (i == 0) or (isinstance(term, Term) and (term.value < 0)):
                sign = ""
            term_str = sign + term_str
            terms.append(term_str)
        text = " ".join(terms)
        return f"({text})" if self.priority < parent_priority else text


class Product(Group):
    priority: int = 30

    def __init__(
            self,
            factors: list[Expression | ValueDataType] | None = None,
            name: str | None = None
    ):  
        super().__init__(factors, name=name)

    @property
    def factors(self) -> list[Expression]:
        return self.items

    def mul(self, factor: Expression | ValueDataType) -> "Product":
        factor = _as_expression(factor)
        factor._parent = self
        self.items.append(factor)
        return self

    def total(self) -> ValueDataType:
        result = 1
        for factor in self.factors:
            if isinstance(factor, Group) and len(factor.items) == 0:
                continue
            result *= factor.total()
        return result

    def fmt(self, parent_priority: int = 0) -> str:
        factors = [
            factor for factor in self.items
            if not (isinstance(factor, Group) and len(factor.items) == 0)
        ]
        if len(factors) == 1:
            text = factors[0].fmt(0)
        else:
            text = " *".join(factor.fmt(self.priority) for factor in factors)
        return f"({text})" if self.priority < parent_priority else text

    def __getitem__(self, name: str) -> Expression | None:
        if self.name == name:
            return self
        for factor in self.factors:
            if (result := factor[name]) is not None:
                return result
        return None


class Function(ABC):
    def __init__(self, label: str | None = None):
        self.label = label

    @abstractmethod
    def __call__(self, x: ValueDataType) -> ValueDataType:
        pass

    @abstractmethod
    def fmt(self, x: str) -> str:
        pass


class Superposition(Expression):
    priority: int = 40

    def __init__(
            self,
            expression: Expression,
            func: Function,
            name: str | None = None
    ):
        super().__init__(name=name)
        self.func = func
        self.expression = expression
        self.expression._parent = self

    def total(self) -> ValueDataType:
        return self.func(self.expression.total())

    def fmt(self, parent_priority: int = 0) -> str:
        # inner = self.expression.fmt(self.priority)
        inner = self.expression.fmt(0)
        text = self.func.fmt(inner)
        return f"({text})" if self.priority < parent_priority else text

    def add(self, other: Expression | ValueDataType) -> "Superposition":
        target = self._inner_expression()
        target.add(other)
        return self

    def mul(self, other: Expression | ValueDataType) -> "Superposition":
        target = self._inner_expression()
        target.mul(other)
        return self

    def _inner_expression(self) -> Expression:
        expr = self.expression
        while isinstance(expr, Superposition):
            expr = expr.expression
        return expr

    def _replace_child(self, prev: Expression, new: Expression):
        if self.expression is prev:
            self.expression = new
            new._parent = self
            return
        raise ValueError("Child not found")

    def __getitem__(self, name: str) -> Expression | None:
        if self.name == name:
            return self
        return self.expression[name]


class Value(Expression):
    def __init__(
            self,
            base_value: Expression | ValueDataType,
            label: str | None = None,
            name: str | None = None,
            round_method: ValueRoundMethod = "no",
            min_value: ValueDataType | None = None,
            max_value: ValueDataType | None = None,
    ):
        super().__init__(name=None)
        if isinstance(base_value, Expression):
            self.expression = base_value
        else:
            label = BASE_VALUE_LABEL if label is None else label
            self.expression = Term(base_value, label=label, name=name)
        self.expression._parent = self
        self.round_method = round_method
        self.min_value = min_value
        self.max_value = max_value

    def add(self, other: Expression | ValueDataType) -> "Value":
        new_expr = Sum([self.expression, _as_expression(other)])
        self.expression = new_expr
        new_expr._parent = self
        return self

    def mul(self, other: Expression | ValueDataType) -> "Value":
        new_expr = Product([self.expression, _as_expression(other)])
        self.expression = new_expr
        new_expr._parent = self
        return self

    def apply(self, func: "Function") -> "Value":
        new_expr = Superposition(self.expression, func)
        self.expression = new_expr
        new_expr._parent = self
        return self

    def total(self) -> ValueDataType:
        value = round_value(self.expression.total(), self.round_method)
        if self.min_value is not None:
            value = max(self.min_value, value)
        if self.max_value is not None:
            value = min(self.max_value, value)
        return value

    def fmt(self, parent_priority: int = 0) -> str:
        return self.expression.fmt(parent_priority)

    def _replace_child(self, prev: Expression, new: Expression) -> None:
        if self.expression is prev:
            self.expression = new
            new._parent = self
            return
        raise ValueError("Child not found")

    def __getitem__(self, name: str) -> Expression | None:
        return self.expression[name]


def round_value(value: ValueDataType, round_method: ValueRoundMethod) -> ValueDataType:
    match round_method:
        case "ceil":
            return int(np.ceil(value))
        case "floor":
            return int(np.floor(value))
        case "round":
            return int(np.round(value))
        case "no":
            return value
        case _:
            raise ValueError(f"Unknown round method: '{round_method}'!")


def fmt_value(value: ValueDataType) -> str:
    if isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        return f"{value:.2f}"
    else:
        raise ValueError(f"Unsupported value type: {type(value)}!")


def _as_expression(value: Expression | ValueDataType) -> Expression:
    if isinstance(value, Expression):
        return value
    return Term(value)


class Pow(Function):
    def __init__(self, power: float | int, label: str | None = None):
        super().__init__(label=label)
        self.power = power

    def __call__(self, x: ValueDataType) -> ValueDataType:
        return x ** self.power

    def fmt(self, x: str) -> str:
        text = f"{x}^{fmt_value(self.power)}"
        return f"{text} [{self.label}]" if self.label is not None else text


class Linear(Function):
    def __init__(
            self,
            k: ValueDataType = 1,
            b: ValueDataType = 0,
            label: str | None = None,
    ):
        super().__init__(label=label)
        self.k = k
        self.b = b

    def __call__(self, x: ValueDataType) -> ValueDataType:
        return x * self.k + self.b

    def fmt(self, x: str) -> str:
        text = f"{x} *{fmt_value(self.k)}"
        if self.b > 0:
            text += f"+{fmt_value(self.b)}"
        elif self.b < 0:
            text += f"-{fmt_value(abs(self.b))}"
        return f"{text} [{self.label}]" if self.label is not None else text


class Floor(Function):
    def __call__(self, x):
        return int(np.floor(x))

    def fmt(self, x: str) -> str:
        if self.label is None:
            return f"⌊{x}⌋"
        return f"⌊{x}⌋ [{self.label}]"
