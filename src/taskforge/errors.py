"""Actionable errors for rejected inputs and incomplete runs."""

from __future__ import annotations


class TaskForgeError(Exception):
    """A rejected input or an incomplete run, with a stable code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
