from sqlalchemy.orm import Session
from models import GalleryPhoto
from repositories.base import BaseRepository


class GalleryRepository(BaseRepository[GalleryPhoto]):
    model = GalleryPhoto

    def get_all(self) -> list[GalleryPhoto]:
        return (
            self.db.query(GalleryPhoto)
            .order_by(GalleryPhoto.sort_order, GalleryPhoto.created_at)
            .all()
        )

    def get_background(self) -> GalleryPhoto | None:
        return (
            self.db.query(GalleryPhoto)
            .filter(GalleryPhoto.is_background.is_(True))
            .first()
        )
