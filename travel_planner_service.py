import os
from typing import List, Dict, Any

from embedding import create_embedding
from database import search_similar_chunks
from model import generate_response
from travel_planner_utils import get_places_for_country, build_google_maps_url


def _build_rag_context(conn, query: str, country: str, top_k: int = 20):
    query_embedding = create_embedding(query)
    retrieved_chunks = search_similar_chunks(conn, query_embedding, top_k=top_k)

    context_parts: List[str] = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(f"[Kaynak {i}] {chunk['source']}: {chunk['text']}")

    places = get_places_for_country(country)
    if places:
        place_catalog = []
        for place in places[:10]:
            place_catalog.append(
                f"- {place.get('Place_Name', '')} | {place.get('City', '')} | {place.get('Country', '')} | {place.get('Famous_For', '')}"
            )
        context_parts.append("[Yer Katalogu]\n" + "\n".join(place_catalog))

    return "\n\n".join(context_parts), retrieved_chunks


def build_trip_plan(conn, country: str, days: int, request: str, favorites: List[str] | None = None):
    favorite_context = ""
    if favorites:
        favorite_context = f"Kullanıcının favori yerleri: {', '.join(favorites)}"

    query = (
        f"{country} için {days} günlük seyahat planı hazırla. "
        f"Sabah, öğle ve akşam saatleriyle düzenle. "
        f"Müzeler, yemek, tatlı, yerel deneyimler ve konum bilgisi ekle. "
        f"{request} {favorite_context}".strip()
    )

    context_text, retrieved_chunks = _build_rag_context(conn, query, country=country, top_k=20)

    prompt = f"""Sen profesyonel bir seyahat asistanısın. Aşağıdaki bağlamı (CONTEXT) kullanarak kullanıcı için {days} günlük ÇOK KAPSAMLI ve detaylı bir plan üret.

KURALLAR:
1. YANITINI KESİNLİKLE TAMAMEN TÜRKÇE OLARAK VER.
2. SADECE bağlamdaki (CONTEXT) bilgilere dayan. Halüsinasyon yapma, dışarıdan mekan uydurma.
3. Planı Sabah / Öğle / Akşam şeklinde düzenle.
4. Müzeler, yemek, tatlı, kahve, alışveriş gibi deneyimleri SADECE bağlamda geçiyorsa ekle.
5. Her önerinin sonuna Google Maps bağlantısı formatında [📍 İsim](https://www.google.com/maps/search/?api=1&query=İsim) ekle.
6. Eğer kullanıcının istediği spesifik bir bilgi bağlamda (CONTEXT) yoksa, bunu açıkça ve dürüstçe belirt. Yalan mekan isimleri (örn. "Kafeler", "Künefe" adlı restoran) türetme.

BAĞLAM:
{context_text}

SORU: {query}
CEVAP:"""

    response = generate_response(prompt)
    places = get_places_for_country(country)[:6]
    maps_section = "\n\n### Haritada görüntüleyebileceğiniz öneriler\n"
    maps_section += "\n".join(
        f"- {place.get('Place_Name', '')} ({place.get('City', '')}) — {build_google_maps_url(place)}"
        for place in places
    )

    return response + "\n\n" + maps_section, retrieved_chunks, places
