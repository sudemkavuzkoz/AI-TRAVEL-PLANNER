import re
import time
from pathlib import Path

COUNTRY_PLACE_DATA = {
    "Italy": {
        "famous_cafes": ["Caffè Florian", "Sant'Eustachio Il Caffè", "Caffè Pasticceria Gilli"],
        "famous_restaurants": ["Osteria Francescana", "Ristorante Aroma", "Trattoria da Enzo"],
        "famous_sweets": ["Gelato", "Tiramisu", "Cannoli"],
        "famous_museums": ["Uffizi Galerisi", "Kolezyum", "Vatikan Müzeleri"]
    },
    "France": {
        "famous_cafes": ["Café de Flore", "Les Deux Magots", "Angelina"],
        "famous_restaurants": ["Le Meurice", "Arpège", "L'Ambroisie"],
        "famous_sweets": ["Macaron", "Éclair", "Crème Brûlée"],
        "famous_museums": ["Louvre Müzesi", "Musée d'Orsay", "Centre Pompidou"]
    },
    "Japan": {
        "famous_cafes": ["Kissa Sakae", "Cafe Kitsune", "Ain Soph. Journey"],
        "famous_restaurants": ["Sukiyabashi Jiro", "Narisawa", "Sushi Dai"],
        "famous_sweets": ["Matcha", "Mochi", "Daifuku"]
    },
    "Turkey": {
        "famous_cafes": ["Beyti", "Karaköy Güllüoğlu", "Kahve Dünyası"],
        "famous_restaurants": ["Nusr-Et", "Mükellef", "Neolokal"],
        "famous_sweets": ["Baklava", "Künefe", "Turkish Delight"],
        "famous_museums": ["Topkapı Sarayı", "Ayasofya", "İstanbul Arkeoloji Müzeleri"]
    },
    "Spain": {
        "famous_cafes": ["El Nacional", "Laie", "Nomad Coffee"],
        "famous_restaurants": ["Celler de Can Roca", "Azurmendi", "El Bulli"],
        "famous_sweets": ["Churros", "Tortilla Española", "Crema Catalana"]
    },
    "Germany": {
        "famous_cafes": ["Café Einstein", "Brammibal's", "Kaffeehaus"],
        "famous_restaurants": ["Schneider's", "Restaurant Tim Raue", "Möwenpick"],
        "famous_sweets": ["Black Forest Cake", "Apfelstrudel", "Pretzel"]
    },
    "Greece": {
        "famous_cafes": ["A for Athens", "Kafeneio", "The Coffee Lab"],
        "famous_restaurants": ["Spondi", "Hytra", "Noma"],
        "famous_sweets": ["Baklava", "Loukoumades", "Galaktoboureko"]
    },
    "Portugal": {
        "famous_cafes": ["A Brasileira", "Fábrica Coffee Roasters", "Café Majestic"],
        "famous_restaurants": ["Belcanto", "Cevicheria", "O Frade"],
        "famous_sweets": ["Pastel de Nata", "Queijada", "Bolo de Arroz"]
    },
    "Netherlands": {
        "famous_cafes": ["The Coffee Company", "Koffiehuis", "Café de Klos"],
        "famous_restaurants": ["Restaurant De Silveren Spiegel", "Restaurant De Kas", "Moeders"],
        "famous_sweets": ["Stroopwafel", "Dutch Apple Pie", "Poffertjes"]
    },
    "Belgium": {
        "famous_cafes": ["Café de l'Ange", "Caffè", "Koffiehuis"],
        "famous_restaurants": ["Comme Chez Soi", "Hof van Cleve", "L'Air du Temps"],
        "famous_sweets": ["Belgian Chocolate", "Waffles", "Speculoos"]
    },
    "Switzerland": {
        "famous_cafes": ["Café de l'Hotel", "Bistro", "Coffee Lab"],
        "famous_restaurants": ["Restaurant de l'Hôtel", "The Restaurant", "Bergrestaurant"],
        "famous_sweets": ["Swiss Chocolate", "Rösti", "Meringue"]
    },
    "Norway": {
        "famous_cafes": ["Tim Wendelboe", "Café", "Kaffehuset"],
        "famous_restaurants": ["Restaurant AOC", "Sushi", "Maaemo"],
        "famous_sweets": ["Kanelbolle", "Brownie", "Lemon Cake"]
    },
    "Sweden": {
        "famous_cafes": ["Drop Coffee", "Lilla Kaffekontoret", "Café"] ,
        "famous_restaurants": ["Operakällaren", "Frantzén", "Restaurant Oaxen"],
        "famous_sweets": ["Semla", "Kanelbullar", "Princess Cake"]
    },
    "Denmark": {
        "famous_cafes": ["Democratic Coffee", "The Coffee Collective", "Café Kitsuné"],
        "famous_restaurants": ["Noma", "Geranium", "Alchemist"],
        "famous_sweets": ["Kagemand", "Butter Cookies", "Danish Pastry"]
    },
    "Austria": {
        "famous_cafes": ["Café Central", "Hotel Sacher", "Café Landtmann"],
        "famous_restaurants": ["Mraz & Sohn", "Restaurant Steirereck", "Munchner"],
        "famous_sweets": ["Sachertorte", "Apfelstrudel", "Krapfen"]
    },
    "Poland": {
        "famous_cafes": ["Koneser", "Coffee Heaven", "Miejsce"],
        "famous_restaurants": ["Nobu", "Chef's Table", "Koneser"],
        "famous_sweets": ["Oscypek", "Makowiec", "Pączki"]
    },
    "Czech Republic": {
        "famous_cafes": ["Café Savoy", "Kantýna", "Lokál"],
        "famous_restaurants": ["U Fleků", "La Degustation", "Kantýna"],
        "famous_sweets": ["Vetrník", "Trdelník", "Knedlíky"]
    },
    "Hungary": {
        "famous_cafes": ["Műhely", "Café Gerbeaud", "Művész Kávéház"],
        "famous_restaurants": ["Mazel Tov", "Onyx", "Costes"],
        "famous_sweets": ["Dobos Torte", "Lángos", "Gesztenyepüré"]
    },
    "Romania": {
        "famous_cafes": ["Café Verona", "The Coffee Shop", "Bistro"],
        "famous_restaurants": ["HORA", "Restaurant Caru' cu Bere", "Mocanita"],
        "famous_sweets": ["Papanic", "Cozonac", "Tort"]
    },
    "Bulgaria": {
        "famous_cafes": ["The Little Things", "Café", "Moma"],
        "famous_restaurants": ["Made in Blue", "Moma", "The Little Things"],
        "famous_sweets": ["Baklava", "Tulumba", "Banitsa"]
    },
    "Croatia": {
        "famous_cafes": ["Tanjga", "Café Bar", "Mala"],
        "famous_restaurants": ["Restaurant 360", "Morten's", "Santos"],
        "famous_sweets": ["Fritule", "Krempita", "Strudel"]
    },
    "Slovenia": {
        "famous_cafes": ["Café", "Kava", "Mala"],
        "famous_restaurants": ["Restaurant Druga Violina", "Gostilna Sokol", "Mala"],
        "famous_sweets": ["Potica", "Prekmurska Gibanica", "Kremna Rezina"]
    },
    "Slovakia": {
        "famous_cafes": ["Mincovna", "Kava", "Café"],
        "famous_restaurants": ["Lokál Dlouhááá", "U Fleků", "Mincovna"],
        "famous_sweets": ["Trdelník", "Knedlíky", "Tort"]
    },
    "Serbia": {
        "famous_cafes": ["Kafana", "Café", "Mala"],
        "famous_restaurants": ["Restaurant A", "Kafana", "Mala"],
        "famous_sweets": ["Baklava", "Tulumba", "Cevapi"]
    },
    "Bosnia and Herzegovina": {
        "famous_cafes": ["Café", "Kafana", "Mala"],
        "famous_restaurants": ["Tanjga", "Mala", "Kafana"],
        "famous_sweets": ["Baklava", "Tulumba", "Cevapi"]
    },
    "Albania": {
        "famous_cafes": ["Cafe", "Kafe", "Caffè"],
        "famous_restaurants": ["Restaurant", "Tavë", "Kafe"],
        "famous_sweets": ["Baklava", "Byrek", "Tavë"]
    },
    "Greece": {
        "famous_cafes": ["A for Athens", "Kafeneio", "The Coffee Lab"],
        "famous_restaurants": ["Spondi", "Hytra", "Noma"],
        "famous_sweets": ["Baklava", "Loukoumades", "Galaktoboureko"]
    }
}


def enrich_country_content(country_name: str, content: str) -> str:
    data = COUNTRY_PLACE_DATA.get(country_name)
    lines = content.splitlines()
    
    if "## Meşhur Kafeler" not in lines:
        if data:
            museums = ", ".join(data.get("famous_museums", ["Tarihi Şehir Merkezleri", "Yerel Müzeler", "Ulusal Galeri"]))
            cafes = ", ".join(data.get("famous_cafes", ["Lokal Kafeler", "Tarihi Meydan Kahvecileri", "Modern Espresso Barları"]))
            rests = ", ".join(data.get("famous_restaurants", ["Geleneksel Sokak Lezzetleri", "Şefin Restoranı", "Yöresel Mutfak Merkezleri"]))
            sweets = ", ".join(data.get("famous_sweets", ["Sokak Tatlıları", "Yerel Fırın Ürünleri", "Geleneksel Tatlılar"]))
        else:
            museums = "Tarihi Şehir Merkezleri, Yerel Müzeler, Ulusal Galeri"
            cafes = "Lokal Kafeler, Tarihi Meydan Kahvecileri, Modern Espresso Barları"
            rests = "Geleneksel Sokak Lezzetleri, Yöresel Mutfak Merkezleri, Popüler Meydan Restoranları"
            sweets = "Sokak Tatlıları, Yerel Fırın Ürünleri, Geleneksel Tatlılar"

        lines.extend([
            "",
            "## Meşhur Müzeler ve Tarihi Yerler",
            f"- {country_name} seyahatinizde {museums} gibi önemli kültürel mekanları ziyaret edebilirsiniz.",
            "",
            "## Meşhur Kafeler",
            f"- {country_name} için öne çıkan kafe deneyimleri arasında {cafes} gibi mekanlar sıklıkla önerilir.",
            "",
            "## Meşhur Restoranlar",
            f"- {country_name} mutfağını deneyimlemek için {rests} gibi mekanlar tercih edilir.",
            "",
            "## Meşhur Tatlıcılar ve Tatlılar",
            f"- {country_name} gezisinde {sweets} gibi yerel tatlılar mutlaka denenmelidir."
        ])
    return "\n".join(lines)


def update_country_files(output_dir="travel_data"):
    from pathlib import Path
    output_dir = Path(output_dir)
    count = 0
    for path in output_dir.glob("country_*.txt"):
        text = path.read_text(encoding="utf-8")
        
        # Extract country name from filename, e.g. "country_united_states.txt" -> "United States"
        basename = path.stem.replace("country_", "")
        country_name = " ".join(word.capitalize() for word in basename.split("_"))
        
        updated = enrich_country_content(country_name, text)
        if len(updated) > len(text):
            path.write_text(updated, encoding="utf-8")
            count += 1
            
    print(f"Toplam {count} ülke dosyasına müze, kafe, restoran ve tatlıcı bilgileri eklendi.")


if __name__ == "__main__":
    update_country_files()
