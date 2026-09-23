from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import Lookup, Sources
from .schemas import ConfigOut, SourceIn, SourceOut, SourceRemoved, SourceResult

router = APIRouter(prefix="/api", tags=["legacy"])


@router.get("/config", response_model=ConfigOut)
def config(sources: Sources) -> ConfigOut:
    return ConfigOut(sources=[SourceOut.of(s) for s in sources.all()])


@router.post("/sources", response_model=SourceResult)
def add_source(body: SourceIn, sources: Sources) -> SourceResult:
    return SourceResult(source=SourceOut.of(sources.add(body.path or "", body.project)))


@router.put("/sources/{index}", response_model=SourceResult)
def update_source(index: int, body: SourceIn, sources: Sources, lookup: Lookup) -> SourceResult:
    source_id = lookup.by_index(index).id
    return SourceResult(source=SourceOut.of(sources.update(source_id, body.path or "", body.project)))


@router.delete("/sources/{index}", response_model=SourceRemoved)
def delete_source(index: int, sources: Sources, lookup: Lookup, path: str | None = None) -> SourceRemoved:
    source_id = lookup.by_index(index, expected_path=path).id
    return SourceRemoved(removed=SourceOut.of(sources.remove(source_id)))
