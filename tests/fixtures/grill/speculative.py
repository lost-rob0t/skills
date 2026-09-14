"""Flexible notification abstraction for future channels."""

from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, subject: str, body: str) -> None: ...


class ChannelRegistry:
    _channels: dict[str, type[NotificationChannel]] = {}

    @classmethod
    def register(cls, name: str, channel: type[NotificationChannel]) -> None:
        cls._channels[name] = channel

    @classmethod
    def resolve(cls, name: str) -> NotificationChannel:
        return cls._channels[name]()


class EmailChannel(NotificationChannel):
    def send(self, recipient: str, subject: str, body: str) -> None:
        print(f"email {recipient}: {subject}")
