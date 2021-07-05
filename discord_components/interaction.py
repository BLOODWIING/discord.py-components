from discord import User, Client, Embed, AllowedMentions, InvalidArgument, Message
from discord.ext.commands import Bot
from discord.http import Route

from aiohttp import FormData
from typing import List, Union, Iterable
from json import dumps

from .button import Button
from .message import ComponentMessage
from .component import Component


__all__ = ("Interaction", "InteractionType", "InteractionEventType", "FlagsType", "ButtonEvent", "TimeoutEvent")


InteractionEventType = {"button_click": 2, "select_option": 3}


class InteractionType:
    Pong: int = 1
    ChannelMessageWithSource: int = 4
    DeferredChannelMessageWithSource: int = 5
    DeferredUpdateMessage: int = 6
    UpdateMessage: int = 7


class FlagsType:
    Crossposted: int = 1 << 0
    Is_crosspost: int = 1 << 1
    Suppress_embeds: int = 1 << 2
    Source_message_deleted: int = 1 << 3
    Urgent: int = 1 << 4
    Ephemeral: int = 1 << 6
    Loading: int = 1 << 7


class Interaction:
    def __init__(
        self,
        *,
        bot: Union[Client, Bot],
        client: "DiscordComponents",
        user: User = None,
        component: Component,
        raw_data: dict,
        message: ComponentMessage = None,
        is_ephemeral: bool = False,
    ):
        self.bot = bot
        self.client = client

        self.user = user
        self.author = self.user

        self.component = component
        self.raw_data = raw_data
        self.is_ephemeral = is_ephemeral
        self.responded = False

        self.message = message
        self.channel = message.channel if message else None
        self.guild = message.guild if message else None

        self.interaction_id = raw_data["d"]["id"]
        self.interaction_token = raw_data["d"]["token"]

    async def respond(
        self,
        *,
        type: int = InteractionType.ChannelMessageWithSource,
        content: str = None,
        embed: Embed = None,
        embeds: List[Embed] = None,
        allowed_mentions: AllowedMentions = None,
        tts: bool = False,
        ephemeral: bool = True,
        components: List[Union[Component, List[Component]]] = None,
        **options,
    ) -> None:
        state = self.bot._get_state()
        data = {
            **self.client._get_components_json(components),
            **options,
            "flags": FlagsType.Ephemeral if ephemeral else 0,
        }

        if content is not None:
            data["content"] = content

        if embed and embeds:
            embeds.append(embed)
        elif embed:
            embeds = [embed]

        if embeds:
            embeds = list(map(lambda x: x.to_dict(), embeds))
            if len(embeds) > 10:
                raise InvalidArgument("Embed limit exceeded. (Max: 10)")
            data["embeds"] = embeds

        if allowed_mentions:
            if state.allowed_mentions:
                allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()

            data["allowed_mentions"] = allowed_mentions

        if tts is not None:
            data["tts"] = tts

        self.responded = True
        await self.bot.http.request(
            Route("POST", f"/interactions/{self.interaction_id}/{self.interaction_token}/callback"),
            json={"type": type, "data": data},
        )


class ButtonEvent(Interaction):
    async def finish(self, *, auto_disable=False, auto_clear=False, run_timeout=False):
        if hasattr(self.bot, '_button_events') and self.message.id in self.bot._button_events:
            await self.client.remove_timeout(self.message, run_first=run_timeout)

            if auto_clear:
                await ButtonEvent.clear_buttons(self.client, self.message)

            elif auto_disable:
                await ButtonEvent.disable_buttons(self.client, self.message)

    def update_timeout(self, timeout: float):
        self.bot._button_events[self.message.id]['reset'] = timeout
        self.client.restart_timeout(self.message)

    @staticmethod
    async def clear_buttons(client: "DiscordComponents", message: Message):
        await client.edit_component_msg(
            message,
            None,
            components=[]
        )

    @staticmethod
    async def disable_buttons(client: "DiscordComponents", message: Message):
        for c in message.components:
            if isinstance(c, Iterable):
                for cc in c:
                    if isinstance(cc, Button):
                        cc.disabled = True
            if isinstance(c, Button):
                c.disabled = True
        await client.edit_component_msg(
            message,
            None,
            components=message.components
        )


class TimeoutEvent:
    def __init__(self, client: "DiscordComponents", message: Message):
        self.client = client
        self.message = message

    async def clear_buttons(self):
        await ButtonEvent.clear_buttons(self.client, self.message)

    async def disable_buttons(self):
        await ButtonEvent.disable_buttons(self.client, self.message)
