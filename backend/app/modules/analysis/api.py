"""Analysis HTTP routes — run the pipeline, list and retrieve saved analyses."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.analysis.schemas import (
    AnalysisResponse,
    AnalysisSummaryResponse,
)
from app.modules.analysis.services import (
    build_export_csv_for_user,
    get_analysis_for_user,
    list_analyses_for_user,
    run_analysis_for_statement,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post(
    "/{statement_id}", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED
)
def create_analysis(
    statement_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisResponse:
    analysis = run_analysis_for_statement(db, user, statement_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found"
        )
    return AnalysisResponse.model_validate(analysis)


@router.get("/", response_model=list[AnalysisSummaryResponse])
def list_analyses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AnalysisSummaryResponse]:
    analyses = list_analyses_for_user(db, user.id)
    return [AnalysisSummaryResponse.model_validate(a) for a in analyses]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisResponse:
    analysis = get_analysis_for_user(db, analysis_id, user.id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
        )
    return AnalysisResponse.model_validate(analysis)

@router.get("/{analysis_id}/export.csv")
def export_analysis_csv(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    csv_text = build_export_csv_for_user(db, analysis_id, user.id)
    if csv_text is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Analysis not found or not authorized"
        )
    return Response(
        content=csv_text, 
        media_type="text/csv", 
        headers={
            "Content-Disposition": 
                f'attachment; filename="analysis-{analysis_id}.csv"'
        }
    )