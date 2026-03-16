from datetime import datetime
from typing import Any


def parse_iso_datetime(value: str) -> datetime:
    """
    Konverterer en ISO-8601 tidsstreng til et Python datetime-objekt.

    Eksempel input:
        "2026-03-06T10:01:47"

    Output:
        datetime(2026, 3, 6, 10, 1, 47)

    Dette brukes fordi JSON-testdataene lagrer tid som tekst.
    """
    return datetime.fromisoformat(value)


def get_image_timestamp(image: dict[str, Any]) -> datetime | None:
    """
    Henter tidspunktet et bilde ble tatt fra metadata.

    Input:
        image-dict fra images.json

    Returnerer:
        datetime-objekt hvis metadata finnes
        None hvis metadata mangler

    Vi bruker feltet 'source_created_at' fordi dette representerer
    tidspunktet bildet faktisk ble tatt (fra EXIF eller annen metadata).
    """
    raw_value = image.get("source_created_at")

    # Hvis metadata mangler returnerer vi None
    if not raw_value:
        return None

    # Konverter ISO-streng til datetime
    return parse_iso_datetime(raw_value)


def get_segment_time_bounds(segment: dict[str, Any]) -> tuple[datetime, datetime]:
    """
    Henter start- og sluttidspunktet til et transkripsjonssegment.

    Input:
        ett segment fra transcript.json

    Output:
        (start_datetime, end_datetime)

    Segmentene har allerede absolutte tider i testdataene våre.
    """
    start = parse_iso_datetime(segment["absolute_start"])
    end = parse_iso_datetime(segment["absolute_end"])
    return start, end


def is_within_segment(
    image_time: datetime,
    segment_start: datetime,
    segment_end: datetime,
) -> bool:
    """
    Sjekker om bildet ble tatt innenfor tidsintervallet til segmentet.

    Returnerer:
        True  -> bildet ligger inne i segmentet
        False -> bildet ligger utenfor segmentet
    """
    return segment_start <= image_time <= segment_end


def seconds_to_segment(
    image_time: datetime,
    segment_start: datetime,
    segment_end: datetime,
) -> float:
    """
    Beregner avstanden i sekunder mellom et bilde og et segment.

    Hvis bildet ligger innenfor segmentet:
        returnerer 0.0

    Hvis bildet ligger før segmentet:
        returnerer sekunder til segment_start

    Hvis bildet ligger etter segmentet:
        returnerer sekunder siden segment_end

    Denne verdien brukes senere til å finne segmentet
    som er nærmest bildet i tid.
    """

    # Hvis bildet allerede ligger inne i segmentet
    if is_within_segment(image_time, segment_start, segment_end):
        return 0.0

    # Hvis bildet ble tatt før segmentet startet
    if image_time < segment_start:
        return (segment_start - image_time).total_seconds()

    # Hvis bildet ble tatt etter segmentet sluttet
    return (image_time - segment_end).total_seconds()


def find_best_segment_for_image(
    image: dict[str, Any],
    segments: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, float]:
    """
    Finner hvilket transkripsjonssegment som passer best til et bilde.

    Strategi:
        1. Hent bildetidspunkt
        2. Gå gjennom alle segmenter
        3. Regn avstand mellom bilde og segment
        4. Velg segmentet med lavest avstand

    Returnerer:
        (beste_segment, avstand_i_sekunder)

    Hvis bildet ikke har timestamp returneres:
        (None, inf)
    """

    # Hent tidspunktet bildet ble tatt
    image_time = get_image_timestamp(image)

    # Hvis metadata mangler kan vi ikke matche
    if image_time is None:
        return None, float("inf")

    best_segment = None
    best_distance = float("inf")

    # Iterer gjennom alle transkripsjonssegmenter
    for segment in segments:

        # Hent tidsintervallet til segmentet
        segment_start, segment_end = get_segment_time_bounds(segment)

        # Beregn avstand mellom bilde og segment
        distance = seconds_to_segment(image_time, segment_start, segment_end)

        # Hvis dette segmentet er nærmere enn tidligere kandidater
        if distance < best_distance:
            best_segment = segment
            best_distance = distance

    return best_segment, best_distance


def build_match_result(
    image: dict[str, Any],
    segment: dict[str, Any] | None,
    distance_seconds: float,
) -> dict[str, Any]:
    """
    Lager et strukturert resultatobjekt for en bilde-match.
    """

    if segment is None:
        return {
            "image_id": image["image_id"],
            "matched_segment_id": None,
            "match_type": "no_match",
            "distance_seconds": None,
        }

    if distance_seconds == 0:
        match_type = "within_segment"
        matched_segment_id = segment["segment_id"]
    elif distance_seconds <= 10:
        match_type = "near_segment"
        matched_segment_id = segment["segment_id"]
    elif distance_seconds <= 30:
        match_type = "weak_match"
        matched_segment_id = segment["segment_id"]
    else:
        match_type = "no_match"
        matched_segment_id = None

    return {
        "image_id": image["image_id"],
        "matched_segment_id": matched_segment_id,
        "match_type": match_type,
        "distance_seconds": None if matched_segment_id is None else distance_seconds,
    }

def match_images_to_segments(
    transcript_data: dict[str, Any],
    image_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Hovedfunksjonen i matcher-modulen.

    Input:
        transcript_data -> JSON-data fra transcript.json
        image_data      -> JSON-data fra images.json

    Prosess:
        1. hent alle segmenter
        2. hent alle bilder
        3. finn beste segment for hvert bilde
        4. lag et resultatobjekt
        5. returner liste med matcher

    Output:
        liste av match-objekter
    """

    segments = transcript_data["segments"]
    images = image_data["images"]

    results = []

    # Match hvert bilde mot segmentene
    for image in images:

        # Finn beste segment
        segment, distance = find_best_segment_for_image(image, segments)

        # Lag strukturert resultat
        result = build_match_result(image, segment, distance)

        results.append(result)

    return results