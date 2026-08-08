from pathlib import Path
import asyncio

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend import file_picker, sources_store, tail
from backend.version import get_app_version

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Logs Home", version=get_app_version())


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    path: str = Field(min_length=1)


class SourceResponse(BaseModel):
    id: str
    name: str
    path: str
    created_at: str


class TailResponse(BaseModel):
    source_id: str
    name: str
    path: str
    lines: list[str]
    line_count: int


class PickFileResponse(BaseModel):
    path: str


class VersionResponse(BaseModel):
    version: str


@app.get("/api/version", response_model=VersionResponse)
def api_version() -> VersionResponse:
    return VersionResponse(version=get_app_version())


@app.post("/api/pick-file", response_model=PickFileResponse, responses={204: {"description": "User cancelled"}})
async def api_pick_file() -> PickFileResponse | Response:
    try:
        selected = await asyncio.to_thread(file_picker.pick_log_file)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not open file picker: {exc}",
        ) from exc

    if selected is None:
        return Response(status_code=204)

    return PickFileResponse(path=selected)


@app.get("/api/sources", response_model=list[SourceResponse])
def api_list_sources() -> list[SourceResponse]:
    return [SourceResponse(**s) for s in sources_store.list_sources()]


@app.post("/api/sources", response_model=SourceResponse, status_code=201)
def api_create_source(body: SourceCreate) -> SourceResponse:
    try:
        source = sources_store.create_source(body.name, body.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SourceResponse(**source)


@app.delete("/api/sources/{source_id}", status_code=204)
def api_delete_source(source_id: str) -> None:
    if not sources_store.delete_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found")


@app.get("/api/sources/{source_id}/tail", response_model=TailResponse)
def api_tail_source(
    source_id: str,
    lines: int = Query(default=200, ge=1, le=10_000),
) -> TailResponse:
    source = sources_store.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        content_lines = tail.read_last_lines(source["path"], lines)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {exc}") from exc

    return TailResponse(
        source_id=source["id"],
        name=source["name"],
        path=source["path"],
        lines=content_lines,
        line_count=len(content_lines),
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
