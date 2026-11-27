"""Experimental encoded BAM streams. Successful transfer is not scientific proof."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Mapping, Sequence

from ._native import GeneWireError, NativeClient, NativeStream
from ._cancellation import Cancellation

__all__ = ["Cancellation", "Client", "Destination", "GeneWireError", "MemoryReport", "Report", "Stream"]
MAX_CHUNK = 256 * 1024


@dataclass(frozen=True)
class Destination:
    """Explicit IP allowlist for one origin; no implicit credential forwarding."""
    addresses: Sequence[str]
    allow_ticket_authorization: bool = False


@dataclass(frozen=True)
class MemoryReport:
    current_payload_bytes: int
    peak_payload_bytes: int
    largest_http_fragment_bytes: int
    rust_output_copy_bytes: int
    python_output_copy_bytes: int


@dataclass(frozen=True)
class Report:
    state: str
    bytes_delivered: int
    retries: int
    cleanup_complete: bool
    error: str | None
    phase: str
    may_have_partial_output: bool
    cleanup: str
    cleanup_error: str | None
    upstream_profile: str
    capability_evidence: str
    memory: MemoryReport
    output_kind: str = "UpstreamRegionalResponse"
    source_consistency: str = "Unverified"
    integrity: str = "TransportOnly"


def _report(snapshot: tuple) -> Report:
    return Report(*snapshot[:-1], MemoryReport(*snapshot[-1]))


class Client:
    def __init__(
        self,
        service: str,
        destinations: Mapping[str, Destination],
        *,
        control_token: str | None = None,
        loopback_http_for_tests: bool = False,
        timeout_ms: int = 600_000,
        result_bytes: int = 1024**3,
        upstream_profile: str = "HtsgetBamRegional",
        additional_ca_pem: bytes | None = None,
    ) -> None:
        if upstream_profile != "HtsgetBamRegional":
            raise GeneWireError("Unsupported")
        if additional_ca_pem is not None and (
            type(additional_ca_pem) is not bytes or not 0 < len(additional_ca_pem) <= 65536
        ):
            raise GeneWireError("InvalidQuery")
        for value in (timeout_ms, result_bytes):
            if type(value) is not int or not 0 < value <= 2**63 - 1:
                raise GeneWireError("InvalidQuery")
        self._native = NativeClient(
            service,
            [(origin, list(d.addresses), d.allow_ticket_authorization) for origin, d in destinations.items()],
            control_token,
            loopback_http_for_tests,
            (timeout_ms, result_bytes),
            additional_ca_pem,
        )
        # Bind local recovery receipts to the configured service without persisting it.
        self._service = service

    def open(self, object_id: str, reference: str, start: int, end: int) -> Stream:
        if any(type(n) is not int or not 0 <= n <= 2**32 - 1 for n in (start, end)):
            raise GeneWireError("InvalidQuery")
        return Stream(self._native.open(object_id, reference, start, end), (reference, start, end))

    def close(self) -> None:
        self._native.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _exit(self, exc)


class Stream:
    def __init__(self, native: NativeStream, region: tuple[str, int, int] | None = None) -> None:
        self._native = native
        self._region = region

    @property
    def region(self) -> tuple[str, int, int] | None:
        return self._region

    def read_chunk(self, max_bytes: int = MAX_CHUNK) -> bytes:
        if type(max_bytes) is not int or not 0 < max_bytes <= MAX_CHUNK:
            raise GeneWireError("InvalidQuery")
        return self._native.read_chunk(max_bytes)

    def iter_chunks(self, max_bytes: int = MAX_CHUNK) -> Iterator[bytes]:
        while chunk := self.read_chunk(max_bytes):
            yield chunk

    def result(self) -> Report:
        return _report(self._native.result())

    def finish(self) -> Report:
        return _report(self._native.finish())

    def cancel(self) -> None:
        self._native.cancel()

    def close(self) -> None:
        self._native.close()

    def __enter__(self) -> Stream:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _exit(self, exc)


def _exit(resource: Client | Stream, original: BaseException | None) -> None:
    try:
        resource.close()
    except GeneWireError as cleanup_error:
        if original is None:
            raise
        if hasattr(original, "add_note"):
            original.add_note(f"GeneWire cleanup failed: {cleanup_error}")
