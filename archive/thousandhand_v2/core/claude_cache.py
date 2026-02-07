"""
Claude Response Cache - Caching layer for forecast simulations.

This module provides caching for Claude API calls to enable:
1. Replay mode: Re-run forecasts with different human inputs
2. Scenario mode: Monte Carlo simulations using cached responses
3. Cost savings: Avoid redundant API calls for identical requests

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    CACHE MODES                               │
    ├─────────────────────────────────────────────────────────────┤
    │  Mode        │ Description                                   │
    ├─────────────────────────────────────────────────────────────┤
    │  PASSTHROUGH │ Normal API calls, no caching                  │
    │  CAPTURE     │ Make API calls AND record to cache            │
    │  REPLAY      │ Use cached responses, no API calls            │
    │  MOCK        │ Use mock responses, no API calls              │
    └─────────────────────────────────────────────────────────────┘

Cache Key: sha256(model + messages + max_tokens + system)[:16]
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any, Protocol

logger = logging.getLogger("1kh.claude_cache")


# =============================================================================
# Cache Mode
# =============================================================================

class CacheMode(str, Enum):
    """Operating mode for the Claude cache."""
    PASSTHROUGH = "passthrough"  # Normal API calls, no caching
    CAPTURE = "capture"          # Record all calls to cache
    REPLAY = "replay"            # Use cached responses only
    MOCK = "mock"                # Use mock responses (no API)


# =============================================================================
# Cache Entry
# =============================================================================

@dataclass
class CacheEntry:
    """A cached Claude API response."""
    cache_key: str
    model: str
    messages: list[dict]
    max_tokens: int
    system: Optional[str]
    response_text: str
    input_tokens: int
    output_tokens: int
    created_at: str
    phase: Optional[str] = None  # "imagination", "work", etc.
    cycle: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        return cls(**data)


# =============================================================================
# Claude Cache
# =============================================================================

class ClaudeCache:
    """
    Manages Claude response cache for a forecast trace.

    Cache files are stored in the trace directory:
        trace_dir/claude_cache/
            index.json              # Maps cache_key -> filename
            cycle_001_imagination_001.json
            cycle_001_work_001.json
            ...
    """

    def __init__(self, cache_dir: Path):
        """
        Initialize cache with a directory.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / "index.json"
        self._index: dict[str, str] = {}  # cache_key -> filename
        self._load_index()
        self._call_counter = 0  # For generating unique filenames
        self._current_phase: Optional[str] = None
        self._current_cycle: int = 0

    def _load_index(self):
        """Load the cache index from disk."""
        if self.index_path.exists():
            try:
                self._index = json.loads(self.index_path.read_text())
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache index: {e}")
                self._index = {}

    def _save_index(self):
        """Save the cache index to disk."""
        self.index_path.write_text(json.dumps(self._index, indent=2))

    def set_context(self, cycle: int, phase: str):
        """Set current cycle and phase for cache file naming."""
        self._current_cycle = cycle
        self._current_phase = phase

    @staticmethod
    def compute_key(
        model: str,
        messages: list[dict],
        max_tokens: int,
        system: Optional[str] = None,
    ) -> str:
        """
        Compute a cache key from request parameters.

        Returns: First 16 characters of SHA256 hash
        """
        key_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "system": system or "",
        }
        key_json = json.dumps(key_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(key_json.encode()).hexdigest()[:16]

    def get(self, cache_key: str) -> Optional[CacheEntry]:
        """
        Get a cached response by key.

        Returns: CacheEntry if found, None otherwise
        """
        filename = self._index.get(cache_key)
        if not filename:
            return None

        cache_file = self.cache_dir / filename
        if not cache_file.exists():
            logger.warning(f"Cache index references missing file: {filename}")
            return None

        try:
            data = json.loads(cache_file.read_text())
            return CacheEntry.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load cache entry: {e}")
            return None

    def put(
        self,
        cache_key: str,
        model: str,
        messages: list[dict],
        max_tokens: int,
        system: Optional[str],
        response_text: str,
        input_tokens: int,
        output_tokens: int,
    ) -> CacheEntry:
        """
        Store a response in the cache.

        Returns: The created CacheEntry
        """
        self._call_counter += 1

        # Generate filename based on current context
        if self._current_phase:
            filename = f"cycle_{self._current_cycle:03d}_{self._current_phase}_{self._call_counter:03d}.json"
        else:
            filename = f"call_{self._call_counter:04d}.json"

        entry = CacheEntry(
            cache_key=cache_key,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            system=system,
            response_text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            created_at=datetime.utcnow().isoformat(),
            phase=self._current_phase,
            cycle=self._current_cycle,
        )

        # Write cache file
        cache_file = self.cache_dir / filename
        cache_file.write_text(json.dumps(entry.to_dict(), indent=2))

        # Update index
        self._index[cache_key] = filename
        self._save_index()

        logger.debug(f"Cached response: {cache_key} -> {filename}")
        return entry

    def get_all_entries(self) -> list[CacheEntry]:
        """Get all cached entries."""
        entries = []
        for cache_key in self._index:
            entry = self.get(cache_key)
            if entry:
                entries.append(entry)
        return entries

    def get_total_tokens(self) -> tuple[int, int]:
        """Get total input and output tokens from all cached entries."""
        input_total = 0
        output_total = 0
        for entry in self.get_all_entries():
            input_total += entry.input_tokens
            output_total += entry.output_tokens
        return input_total, output_total

    def estimate_cost(self, input_rate: float = 0.003, output_rate: float = 0.015) -> float:
        """
        Estimate API cost from cached usage.

        Args:
            input_rate: Cost per 1000 input tokens (default: Claude 3.5 Sonnet)
            output_rate: Cost per 1000 output tokens

        Returns: Estimated cost in dollars
        """
        input_tokens, output_tokens = self.get_total_tokens()
        return (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)


# =============================================================================
# Mock Message Response (matches Anthropic SDK structure)
# =============================================================================

@dataclass
class MockContentBlock:
    """Simulates anthropic.types.ContentBlock."""
    text: str
    type: str = "text"


@dataclass
class MockUsage:
    """Simulates anthropic.types.Usage."""
    input_tokens: int = 100
    output_tokens: int = 50


@dataclass
class MockMessage:
    """Simulates anthropic.types.Message."""
    content: list
    stop_reason: str = "end_turn"
    usage: MockUsage = field(default_factory=MockUsage)
    model: str = "claude-sonnet-4-20250514"
    id: str = "msg_cached"


# =============================================================================
# Cached Messages API
# =============================================================================

class CachedMessagesAPI:
    """Wrapper around messages.create() with caching support."""

    def __init__(self, parent: "CachedClaudeClient"):
        self._parent = parent

    def create(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs,
    ) -> MockMessage:
        """
        Create a message with caching.

        In CAPTURE mode: Calls API and caches response
        In REPLAY mode: Returns cached response or raises error
        In MOCK mode: Returns mock response
        In PASSTHROUGH mode: Calls API without caching
        """
        mode = self._parent.mode
        cache = self._parent.cache

        # Compute cache key
        cache_key = ClaudeCache.compute_key(model, messages, max_tokens, system)

        # MOCK mode - return mock response
        if mode == CacheMode.MOCK:
            return self._mock_response(messages)

        # REPLAY mode - must use cache
        if mode == CacheMode.REPLAY:
            entry = cache.get(cache_key) if cache else None
            if entry:
                logger.debug(f"Cache hit: {cache_key}")
                return MockMessage(
                    content=[MockContentBlock(text=entry.response_text)],
                    usage=MockUsage(
                        input_tokens=entry.input_tokens,
                        output_tokens=entry.output_tokens,
                    ),
                    model=entry.model,
                    id=f"msg_cached_{cache_key}",
                )
            else:
                raise ValueError(f"Cache miss in REPLAY mode: {cache_key}")

        # CAPTURE or PASSTHROUGH - call real API
        if not self._parent._real_client:
            raise ValueError("No real client available for API calls")

        # Make the actual API call
        response = self._parent._real_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            system=system,
            **kwargs,
        )

        # Extract response text
        response_text = ""
        if response.content:
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text

        # CAPTURE mode - save to cache
        if mode == CacheMode.CAPTURE and cache:
            cache.put(
                cache_key=cache_key,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                system=system,
                response_text=response_text,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

        return response

    def _mock_response(self, messages: list[dict]) -> MockMessage:
        """Generate a mock response for MOCK mode."""
        # Generate a simple mock response based on the last message
        last_message = messages[-1] if messages else {}
        content = last_message.get("content", "")

        # Simple mock responses based on context
        if "hypothesis" in content.lower() or "hypothes" in content.lower():
            mock_text = '''```json
{
  "hypotheses": [
    {
      "id": "hyp-mock-001",
      "description": "Mock hypothesis for testing",
      "feasibility": 0.85,
      "north_star_alignment": 0.90,
      "estimated_effort": "medium"
    }
  ]
}
```'''
        elif "task" in content.lower():
            mock_text = '''```json
{
  "description": "Mock task for testing",
  "task_type": "build",
  "estimated_minutes": 30
}
```'''
        else:
            mock_text = "I understand. I'll proceed with the task."

        return MockMessage(
            content=[MockContentBlock(text=mock_text)],
            usage=MockUsage(input_tokens=100, output_tokens=50),
        )


# =============================================================================
# Cached Claude Client
# =============================================================================

class CachedClaudeClient:
    """
    Claude client wrapper with caching support.

    Usage:
        # CAPTURE mode - record API calls
        client = CachedClaudeClient(
            cache_dir=Path("./trace/claude_cache"),
            mode=CacheMode.CAPTURE,
            api_key="sk-ant-..."
        )

        # REPLAY mode - use cached responses
        client = CachedClaudeClient(
            cache_dir=Path("./trace/claude_cache"),
            mode=CacheMode.REPLAY,
        )

        # Use like normal Anthropic client
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello"}],
        )
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        mode: CacheMode = CacheMode.PASSTHROUGH,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the cached client.

        Args:
            cache_dir: Directory for cache files (required for CAPTURE/REPLAY)
            mode: Cache operating mode
            api_key: Anthropic API key (required for CAPTURE/PASSTHROUGH)
        """
        self.mode = mode
        self.cache: Optional[ClaudeCache] = None
        self._real_client = None

        # Initialize cache if needed
        if cache_dir and mode in (CacheMode.CAPTURE, CacheMode.REPLAY):
            self.cache = ClaudeCache(cache_dir)

        # Initialize real client if needed
        if mode in (CacheMode.CAPTURE, CacheMode.PASSTHROUGH):
            if api_key:
                import anthropic
                self._real_client = anthropic.Anthropic(api_key=api_key)
            elif mode != CacheMode.MOCK:
                import os
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if api_key:
                    import anthropic
                    self._real_client = anthropic.Anthropic(api_key=api_key)

        # Sub-APIs
        self.messages = CachedMessagesAPI(self)

    def set_phase(self, cycle: int, phase: str):
        """Set current cycle and phase for cache file naming."""
        if self.cache:
            self.cache.set_context(cycle, phase)

    def get_usage_stats(self) -> dict:
        """Get usage statistics from cache."""
        if not self.cache:
            return {"input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0}

        input_tokens, output_tokens = self.cache.get_total_tokens()
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": self.cache.estimate_cost(),
        }
