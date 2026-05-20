# Proxy Layer
# Fiverr Research System — Wave 4

**Document Status:** Complete
**Wave:** 4 — Collection Engine Design
**Purpose:** ProxyLayer interface specification, v1 no-proxy pass-through implementation, v2 rotating residential proxy extension, Playwright and httpx injection, proxy health tracking, and config.yaml proxy section.

---

## Design Principles

1. **Pluggable by design.** The ProxyLayer is an interface with a v1 pass-through and a v2 extension point. Switching from no-proxy to rotating proxies requires only a config change and a class swap — no collection module code changes.
2. **No-proxy is the correct v1 choice.** A residential IP combined with authenticated session + natural-rate pacing is sufficient for the collection volumes in this system. Proxies add cost and complexity without meaningful benefit at weekly-run cadence.
3. **v2 proxy support is designed now so it is not disruptive later.** The interface is defined, the injection points are documented, and the extension class is specified — only the implementation is deferred.
4. **Proxy state is per-run, not per-request.** In v2, the session manager receives a proxy at context creation time. Rotating happens between runs or between niches, not between individual page loads. This keeps the Fiverr session cookie valid (session cookies are IP-associated in some cases).

---

## v1 — No-Proxy Pass-Through (Default)

```python
# src/collection/proxy_layer.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import logging

log = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Represents a single proxy configuration."""
    server: str                 # e.g., "http://proxy.example.com:8080"
    username: Optional[str] = None
    password: Optional[str] = None
    bypass: Optional[str] = None  # Hosts to bypass (e.g., "localhost,127.0.0.1")

    def to_playwright_dict(self) -> dict:
        """Returns proxy dict for Playwright new_context(proxy=...)."""
        d = {"server": self.server}
        if self.username:
            d["username"] = self.username
        if self.password:
            d["password"] = self.password
        if self.bypass:
            d["bypass"] = self.bypass
        return d

    def to_httpx_url(self) -> str:
        """Returns proxy URL string for httpx proxies= parameter."""
        if self.username and self.password:
            protocol = self.server.split("://")[0]
            host_port = self.server.split("://")[1]
            return f"{protocol}://{self.username}:{self.password}@{host_port}"
        return self.server


class ProxyLayer:
    """
    v1 Implementation: No-proxy pass-through.

    All collection uses the user's direct residential internet connection.
    This is the correct choice for v1 because:
    - Weekly run cadence is low-volume by nature
    - Authenticated session + natural-rate pacing is sufficient
    - Residential IP is less detectable than datacenter or proxy IP
    - No cost, no complexity, no rotation state management

    Override get_proxy() in a subclass to enable proxy support in v2.
    """

    def __init__(self, config):
        self.config = config
        self.proxy_enabled = getattr(
            getattr(config, "proxy", None), "enabled", False
        )
        if self.proxy_enabled:
            log.warning(
                "proxy.enabled=true but using base ProxyLayer (no-proxy). "
                "Set a concrete proxy implementation to use proxies."
            )

    def get_proxy(self, niche_id: str | None = None) -> Optional[ProxyConfig]:
        """
        Returns proxy configuration for the given niche, or None for no proxy.

        v1: Always returns None (direct connection).
        v2: Override this method to return a ProxyConfig.

        Args:
            niche_id: Optional niche context (v2 may use different proxies per niche)
        """
        return None

    def get_playwright_proxy(self, niche_id: str | None = None) -> Optional[dict]:
        """
        Returns Playwright-compatible proxy dict, or None.
        Inject this into: browser.new_context(proxy=get_playwright_proxy())
        """
        proxy = self.get_proxy(niche_id)
        return proxy.to_playwright_dict() if proxy else None

    def get_httpx_proxy(self, niche_id: str | None = None) -> Optional[dict]:
        """
        Returns httpx-compatible proxies dict, or None.
        Inject this into: httpx.AsyncClient(proxies=get_httpx_proxy())
        """
        proxy = self.get_proxy(niche_id)
        if proxy is None:
            return None
        proxy_url = proxy.to_httpx_url()
        return {
            "http://": proxy_url,
            "https://": proxy_url,
        }

    def report_failure(self, proxy: ProxyConfig, error: Exception):
        """
        Reports a proxy failure.
        v1: No-op (no proxy to report on).
        v2: Override to implement rotation/removal logic.
        """
        pass

    def report_success(self, proxy: ProxyConfig):
        """
        Reports a successful proxy use.
        v1: No-op.
        v2: Override to track success rates.
        """
        pass

    def get_health_stats(self) -> dict:
        """
        Returns proxy health statistics for run summary.
        v1: Returns minimal stats.
        v2: Returns per-proxy success/failure rates.
        """
        return {
            "proxy_enabled": self.proxy_enabled,
            "proxy_mode": "direct",
            "total_proxies": 0,
            "healthy_proxies": 0,
        }
```

---

## v2 — Rotating Residential Proxy Extension

When the user decides to add proxies (e.g., to scale to multiple daily runs, or if rate limiting becomes an issue), swap `ProxyLayer` for this extension:

```python
# src/collection/rotating_proxy_layer.py

import random
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
from .proxy_layer import ProxyLayer, ProxyConfig

log = logging.getLogger(__name__)


@dataclass
class ProxyHealth:
    """Tracks health metrics for a single proxy."""
    proxy: ProxyConfig
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    is_healthy: bool = True

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0


class RotatingResidentialProxyLayer(ProxyLayer):
    """
    v2 Implementation: Rotating residential proxy pool.

    Supports round-robin, random, and sticky-session rotation modes.
    Automatically removes proxies that fail repeatedly.
    Compatible with providers: Bright Data, Oxylabs, Smartproxy, custom list.
    """

    def __init__(self, config):
        super().__init__(config)
        self.rotation_mode = getattr(config.proxy, "rotation_mode", "round_robin")
        self.sticky_duration = getattr(config.proxy, "sticky_session_duration", 300)
        self._proxy_pool: list[ProxyHealth] = []
        self._round_robin_index: int = 0
        self._niche_sticky: dict[str, ProxyConfig] = {}  # niche_id → current proxy
        self._load_proxies()

    def _load_proxies(self):
        """Loads proxy list from config or file."""
        proxy_list_file = getattr(self.config.proxy, "proxy_list_file", None)
        if proxy_list_file:
            self._load_from_file(proxy_list_file)
        elif hasattr(self.config.proxy, "proxies"):
            self._load_from_config(self.config.proxy.proxies)

        if not self._proxy_pool:
            log.error("No proxies loaded. Falling back to direct connection.")
            self.proxy_enabled = False

        log.info(f"Proxy pool loaded: {len(self._proxy_pool)} proxies, mode={self.rotation_mode}")

    def _load_from_file(self, filepath: str):
        """
        Loads proxies from a text file (one proxy per line).
        Supported formats:
            http://user:pass@host:port
            host:port:user:pass
            host:port (no auth)
        """
        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    proxy = self._parse_proxy_line(line)
                    if proxy:
                        self._proxy_pool.append(ProxyHealth(proxy=proxy))
        except FileNotFoundError:
            log.error(f"Proxy list file not found: {filepath}")

    def _parse_proxy_line(self, line: str) -> Optional[ProxyConfig]:
        """Parses a proxy line into a ProxyConfig."""
        try:
            if line.startswith("http://") or line.startswith("https://"):
                return ProxyConfig(server=line)
            parts = line.split(":")
            if len(parts) == 4:  # host:port:user:pass
                host, port, user, password = parts
                return ProxyConfig(
                    server=f"http://{host}:{port}",
                    username=user,
                    password=password,
                )
            elif len(parts) == 2:  # host:port
                return ProxyConfig(server=f"http://{line}")
        except Exception as e:
            log.warning(f"Could not parse proxy line '{line}': {e}")
        return None

    def _load_from_config(self, proxies_config: list):
        """Loads proxies from config.yaml proxy.proxies list."""
        for p in proxies_config:
            self._proxy_pool.append(ProxyHealth(
                proxy=ProxyConfig(
                    server=p["server"],
                    username=p.get("username"),
                    password=p.get("password"),
                )
            ))

    def get_proxy(self, niche_id: str | None = None) -> Optional[ProxyConfig]:
        """Returns next proxy according to rotation mode."""
        healthy = [ph for ph in self._proxy_pool if ph.is_healthy]
        if not healthy:
            log.error("No healthy proxies available. Using direct connection.")
            return None

        if self.rotation_mode == "sticky_session" and niche_id:
            # Return same proxy for this niche if within sticky duration
            if niche_id in self._niche_sticky:
                return self._niche_sticky[niche_id]
            proxy = random.choice(healthy).proxy
            self._niche_sticky[niche_id] = proxy
            return proxy

        if self.rotation_mode == "random":
            return random.choice(healthy).proxy

        # Default: round-robin
        self._round_robin_index = self._round_robin_index % len(healthy)
        proxy = healthy[self._round_robin_index].proxy
        self._round_robin_index += 1
        return proxy

    def report_failure(self, proxy: ProxyConfig, error: Exception):
        """Records a proxy failure. Removes proxy after 3 consecutive failures."""
        for ph in self._proxy_pool:
            if ph.proxy.server == proxy.server:
                ph.failure_count += 1
                ph.consecutive_failures += 1
                if ph.consecutive_failures >= 3:
                    ph.is_healthy = False
                    log.warning(
                        f"Proxy {proxy.server} marked unhealthy after "
                        f"{ph.consecutive_failures} consecutive failures. "
                        f"Removing from pool."
                    )
                    # Clear sticky session for this proxy
                    self._niche_sticky = {
                        k: v for k, v in self._niche_sticky.items()
                        if v.server != proxy.server
                    }
                break

    def report_success(self, proxy: ProxyConfig):
        """Records a proxy success, resets consecutive failure count."""
        for ph in self._proxy_pool:
            if ph.proxy.server == proxy.server:
                ph.success_count += 1
                ph.consecutive_failures = 0
                break

    def get_health_stats(self) -> dict:
        """Returns proxy health statistics."""
        return {
            "proxy_enabled": True,
            "proxy_mode": self.rotation_mode,
            "total_proxies": len(self._proxy_pool),
            "healthy_proxies": sum(1 for ph in self._proxy_pool if ph.is_healthy),
            "unhealthy_proxies": sum(1 for ph in self._proxy_pool if not ph.is_healthy),
            "per_proxy_stats": [
                {
                    "server": ph.proxy.server,
                    "is_healthy": ph.is_healthy,
                    "success_count": ph.success_count,
                    "failure_count": ph.failure_count,
                    "success_rate": round(ph.success_rate, 3),
                }
                for ph in self._proxy_pool
            ],
        }
```

---

## Playwright Context Proxy Injection

The Session Manager injects the proxy at browser context creation:

```python
# In session_manager.py — _load_session_headless():

async def _load_session_headless(self) -> BrowserContext:
    """Loads saved session into a headless browser context, with optional proxy."""
    self._playwright = await async_playwright().start()
    self._browser = await self._playwright.chromium.launch(
        headless=True,
        args=self._browser_args(),
        proxy=self.proxy_layer.get_playwright_proxy(niche_id=self._current_niche_id),
        # NOTE: proxy is set at browser launch level for full traffic routing.
        # Alternatively, set at context level (new_context(proxy=...))
        # for per-niche proxy rotation without restarting the browser.
    )
    context = await self._browser.new_context(
        storage_state=str(self.session_file),
        **self._context_options(),
    )
    return context

# For per-niche proxy rotation (v2 sticky session mode):
async def _create_niche_context(self, niche_id: str) -> BrowserContext:
    """Creates a browser context with niche-specific proxy."""
    proxy = self.proxy_layer.get_playwright_proxy(niche_id=niche_id)
    context = await self._browser.new_context(
        storage_state=str(self.session_file),
        proxy=proxy,  # None = direct connection
        **self._context_options(),
    )
    return context
```

---

## httpx Proxy Injection

External source connectors (Google Trends via httpx, YouTube via httpx) receive proxy config through the httpx client:

```python
# src/collection/external/http_client.py

import httpx
from src.collection.proxy_layer import ProxyLayer


def create_httpx_client(proxy_layer: ProxyLayer, niche_id: str | None = None) -> httpx.AsyncClient:
    """
    Creates an httpx AsyncClient with optional proxy configuration.
    v1: Returns client with no proxy (direct connection).
    v2: Returns client routed through the ProxyLayer's current proxy.
    """
    proxy_config = proxy_layer.get_httpx_proxy(niche_id)

    return httpx.AsyncClient(
        proxies=proxy_config,    # None = no proxy (v1 default)
        timeout=httpx.Timeout(15.0, connect=10.0),
        headers={
            "User-Agent": random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        },
        follow_redirects=True,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    )
```

---

## ProxyLayer Factory (Selecting Implementation)

```python
# src/collection/proxy_layer_factory.py

from src.collection.proxy_layer import ProxyLayer
from src.core.config import SystemConfig


def create_proxy_layer(config: SystemConfig) -> ProxyLayer:
    """
    Returns the appropriate ProxyLayer implementation based on config.

    config.proxy.enabled = false → ProxyLayer (no-proxy, v1 default)
    config.proxy.enabled = true  → RotatingResidentialProxyLayer (v2)
    """
    if not getattr(getattr(config, "proxy", None), "enabled", False):
        return ProxyLayer(config)

    from src.collection.rotating_proxy_layer import RotatingResidentialProxyLayer
    return RotatingResidentialProxyLayer(config)
```

---

## Proxy Configuration in config.yaml

```yaml
# config.yaml — proxy section
# v1: proxy.enabled = false (default)
# v2: change proxy.enabled to true and configure provider settings

proxy:
  enabled: false
  # Type: boolean | Default: false
  # Description: Set to true in v2 to enable proxy rotation.
  # In v1, leave as false. Direct residential IP + auth session is sufficient.

  provider: none
  # Type: string | Values: none | brightdata | oxylabs | smartproxy | custom
  # Default: none

  rotation_mode: round_robin
  # Type: string | Values: round_robin | random | sticky_session
  # Default: round_robin
  # sticky_session: same proxy is used for all requests within a niche per run

  sticky_session_duration: 300
  # Type: integer (seconds) | Default: 300
  # Description: How long to keep same proxy for a niche in sticky_session mode
  # Only used when rotation_mode = sticky_session

  proxy_list_file: data/proxies.txt
  # Type: string (path) | Default: data/proxies.txt
  # Description: Path to proxy list file (one proxy per line)
  # Supported format: http://user:pass@host:port OR host:port:user:pass

  # Alternative: define proxies directly in config (useful for small pools)
  # proxies:
  #   - server: "http://proxy1.example.com:8080"
  #     username: "user1"
  #     password: "pass1"
  #   - server: "http://proxy2.example.com:8080"
  #     username: "user2"
  #     password: "pass2"

  max_failures_before_remove: 3
  # Type: integer | Default: 3
  # Description: Number of consecutive failures before a proxy is removed from pool
```

---

## Proxy Provider Quick-Start Notes (v2 Reference)

### Bright Data (Luminati)
```
Proxy format: http://username:password@zproxy.lum-superproxy.io:22225
Residential plan recommended for Fiverr
Country targeting: &country=us (append to username for US IPs)
```

### Oxylabs
```
Proxy format: http://user:pass@pr.oxylabs.io:7777
Residential proxies with sticky sessions supported
```

### Smartproxy
```
Proxy format: http://user.pass@gate.smartproxy.com:10000
Lower cost option; adequate for weekly research runs
```

### Custom List (data/proxies.txt)
```
# One proxy per line
# Format: http://user:pass@host:port
http://user1:pass1@192.168.1.100:8080
http://user2:pass2@192.168.1.101:8080
# Or without auth:
# http://192.168.1.102:8080
```
