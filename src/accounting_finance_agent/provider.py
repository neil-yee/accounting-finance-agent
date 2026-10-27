"""Proxy adapter for the pinned LangSmith SDK's custom HTTP transport."""
from contextlib import contextmanager
import os
from langsmith.sandbox import SandboxClient
from langsmith._openapi_client._httpx import httpx


@contextmanager
def sandbox_client(*, timeout=10, max_retries=0):
    with SandboxClient(timeout=timeout, max_retries=max_retries) as client:
        proxy = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
        if proxy:
            old = client._http
            client._http = httpx.Client(proxy=proxy, timeout=timeout, headers=old.headers)
            old.close()
        yield client
