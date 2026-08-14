"""Moderator package — the Claude-backed decision cycle.

T4 lands the structured-output contract (`schema.Decision`) and the SDK wrapper
(`client.decide`). The constitution / system prompt, the decision-cycle
orchestration, and structured-state read/update are T5.

Kept import-light on purpose: `schema` needs only pydantic, while `client`
pulls in the `anthropic` SDK. Importing this package does **not** import
`client`, so `import app.moderator` stays cheap and works without the SDK
installed (e.g. app boot before T5 wires the moderator).
"""
