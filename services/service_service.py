from sqlalchemy.orm import Session
from models import Service
from repositories.base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    model = Service

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_frizer(self, frizer_id: int) -> list[Service]:
        return self.db.query(Service).filter_by(frizer_id=frizer_id).order_by(Service.name).all()


class ServiceService:
    def __init__(self, db: Session):
        self.repo = ServiceRepository(db)
        self.db = db

    def get_all_for_frizer(self, frizer_id: int) -> list[Service]:
        return self.repo.get_by_frizer(frizer_id)

    def create_service(self, name: str, description: str | None, price: int | None, frizer_id: int) -> Service:
        service = Service(
            name=name,
            description=description,
            price=price,
            frizer_id=frizer_id
        )
        return self.repo.create(service)

    def update_service(self, service_id: int, name: str, description: str | None, price: int | None) -> Service:
        service = self.repo.get_by_id(service_id)
        if not service:
            raise ValueError("Serviciu nu exista")
        
        service.name = name
        service.description = description
        service.price = price
        return self.repo.update(service)

    def delete_service(self, service_id: int) -> None:
        service = self.repo.get_by_id(service_id)
        if not service:
            raise ValueError("Serviciu nu exista")
        self.repo.delete(service)