# Shared runtime protocol

This package defines the Universal Runtime Protocol used by every Appi device runtime.

- Request/response JSON schemas
- Capability names (support ≠ permission)
- Heartbeat payload shape
- `CAPABILITY_UNAVAILABLE` error code

The working desktop implementation lives in `apps/device-agent` and is launched by the Windows/Linux/macOS runtime entrypoints. Android and iOS runtimes in this milestone are architecture placeholders and must not pretend to execute device APIs.
