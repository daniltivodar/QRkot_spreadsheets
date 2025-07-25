from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser, current_user
from app.crud.charity_project import charity_project_crud
from app.crud.donation import donation_crud
from app.models.user import User
from app.schemas.donation import (
    DonationCreate, DonationDBForAdmin, DonationDBForUser,
)
from app.services.investment import investment

router = APIRouter()


@router.get(
    '/',
    response_model=list[DonationDBForAdmin],
    dependencies=(Depends(current_superuser),),
)
async def get_all_donations(
    session: AsyncSession = Depends(get_async_session),
):
    """Только для суперюзеров.

    Возвращает список всех пожертвований
    """
    return await donation_crud.get_multi(session)


@router.post(
    '/',
    response_model=DonationDBForUser,
    response_model_exclude_none=True,
)
async def create_donation(
    donation: DonationCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    """Сделать пожертвование."""
    donation = await donation_crud.create(donation, session, user, False)
    session.add_all(
        investment(
            donation,
            await charity_project_crud.get_not_fully_invested(session),
        ),
    )
    await session.commit()
    await session.refresh(donation)
    return donation


@router.get(
    '/my',
    response_model=list[DonationDBForUser],
    response_model_exclude={'user_id'},
)
async def get_user_donations(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    """Вернуть список пожертвований пользователя, выполняющего запрос."""
    return await donation_crud.get_by_user(session, user)
