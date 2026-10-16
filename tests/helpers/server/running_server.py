from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI


@dataclass
class RunningServer:
    base_url: str
    app: FastAPI
