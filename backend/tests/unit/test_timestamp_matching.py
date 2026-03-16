import json
from pathlib import Path

from app.modules.timeline.matcher import match_images_to_segments


# Finner fixtures-mappen relativt til denne testfilen
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "simple_case"


def load_json(filename: str) -> dict:
    """
    Leser en JSON-fil fra fixtures-mappen og returnerer innholdet som dict.
    """
    with open(FIXTURE_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


def test_match_images_to_expected_segments():
    """
    Tester at bildene matches til de segmentene vi forventer
    i simple_case-fixturen.
    """
    transcript_data = load_json("transcript.json")
    image_data = load_json("images.json")
    expected_data = load_json("expected_matches.json")

    actual_matches = match_images_to_segments(transcript_data, image_data)

    # PRINT RESULTATENE
    print("\nImage → Segment matches\n")
    for match in actual_matches:
        print(
            f"{match['image_id']} -> {match['matched_segment_id']} "
            f"(distance: {match['distance_seconds']} sec)"
        )

    # Vi sammenligner bare feltene vi faktisk bryr oss om i denne testen
    simplified_actual = [
        {
            "image_id": match["image_id"],
            "matched_segment_id": match["matched_segment_id"],
        }
        for match in actual_matches
    ]

    assert simplified_actual == expected_data["matches"]