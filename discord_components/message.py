from discord import Message
from typing import List, Union, Iterable

from .component import Component


class ComponentMessage(Message):
    def __init__(self, *, components: List[Union[Component, List[Component]]] = [], **kwargs):
        super().__init__(**kwargs)
        self.components = components

    def _get_button_events(self):
        if not isinstance(self.components, list):
            return {}
        button_events = {}
        for c in self.components:
            if isinstance(c, Iterable):
                for cc in c:
                    if cc.event is not None:
                        button_events[cc.id] = cc.event
            else:
                if c.event is not None:
                    button_events[c.id] = c.event
        return button_events
