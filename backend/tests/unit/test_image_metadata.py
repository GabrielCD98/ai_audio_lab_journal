from pathlib import Path

from app.modules.images.metadata import extract_image_date, extract_image_time


FIXTURE_IMAGE = (
    Path(__file__).resolve().parent.parent / "fixtures" / "images" / "1000002034.jpg"
)


def test_extract_image_date_and_time():
    """
    Verifies that date and time are read from the JPG metadata.
    """
    image_date = extract_image_date(FIXTURE_IMAGE)
    image_time = extract_image_time(FIXTURE_IMAGE)

    print(f"\nMetadata date: {image_date}")
    print(f"Metadata time: {image_time}")

    assert image_date == "2026-03-14"
    assert image_time == "17:59:35"

