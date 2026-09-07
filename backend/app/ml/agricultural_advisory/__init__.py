"""Agricultural Advisory Engine.

A controlled decision-support layer that turns AI perception outputs (pest
detection, and — once integrated — disease detection), sensor/weather data,
and farm context into safe, explainable, source-traceable recommendations.

This is not a chatbot and does not use an LLM for decision-making. Every
recommendation is deterministic, traceable to a knowledge-base entry and an
authoritative agricultural source, and gated behind explicit safety checks.
See docs/AGRICULTURAL_ADVISORY.md for the full architecture.
"""
