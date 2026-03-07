"""Artifact upload/download endpoints."""

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import Response

from backend.app.schemas.artifact import ArtifactResponse, ArtifactUploadResponse
from backend.app.core.dependencies import DatabaseSession, CurrentUser
from backend.app.services.artifact_service import upload_artifact, download_artifact
from backend.app.models.artifact import Artifact
from backend.app.models.ticket import Ticket


router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.post("", response_model=ArtifactUploadResponse)
async def upload_artifact_endpoint(
    ticket_id: int,
    file: UploadFile = File(...),
    artifact_type: str | None = None,
    description: str | None = None,
    db: DatabaseSession = None,
    current_user: CurrentUser = None
):
    """
    Upload an artifact for a ticket.

    Args:
        ticket_id: Associated ticket ID
        file: File to upload
        artifact_type: Optional artifact classification
        description: Optional description
    """
    # Verify ticket exists and user has permission
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check permissions
    if not current_user.is_admin:
        if ticket.created_by_id != current_user.id:
        # 当前用户如果不是管理员 ，
        # 而且 如果这个工单不是由当前已登录的用户创建的话，报错。
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload artifacts for this ticket"
            )

    # Upload artifact
    artifact = await upload_artifact(
        db=db,
        file=file.file,
        filename=file.filename,
        ticket_id=ticket_id,
        uploader=current_user,
        content_type=file.content_type,
        artifact_type=artifact_type,
        description=description
    )

    return ArtifactUploadResponse(artifact=artifact)


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact_metadata(
    artifact_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get artifact metadata."""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )

    # Check permissions
    if not current_user.is_admin:
        if artifact.ticket.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this artifact"
            )

    return artifact


@router.get("/{artifact_id}/download")
async def download_artifact_endpoint(
    artifact_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Download artifact file."""
    file_content, artifact = await download_artifact(db, artifact_id, current_user)

    return Response(
        content=file_content,
        media_type=artifact.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{artifact.filename}"'
        }
    )


@router.get("/ticket/{ticket_id}", response_model=list[ArtifactResponse])
async def list_ticket_artifacts(
    ticket_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """List all artifacts for a ticket."""
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check permissions
    if not current_user.is_admin:
        if ticket.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view artifacts for this ticket"
            )

    artifacts = db.query(Artifact).filter(
        Artifact.ticket_id == ticket_id,
        Artifact.is_deleted == False
    ).all()

    return artifacts
