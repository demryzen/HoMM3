from homm3.units import Stack


class TurnQueue:
    def __init__(self):
        self.active = []
        self.waiting = []
        self.waited = set()
        self.current_id = None

    def start_round(self, stacks: list[Stack]):
        ordered = sorted(stacks, key=lambda stack: (-stack.speed_base, stack.id))
        self.active = [stack.id for stack in ordered if not stack.is_died()]
        self.waiting = []
        self.waited = set()
        self.current_id = None

    def next(self) -> str | None:
        if self.active:
            self.current_id = self.active.pop(0)
            return self.current_id
        if self.waiting:
            self.current_id = self.waiting.pop(0)
            return self.current_id
        self.current_id = None
        return None

    def wait(self, stack_id: str):
        if stack_id in self.waited:
            raise ValueError("Stack cannot wait twice")
        self.waiting.insert(0, stack_id)
        self.waited.add(stack_id)

    def has_waited(self, stack_id: str) -> bool:
        return stack_id in self.waited

    def remove(self, stack_id: str):
        self.active = [item for item in self.active if item != stack_id]
        self.waiting = [item for item in self.waiting if item != stack_id]