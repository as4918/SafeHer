import requests
import config

BASE_URL = "https://places.googleapis.com/v1/places:autocomplete"


def search_places(query):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": config.GOOGLE_MAPS_API_KEY,
    }

    body = {
        "input": query
    }

    response = requests.post(
        BASE_URL,
        headers=headers,
        json=body,
        timeout=10,
    )

    if response.status_code != 200:
        return []

    data = response.json()

    suggestions = []

    for item in data.get("suggestions", []):

        place = item.get("placePrediction")

        if place:

            suggestions.append({
                "text": place["text"]["text"],
                "place_id": place["placeId"],
            })

    return suggestions