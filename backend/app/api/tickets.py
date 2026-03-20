"""Ticket management endpoints."""

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func

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
    page_size: int = Query(default=20, ge=1, le=100)
):
    """
    List tickets with pagination.

    Admins can see all tickets, employees can only see their own.
    """
    query = select(Ticket)

    if not current_user.is_admin:
        query = query.where(Ticket.created_by_id == current_user.id)

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

