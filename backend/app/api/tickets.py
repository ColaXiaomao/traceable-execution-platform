"""Ticket management endpoints."""

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func

from datetime import datetime
from sqlalchemy import select, func, text

from backend.app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketApprove, PaginatedTicketResponse
from backend.app.core.dependencies import DatabaseSession, CurrentUser, CurrentAdmin
from backend.app.services.ticket_service import create_ticket, approve_ticket, update_ticket
from backend.app.models.ticket import Ticket


router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse)
async def create_new_ticket(
    ticket_in: TicketCreate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Create a new ticket."""
    ticket = await create_ticket(db, ticket_in, current_user)
    return ticket


# 修改
@router.get("", response_model=PaginatedTicketResponse)
async def list_tickets(
    db: DatabaseSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
     # ↓ 新增四个筛选参数
    keyword: str | None = Query(default=None),           # 标题关键词
    status: str | None = Query(default=None),            # 状态筛选
    asset_id: int | None = Query(default=None),          # 资产筛选
    start_date: datetime | None = Query(default=None),   # 开始时间
    end_date: datetime | None = Query(default=None)      # 结束时间
):
    
    query = select(Ticket)

    if not current_user.is_admin:
        query = query.where(Ticket.created_by_id == current_user.id)

    if keyword:
        query = query.where(Ticket.title.ilike(f"%{keyword}%"))
    if status:
        query = query.where(Ticket.status == status)
    if asset_id:
        query = query.where(Ticket.asset_id == asset_id)
    if start_date:
        query = query.where(Ticket.created_at >= start_date)
    if end_date:
        query = query.where(Ticket.created_at <= end_date) 

    # 总数
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    # 分页数据
    result = await db.execute(
        query.order_by(Ticket.created_at.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
    )
    tickets = result.scalars().all()

    return {
        "data": tickets,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket_endpoint(
    ticket_id: int,
    ticket_in: TicketUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Update a ticket."""
    ticket = await update_ticket(db, ticket_id, ticket_in, current_user)
    return ticket

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get ticket by ID."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    if not current_user.is_admin and ticket.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this ticket"
        )

    return ticket

@router.post("/{ticket_id}/approve", response_model=TicketResponse)
async def approve_ticket_endpoint(
    ticket_id: int,
    db: DatabaseSession,
    current_admin: CurrentAdmin
):
    """
    Approve a ticket (admin only).

    Required for action runs.
    """
    ticket = await approve_ticket(db, ticket_id, current_admin)
    return ticket

