"""Cooperative cancellation with a serialized irreversible publication boundary."""
from __future__ import annotations

from threading import Event, Lock
from typing import Callable, TypeVar

from ._native import GeneWireError

T = TypeVar("T")


class Cancellation:
    """Thread-safe, one-way cancellation shared by one or more BAM operations.

    cancel() signals work to stop; operation completion still owns cleanup.
    A publication already admitted under this token is not rolled back.
    """

    def __init__(self) -> None:
        self._event = Event()
        self._lock = Lock()
        self._callbacks: dict[object, Callable[[], None]] = {}

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        with self._lock:
            if self.is_cancelled:
                return
            self._event.set()
            callbacks = tuple(self._callbacks.values())
            self._callbacks.clear()
        # Never hold the publication lock while invoking native cancellation.
        for callback in callbacks:
            try:
                callback()
            except GeneWireError:
                # The owning operation also observes the token and owns cleanup.
                pass

    def _check(self) -> None:
        if self.is_cancelled:
            raise GeneWireError("Cancelled")

    def _subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        key = object()
        with self._lock:
            cancelled = self.is_cancelled
            if not cancelled:
                self._callbacks[key] = callback
        if cancelled:
            callback()

        def unsubscribe() -> None:
            with self._lock:
                self._callbacks.pop(key, None)

        return unsubscribe

    def _commit(self, action: Callable[[], T]) -> T:
        with self._lock:
            self._check()
            return action()
