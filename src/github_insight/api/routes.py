"""Versioned JSON and CSV endpoints consumed by the browser client."""

import csv
import io
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from github_insight.api.dependencies import AnalysisServiceDep
from github_insight.schemas import AnalysisRequest, AnalysisResponse, HistoryItem
from github_insight.services.github_client import GitHubAPIError

router = APIRouter(prefix="/api/v1", tags=["analysis"])


def _response(snapshot, cached: bool = False) -> AnalysisResponse:
    return AnalysisResponse(
        id=snapshot.id,
        username=snapshot.username,
        analyzed_at=snapshot.analyzed_at,
        cached=cached,
        data=snapshot.payload,
    )


@router.post("/analyses", response_model=AnalysisResponse, status_code=201)
async def create_analysis(
    request: AnalysisRequest,
    service: AnalysisServiceDep,
) -> AnalysisResponse:
    try:
        snapshot, cached = await service.analyze(request.username, request.force_refresh)
    except GitHubAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return _response(snapshot, cached)


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int, service: AnalysisServiceDep
) -> AnalysisResponse:
    snapshot = service.get(analysis_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _response(snapshot)


@router.get("/history", response_model=list[HistoryItem])
def get_history(
    service: AnalysisServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[HistoryItem]:
    return [
        HistoryItem(
            id=item.id,
            username=item.username,
            display_name=item.display_name,
            avatar_url=item.avatar_url,
            analyzed_at=item.analyzed_at,
        )
        for item in service.history(limit)
    ]


@router.delete("/history/{analysis_id}", status_code=204)
def delete_history(
    analysis_id: int, service: AnalysisServiceDep
) -> None:
    if not service.delete(analysis_id):
        raise HTTPException(status_code=404, detail="Analysis not found")


@router.get("/analyses/{analysis_id}/export.csv")
def export_analysis(
    analysis_id: int, service: AnalysisServiceDep
) -> StreamingResponse:
    snapshot = service.get(analysis_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "name", "value"])
    for name, value in snapshot.payload["totals"].items():
        writer.writerow(["totals", name, value])
    for language in snapshot.payload["languages"]:
        writer.writerow(["language_percentage", language["name"], language["percentage"]])
    for repo in snapshot.payload["top_repositories"]:
        writer.writerow(["repository", repo["name"], json.dumps(repo, ensure_ascii=False)])
    headers = {"Content-Disposition": f'attachment; filename="{snapshot.username}-analysis.csv"'}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)
