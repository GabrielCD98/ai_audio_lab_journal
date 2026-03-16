from datetime import datetime
from pathlib import Path

from PIL import Image


def _get_image_datetime(image_path: str | Path) -> datetime:
    """
    Read the EXIF timestamp from a JPG image and convert it to datetime.
    """
    path = Path(image_path)

    if path.suffix.lower() != ".jpg":
        raise ValueError("Filen må være et .jpg-bilde.")

    with Image.open(path) as image:
        exif_data = image.getexif()

    raw_datetime = exif_data.get(306) or exif_data.get(36867) or exif_data.get(36868)
    if not raw_datetime:
        raise ValueError(f"Fant ikke dato/klokkeslett i metadata for {path.name}.")

    return datetime.strptime(raw_datetime, "%Y:%m:%d %H:%M:%S")


def extract_image_date(image_path: str | Path) -> str:
    """
    Return the date from JPG metadata as YYYY-MM-DD.
    """
    image_datetime = _get_image_datetime(image_path)
    return image_datetime.date().isoformat()


def extract_image_time(image_path: str | Path) -> str:
    """
    Return the time from JPG metadata as HH:MM:SS.
    """
    image_datetime = _get_image_datetime(image_path)
    return image_datetime.time().isoformat()
