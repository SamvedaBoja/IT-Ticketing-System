from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select, SQLModel
from typing import List
from app.database.config import get_session
from app.models.ticket import Ticket, TicketCreate, TicketRead, TicketTriageUpdate, TicketPriority, TicketStatus, TicketAssignUpdate, TicketResolveUpdate
from app.models.user import User, UserRole
from app.database.config import get_session
from datetime import datetime


router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("/", response_model=TicketRead, status_code=201)
def create_ticket(
    ticket: TicketCreate,
    session: Session = Depends(get_session),
    x_user_id: int = Header(..., alias="X-User-ID")
):
    user = session.get(User, x_user_id)
    if not user or user.role != "employee":
        raise HTTPException(status_code=403, detail="Only employees can submit tickets.")
    
    new_ticket = Ticket(**ticket.dict(), reporter_id=user.id)
    session.add(new_ticket)
    session.commit()
    session.refresh(new_ticket)
    return new_ticket

@router.get("/my", response_model=list[TicketRead])
def get_my_tickets(
    session: Session = Depends(get_session),
    x_user_id: int = Header(..., alias="X-User-ID")
):
    user = session.get(User, x_user_id)
    if not user or user.role != "employee":
        raise HTTPException(status_code=403, detail="Only employees can view their tickets.")
    
    tickets = session.exec(select(Ticket).where(Ticket.reporter_id == user.id)).all()
    return tickets

# --- REOPEN TICKET ---
@router.put("/{ticket_id}/reopen", response_model=TicketRead)
def reopen_ticket(ticket_id: int, session: Session = Depends(get_session), x_user_id: int = Header(..., alias="X-User-ID")):
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    user = session.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if ticket.status != "resolved":
        raise HTTPException(status_code=400, detail="Only resolved tickets can be reopened")

    if user.role != UserRole.agent and ticket.reporter_id != user.id and ticket.assignee_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to reopen this ticket")

    ticket.status = "in_progress"
    ticket.resolved_at = None
    ticket.resolution_notes = None
    ticket.updated_at = datetime.utcnow()
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket

# --- CLOSE TICKET ---
@router.put("/{ticket_id}/close", response_model=TicketRead)
def close_ticket(ticket_id: int, session: Session = Depends(get_session), x_user_id: int = Header(..., alias="X-User-ID")):
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    user = session.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if ticket.status != "resolved":
        raise HTTPException(status_code=400, detail="Only resolved tickets can be closed")

    if user.role != UserRole.agent and ticket.reporter_id != user.id and ticket.assignee_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to close this ticket")

    ticket.status = "closed"
    ticket.updated_at = datetime.utcnow()
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket

@router.get("/pending-triage", response_model=List[TicketRead])
def get_pending_tickets_for_triage(
    session: Session = Depends(get_session),
    x_user_id: int = Header(..., alias="X-User-ID")
):
    user = session.get(User, x_user_id)
    if not user or user.role != UserRole.triage_officer:
        raise HTTPException(status_code=403, detail="Only triage officers can access this")

    tickets = session.exec(select(Ticket).where(Ticket.status == TicketStatus.new)).all()
    return tickets

@router.put("/{ticket_id}/triage", response_model=TicketRead)
def triage_ticket(
    ticket_id: int,
    update_data: TicketTriageUpdate,
    session: Session = Depends(get_session),
    x_user_id: int = Header(..., alias="X-User-ID")
):
    user = session.get(User, x_user_id)
    if not user or user.role != UserRole.triage_officer:
        raise HTTPException(status_code=403, detail="Only triage officers can triage tickets")

    ticket = session.get(Ticket, ticket_id)
    if not ticket or ticket.status != TicketStatus.new:
        raise HTTPException(status_code=400, detail="Ticket not found or not in 'new' status")

    ticket.priority = update_data.priority
    ticket.assigned_team = update_data.assigned_team
    ticket.assignee_id = update_data.assignee_id
    ticket.status = TicketStatus.triaged
    ticket.updated_at = datetime.utcnow()

    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket

@router.get("/", response_model=List[TicketRead])
def get_all_tickets(x_user_id: int = Header(..., alias="X-User-ID"), session: Session = Depends(get_session)):
    user = session.get(User, x_user_id)
    if user is None or user.role not in ["agent", "triage_officer"]:
        raise HTTPException(status_code=403, detail="Access forbidden")
    tickets = session.exec(select(Ticket)).all()
    return tickets

@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket_by_id(
    ticket_id: int,
    x_user_id: int = Header(..., alias="X-User-ID"),
    session: Session = Depends(get_session)
):
    # Fetch the user making the request
    user = session.exec(select(User).where(User.id == x_user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the ticket
    ticket = session.exec(select(Ticket).where(Ticket.id == ticket_id)).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Authorization check
    if (
        ticket.reporter_id != x_user_id
        and ticket.assignee_id != x_user_id
        and user.role not in ["agent", "triage_officer"]
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")

    return ticket

@router.put("/{ticket_id}/assign", response_model=TicketRead)
def assign_ticket(ticket_id: int, update: TicketAssignUpdate, x_user_id: int = Header(..., alias="X-User-ID"), session: Session = Depends(get_session)):
    agent = session.get(User, x_user_id)
    if agent is None or agent.role != "agent":
        raise HTTPException(status_code=403, detail="Only agents can assign tickets")

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.assignee_id = update.assignee_id
    if ticket.status == "triaged":
        ticket.status = "in_progress"
    ticket.updated_at = datetime.utcnow()
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket

@router.put("/{ticket_id}/resolve", response_model=TicketRead)
def resolve_ticket(ticket_id: int, update: TicketResolveUpdate, x_user_id: int = Header(..., alias="X-User-ID"), session: Session = Depends(get_session)):
    agent = session.get(User, x_user_id)
    if agent is None or agent.role != "agent":
        raise HTTPException(status_code=403, detail="Only agents can resolve tickets")

    ticket = session.get(Ticket, ticket_id)
    if ticket is None or ticket.status != "in_progress":
        raise HTTPException(status_code=400, detail="Ticket must be in progress to resolve")

    ticket.status = "resolved"
    ticket.resolution_notes = update.resolution_notes
    ticket.resolved_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()

    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket