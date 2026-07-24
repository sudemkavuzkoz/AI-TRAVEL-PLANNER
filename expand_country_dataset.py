import os
import re
import time
from pathlib import Path

from travel_extractor import scrape_wikipedia

COUNTRIES = [
    {
        "slug": "italya",
        "name": "İtalya",
        "wiki_url": "https://tr.wikipedia.org/wiki/%C4%B0talya",
        "highlights": [
            "Rönesans sanatının doğduğu topraklar; Roma, Floransa, Venedik ve Milan gibi şehirler tarih ve mimari açısından zengindir.",
            "Piza Kulesi, Kolizeum, Sistine Şapeli ve Leonardo da Vinci mirası ülkeyi kültür turizmi açısından çok güçlü kılar.",
            "Toskana, Amalfi Kıyısı, Cinque Terre ve Sicilya, doğal güzellik ve sahil deneyimleri sunar.",
            "İtalyan mutfağı pizza, pasta, risotto, gelato ve bölgesel şaraplarla dünya çapında ünlüdür.",
            "Yaz aylarında Akdeniz sahilleri çok yoğun olur; ilkbahar ve sonbahar daha keyifli gezme dönemleridir."
        ],
    },
    {
        "slug": "norveç",
        "name": "Norveç",
        "wiki_url": "https://tr.wikipedia.org/wiki/Norve%C3%A7",
        "highlights": [
            "Fiyortlar, dağlar, ormanlar ve buzullar Norveç'i dünya çapında doğa turizmi merkezi yapar.",
            "Bergen, Oslo, Tromsø ve Lofoten, şehir hayatı ile doğal manzara deneyimini bir araya getirir.",
            "Kuzey Işıkları, yaz aylarında gece yarısı güneşi ve sürükleyici kıyı rotaları ülkeyi farklı kılar.",
            "Bisiklet, yürüyüş, kano ve balık avcılığı gibi açık hava aktiviteleri oldukça gelişmiştir.",
            "Soğuk iklimine rağmen mükemmel altyapı, temiz şehirler ve dış mekan deneyimleri sık ziyaret edilmesini sağlar."
        ],
    },
    {
        "slug": "isvicre",
        "name": "İsviçre",
        "wiki_url": "https://tr.wikipedia.org/wiki/%C4%B0svi%C3%A7re",
        "highlights": [
            "Alpler, kristal göller, dağ köyleri ve yüksek demiryolu rotaları İsviçre'yi masalsı kılar.",
            "Zermatt, Lucerne, Interlaken ve Jungfrau bölgesi açık hava tutkunları için çok güçlü rotalardır.",
            "Şehirler temiz, güvenli ve düzenlidir; ulaşım sistemi çok verimlidir.",
            "Çikolata, saatçilik, dağ köyü kültürü ve mükemmel manzaralar ülkeyi romantik ve sakin bir destinasyon yapar.",
            "Yazda trekking, kışta kayak ve snowboard açısından çok güçlü bir destinasyondur."
        ],
    },
    {
        "slug": "fransa",
        "name": "Fransa",
        "wiki_url": "https://tr.wikipedia.org/wiki/Fransa",
        "highlights": [
            "Paris, Louvre Müzesi, Eyfel Kulesi ve Champs-Élysées ile dünyanın en çok ziyaret edilen şehirlerinden biridir.",
            "Provence, Dordogne, Loire Vadisi ve Côte d'Azur, şatolar, köyler ve kıyı manzaralarıyla dikkat çeker.",
            "Sanat, moda, mutfak, şarap ve tarih Fransa'yı çok katmanlı bir rota haline getirir.",
            "Bordeaux, Lyon, Nice, Marseille ve Strasbourg farklı kültür ve şehir deneyimleri sunar.",
            "Fransa gezisinde şehir, kıyı, şarap ve doğa aynı anda deneyimlenebilir."
        ],
    },
    {
        "slug": "japonya",
        "name": "Japonya",
        "wiki_url": "https://tr.wikipedia.org/wiki/Japonya",
        "highlights": [
            "Tokyo, Kyoto, Osaka ve Nara, gelenek ile moderniteyi aynı anda yaşatan şehirlerdir.",
            "Tapınaklar, bahçeler, çay seremonileri ve festival kültürü Japonya'yı benzersiz kılar.",
            "Hiroşima, Miyajima ve Fuji Dağı, tarihi ve doğal güzellik açısından güçlü rota parçalarıdır.",
            "Sushiden ramen'e, manga kültüründen teknoloji merkezlerine kadar çok geniş bir deneyim sunar.",
            "İlkbaharda kiraz çiçeği, sonbaharda yaprak renkleri ve kışın kar manzaraları mevsimsel güzellikler sunar."
        ],
    },
    {
        "slug": "yeni_zelanda",
        "name": "Yeni Zelanda",
        "wiki_url": "https://tr.wikipedia.org/wiki/Yeni_Zelanda",
        "highlights": [
            "Milford Sound, Fiordland, Queenstown ve Rotorua gibi bölgeler doğa tutkunları için vazgeçilmezdir.",
            "Sörf, trekking, kayak, dağ bisikleti ve safari gibi açık hava aktiviteleri çok zengindir.",
            "Maoriler'in kültürü, geleneksel müzik ve yemekleri ülkeye özgü bir karakter katar.",
            "Kısa mesafelerde değişen manzaralar, temiz hava ve sakin yollar ülkeyi çok çekici yapar.",
            "Yolculuk planında doğal güzellikler önce gelmeli; ülke birçok farklı ekoturizm rotası sunar."
        ],
    },
    {
        "slug": "nepal",
        "name": "Nepal",
        "wiki_url": "https://tr.wikipedia.org/wiki/Nepal",
        "highlights": [
            "Everest bölgesi, trekking rotaları, dağ köyleri ve Himalaya manzaralarıyla macera turizmi için başlıca destinasyonlardan biridir.",
            "Katmandu Vadisi, Bhaktapur ve Patan, tarihi tapınaklar ve kültürel miras açısından çok güçlüdür.",
            "Budizm ve Hinduizm'in etkisini taşıyan dini ve manevi dokusu ziyaretçilere farklı bir deneyim sunar.",
            "Dağ yürüyüşleri, tepe kampı, kültürel şehir gezileri ve fotoğrafçılık için mükemmel bir ülke.",
            "En iyi dönemler ilkbahar ve sonbahardır; bu dönemlerde hava daha dengeli olur."
        ],
    },
    {
        "slug": "filipinler",
        "name": "Filipinler",
        "wiki_url": "https://tr.wikipedia.org/wiki/Filipinler",
        "highlights": [
            "7.000'den fazla ada, turkuaz denizler, beyaz kumsallar ve dalış noktalarıyla tropik bir cennettir.",
            "Palawan, Boracay, Cebu ve Bohol, plaj, şnorkel ve adalar arası seyahat açısından öne çıkar.",
            "El Nido ve Coron, berrak sularda dalış ve doğal güzellik açısından çok popülerdir.",
            "Yöresel mutfak, sahil kasabaları ve adalar arası feribot rotaları ülkedeki deneyimi zenginleştirir.",
            "Mart-Mayıs ve Kasım-Şubat arası daha uygun dönemler olarak tercih edilir."
        ],
    },
    {
        "slug": "peru",
        "name": "Peru",
        "wiki_url": "https://tr.wikipedia.org/wiki/Peru",
        "highlights": [
            "Machu Picchu, Sacred Valley, Cusco ve And Dağları Peru'nun en ikonik rotalarıdır.",
            "İnka medeniyetinin mirası, tarihi şehirler ve dağ rotaları ülkeyi arkeoloji ve doğa turizmi için özel kılar.",
            "Lima, Cusco, Arequipa ve Iquitos farklı bölgelerden deneyim sunan şehirlerdir.",
            "Mutfak kültürü, özellikle ceviche, lomo saltado ve pisco sour ile dikkat çeker.",
            "Mayıs-Eylül arası And Dağları için daha uygun dönemlerdir."
        ],
    },
    {
        "slug": "brezilya",
        "name": "Brezilya",
        "wiki_url": "https://tr.wikipedia.org/wiki/Brezilya",
        "highlights": [
            "Rio de Janeiro, Salvador, Fernando de Noronha ve Amazon Ormanı Brezilya'da çok farklı deneyimler sunar.",
            "Carnaval, samba kültürü, sahil şehirleri ve yeşil dağ manzaraları dünya çapında tanınır.",
            "Amazon, kuş çeşitliliği, su yolları ve keşif turizmi açısından çok güçlü bir alan sağlar.",
            "Brezilya mutfağı, churrasco, feijoada ve tropikal meyvelerle dikkat çeker.",
            "Yılın büyük bölümünde sıcak ve nemli bir iklim hakimdir; kıyı bölgeleri yazın çok popüler olur."
        ],
    },
    {
        "slug": "arjantin",
        "name": "Arjantin",
        "wiki_url": "https://tr.wikipedia.org/wiki/Arjantin",
        "highlights": [
            "Buenos Aires, tango kültürü, neoklasik mimari ve gece hayatıyla öne çıkar.",
            "Patagonya, Perito Moreno Buzulu ve El Calafate, doğa ve macera turizmi açısından çok güçlüdür.",
            "Mendoza, şarap üretimi ve dağ manzaralarıyla önemli bir rota oluşturur.",
            "Uçsuz bucaksız pampalar, estancias ve şehir kültürü ülkeyi zengin kılar.",
            "Arjantin gezisi hem kültür hem de açık hava deneyimi sunan bir seyahat planı olarak öne çıkar."
        ],
    },
    {
        "slug": "kanada",
        "name": "Kanada",
        "wiki_url": "https://tr.wikipedia.org/wiki/Kanada",
        "highlights": [
            "Rocky Dağları, Banff, Jasper, Vancouver ve Toronto, Kanada'nın en çekici rota parçalarıdır.",
            "Büyük Göller, ormanlar, dağlar ve kuzey bölgeleri doğal güzellik açısından çok geniş bir alan sunar.",
            "Kuzey kutbu yakınındaki manzaralar, balıkçılık, kamp ve doğa yürüyüşleri için çok güçlüdür.",
            "Kanada, sakin şehir yaşamı, açık hava rekreasyonu ve doğal koruma alanlarıyla öne çıkar.",
            "Yaz aylarında trekking ve kano, kışın kayak ve kar manzarası için ideal bir destinasyondur."
        ],
    },
    {
        "slug": "guney_afrika",
        "name": "Güney Afrika",
        "wiki_url": "https://tr.wikipedia.org/wiki/G%C3%BCney_Afrika_Cumhuriyeti",
        "highlights": [
            "Cape Town, Table Mountain, Cape Peninsula ve Winelands, ülkenin en etkileyici bölgelerindendir.",
            "Kruger Milli Parkı, safari deneyimi ve vahşi yaşam izleme açısından dünyaca ünlüdür.",
            "Şehirlerin farklı kültürel dokusu, müzik, mutfak ve sanat hayatı çok çeşitlidir.",
            "Sahil, doğa, şehir ve safari aynı yolculukta deneyimlenebilir.",
            "Mayıs-Eylül arası safari için daha uygun, yaz ayları şehir gezisi için keyiflidir."
        ],
    },
    {
        "slug": "fas",
        "name": "Fas",
        "wiki_url": "https://tr.wikipedia.org/wiki/Fas",
        "highlights": [
            "Marrakesh, Fes, Chefchaouen ve Sahara Çölü Fas'ın en tanınmış rota parçalarıdır.",
            "Renkli pazarlar, medinalar, geleneksel el sanatları ve otantik konaklar çok güçlü bir kültür deneyimi sunar.",
            "Sahra Çölü'nde kum tepeleri, çadırlı kamp ve yıldızlı geceler unutulmazdır.",
            "Fas mutfağı, tagine, couscous, harissa ve çay kültürüyle öne çıkar.",
            "İlkbahar ve sonbahar, sıcak ve kurak iklim nedeniyle daha rahat seyahat dönemleridir."
        ],
    },
    {
        "slug": "turkiye",
        "name": "Türkiye",
        "wiki_url": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye",
        "highlights": [
            "İstanbul, Kapalıçarşı, Ayasofya, Topkapı Sarayı ve Boğaziçi ile tarih ile modern yaşamı bir araya getirir.",
            "Kapadokya, Antalya, İzmir, Çanakkale, Safranbolu ve Şanlıurfa farklı rota seçenekleri sunar.",
            "Ülke hem Avrupa hem Asya'da yer alır; bu nedenle kültür, mutfak ve coğrafya açısından çok zengindir.",
            "Yemek kültürü, hamam geleneği, tarihî kalıntılar ve doğal güzellikler Türkiye'yi çok yönlü bir destinasyon yapar.",
            "İlkbahar ve sonbahar, şehir gezisi ve doğa rotası için en dengeli dönemlerdir."
        ],
    },
]


def build_country_text(country):
    wiki_text = ""
    try:
        wiki_text = scrape_wikipedia(country["wiki_url"])
    except Exception as e:
        wiki_text = f"Wiki verisi alınamadı: {e}"

    lines = []
    lines.append(f"# {country['name']}")
    lines.append("")
    lines.append("## Genel bakış")
    lines.append(f"{country['name']}, kültür, tarih, doğa ve mutfak açısından dünya çapında öne çıkan bir ülkedir. Bu belge, gezginlerin ülkeyi daha iyi anlaması için kapsamlı bir rehber niteliği taşır.")
    lines.append("")
    lines.append("## Neden ziyaret edilmeli?")
    for highlight in country["highlights"]:
        lines.append(f"- {highlight}")
    lines.append("")
    lines.append("## Wikipedia temel bilgisi")
    lines.append(wiki_text[:4000])
    lines.append("")
    lines.append("## Kısa seyahat özeti")
    lines.append(f"{country['name']} gezisinde şehir merkezleri, doğal güzellikler, yerel mutfak ve kültürel etkinlikler aynı anda deneyimlenebilir. En iyi plan, ülkenin öne çıkan bölgelerini bir rota halinde birleştirmektir.")
    lines.append("")
    lines.append("## Önerilen ziyaret yaklaşımı")
    lines.append("- Şehir merkezlerinde tarihi alanları keşfedin.")
    lines.append("- Doğal alanlara ise en az bir gün ayırın.")
    lines.append("- Yerel mutfak deneyimini ihmal etmeyin.")
    lines.append("- İhtiyaçlarınıza göre mevsim seçimini yapın.")
    return "\n".join(lines)


def write_country_files(output_dir="travel_data"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for country in COUNTRIES:
        filepath = output_dir / f"country_{country['slug']}.txt"
        content = build_country_text(country)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("--- METADATA ---\n")
            f.write(f"SOURCE_URL: {country['wiki_url']}\n")
            f.write(f"FILE_NAME: {filepath.name}\n")
            f.write("PROCESSED_DATE: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
            f.write("----------------\n\n")
            f.write(content)
        created.append(str(filepath))
    return created


if __name__ == "__main__":
    files = write_country_files()
    print("Oluşturulan dosyalar:")
    for file in files:
        print(file)
