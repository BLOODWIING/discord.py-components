from discord import Message
from typing import List, Union, Iterable

from .component import Component


class ComponentMessage(Message):
    def __init__(self, *, components: List[Union[Component, List[Component]]] = [], **kwargs):
        super().__init__(**kwargs)
        self.components = components

    def _get_button_events(self):
        return ComponentMessage._get_obj_button_events(self.components)

    @staticmethod
    def _get_obj_button_events(components):
        if not isinstance(components, list):
            return {}
        button_events = {}
        for c in components:
            if isinstance(c, Iterable):
                for cc in c:
                    if cc.event is not None:
                        button_events[cc.id] = cc.event
            else:
                if c.event is not None:
                    button_events[c.id] = c.event
        return button_events
