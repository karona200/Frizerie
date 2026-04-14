from datetime import date
from sqlalchemy.orm import Session
from models import Frizer
from repositories.base import BaseRepository


class FrizerRepository(BaseRepository[Frizer]):
    """
    Toate operatiile cu baza de date legate de descrieri.
    Rutele nu ating niciodata DB direct — trec prin acest repository.
    """

    model = Frizer


    def get_frizer(self) -> Frizer | None:
        """Returneaza frizerul existent sau None daca nu exista."""
        return self.db.query(Frizer).first()

    def get_image_frizer(self) -> str | None:
        """Returneaza calea catre imaginea frizerului sau None daca nu exista."""
        frizer = self.get_frizer()
        return frizer.image_path if frizer else None
        
    def update_fields_frizer(self, name: str, description: str, image_path: str | None = None) -> Frizer:
        """Actualizeaza numele si descrierea frizerului, creand un nou record daca e necesar."""
        frizer = self.get_frizer()
        if not frizer:
            frizer = Frizer(name=name, description=description, image_path=image_path)
            return self.create(frizer)
        else:
            frizer.name = name
            frizer.description = description
            frizer.image_path = image_path if image_path else frizer.image_path # pastreaza imaginea existenta daca nu se furnizeaza una noua
            return self.update(frizer)

    def delete_frizer(self) -> None:
        """Sterge frizerul existent, daca exista."""
        frizer = self.get_frizer()
        if frizer:
            self.db.delete(frizer)
            self.db.commit()