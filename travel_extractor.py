# -*- coding: utf-8 -*-
import os
import re
import time
import random
from urllib.parse import urlparse, unquote
import requests
from bs4 import BeautifulSoup
import wikipediaapi

try:
    import cloudscraper
except ImportError:  # pragma: no cover
    cloudscraper = None

# AI Travel Planner için anlamlı olan ve RAG (Embedding) için temizlenecek anahtar kelimeler
SECTIONS_OF_INTEREST = [
    # Türkçe
    "tarih", "tarihçe", "kültür", "turizm", "gezilecek", "ulaşım", "mutfak", "yemek", 
    "coğrafya", "mimari", "görülecek", "iklim", "sanat", "müze", "etkinlik", "aktivite",
    # İngilizce
    "history", "culture", "tourism", "transport", "cuisine", "food", "geography", 
    "architecture", "climate", "art", "museum", "attractions", "activities", "sights"
]

HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        "Connection": "keep-alive"
    }
]

def clean_filename(url):
    """URL'den temiz ve benzersiz bir dosya adı üretir."""
    parsed = urlparse(url)
    path = unquote(parsed.path).strip("/")
    clean_path = re.sub(r'[^a-zA-Z0-9_]', '_', path)
    if not clean_path:
        clean_path = "index"
    
    if "wikipedia.org" in parsed.netloc:
        prefix = "wiki_"
    elif "tripadvisor" in parsed.netloc:
        prefix = "tripadvisor_"
    else:
        prefix = "blog_"
        
    return prefix + clean_path + ".txt"

def should_keep_section(section_title):
    """Bölüm başlığının önemsiz (referans, kaynakça vb.) olup olmadığını kontrol eder.
    Artık çok daha kapsayıcı (neredeyse tüm içerik alınacak).
    """
    title_lower = section_title.lower()
    ignore_list = ["kaynakça", "dış bağlantılar", "notlar", "ayrıca bakınız", "references", "external links", "see also"]
    return not any(ignore in title_lower for ignore in ignore_list)

def extract_wiki_sections(sections, collected_data):
    """Wikipedia başlıklarını özyinelemeli (recursive) olarak tarar ve daha kapsamlı bilgi alır."""
    for section in sections:
        if should_keep_section(section.title):
            if section.text.strip():
                # Hata olasılığını sıfırlamak için klasik birleştirme kullanıyoruz
                text_block = "### Bölüm: " + section.title + "\n" + section.text.strip() + "\n"
                collected_data.append(text_block)
            # Alt bölümleri de mutlaka tara
            if section.sections:
                extract_wiki_sections(section.sections, collected_data)

def scrape_wikipedia(url):
    """Wikipedia API kullanarak sadece gerekli bölümleri çeker."""
    parsed = urlparse(url)
    lang = parsed.netloc.split(".")[0]
    page_title = unquote(parsed.path.split("/")[-1]).replace("_", " ")
    
    wiki = wikipediaapi.Wikipedia(
        user_agent="MyTravelRAGApp/1.0 (travelplanner@example.com)",
        language=lang
    )
    
    page = wiki.page(page_title)
    if not page.exists():
        return "Hata: Wikipedia sayfası bulunamadı (" + page_title + ")"
        
    content_blocks = []
    
    # Satır kaymalarından etkilenmeyen güvenli birleştirme:
    summary_text = "### Genel Özet\n" + page.summary.strip() + "\n"
    content_blocks.append(summary_text)
    
    extract_wiki_sections(page.sections, content_blocks)
    return "\n".join(content_blocks)

def scrape_general_blog(url):
    """Seyahat bloglarından gereksiz alanları temizleyerek ana metni alır."""
    headers = random.choice(HEADERS_LIST)
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        return "Hata: Sayfaya erişilemedi (" + str(e) + ")"
        
    soup = BeautifulSoup(response.text, "html.parser")
    
    for element in soup(["nav", "footer", "header", "aside", "script", "style", "noscript", ".comments", "#comments", ".sidebar", ".ads"]):
        element.decompose()
        
    title = soup.find("h1")
    title_text = title.text.strip() if title else "Başlıksız Makale"
    
    article_body = soup.find(["article", ".post-content", ".entry-content", ".content"])
    container = article_body if article_body else soup.body
    
    if not container:
        return "Hata: Sayfa içeriği çözümlenemedi."
        
    content_blocks = ["# " + title_text + "\n"]
    
    for elem in container.find_all(["h2", "h3", "h4", "p", "li"]):
        text = elem.text.strip()
        if not text or len(text) < 10:
            continue
            
        if elem.name == "li":
            content_blocks.append("- " + text)
        elif elem.name in ["h2", "h3", "h4"]:
            content_blocks.append("\n## " + text)
        else:
            content_blocks.append(text)
            
    return "\n".join(content_blocks)

def scrape_tripadvisor(url):
    """TripAdvisor sayfalarını kazımayı dener; başarısız olursa açıklayıcı metin döndürür."""
    if cloudscraper is None:
        return (
            "⚠️ TripAdvisor verisi çekilemedi.\n"
            "cloudscraper kütüphanesi yüklü değil.\n"
            f"Hedef URL: {url}"
        )

    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    })

    try:
        time.sleep(random.uniform(1.5, 3.0))
        response = scraper.get(url, timeout=20)

        if response.status_code == 403:
            return (
                "⚠️ TripAdvisor Bot Koruması Engeli (403 Forbidden):\n"
                "Bu sayfa TripAdvisor tarafından koruma altına alınmış olabilir.\n"
                "Kaynak URL: " + url + "\n"
                "Bu nedenle bu kaynak için metin verisi doğrudan çekilemedi."
            )

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("h1")
        title_text = title.text.strip() if title else "TripAdvisor Detayları"

        content_blocks = ["# " + title_text + "\n", "Kaynak URL: " + url + "\n"]

        items = soup.find_all(["div", "span"], class_=re.compile(r"(biGQs|comment|title|poi|restaurant)", re.I))
        unique_texts = set()
        for item in items:
            text = item.text.strip()
            if len(text) > 20 and text not in unique_texts:
                if not any(x in text.lower() for x in ["çerez", "cookie", "gizlilik", "tüm hakları", "site haritası"]):
                    unique_texts.add(text)
                    content_blocks.append("- " + text)

        if len(content_blocks) <= 2:
            paragraphs = soup.find_all("p")
            for p in paragraphs:
                text = p.text.strip()
                if len(text) > 30 and text not in unique_texts:
                    unique_texts.add(text)
                    content_blocks.append(text)

        if len(content_blocks) <= 2:
            return (
                "⚠️ TripAdvisor sayfası işlenemedi.\n"
                "Sayfa içeriği boş ya da erişilemez durumda.\n"
                "Kaynak URL: " + url
            )

        return "\n".join(content_blocks)

    except Exception as e:
        return (
            "⚠️ TripAdvisor verisi çekilemedi.\n"
            f"Hata: {e}\n"
            f"Hedef URL: {url}"
        )

from concurrent.futures import ThreadPoolExecutor, as_completed


def scrape_gezipgordum_country_page(url):
    """Gezip Gördüm ülke sayfasından ana metin ve ilgili linklerin metinlerini çıkarır."""
    headers = random.choice(HEADERS_LIST)
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        return f"Hata: Sayfa çekilemedi ({e})\nKaynak URL: {url}"

    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["nav", "footer", "header", "aside", "script", "style", "noscript", ".comments", "#comments", ".sidebar", ".ads"]):
        element.decompose()

    title = soup.find("h1")
    title_text = title.text.strip() if title else "Ülke Sayfası"
    blocks = [f"# {title_text}", f"Kaynak URL: {url}"]

    main_text = []
    for p in soup.find_all(["p", "li"]):
        text = " ".join(p.get_text(" ", strip=True).split())
        if len(text) > 20:
            main_text.append(text)

    if main_text:
        blocks.extend(main_text[:60])

    return "\n".join(blocks)


def process_single_url(url, output_dir, index, total):
    url = url.strip().strip(",").strip('"').strip("'")
    if not url:
        return

    if "tripadvisor" in url:
        print(f"[{index}/{total}] Atlanıyor (TripAdvisor resmi API desteği yok): {url}")
        return
        
    filename = clean_filename(url)
    filepath = os.path.join(output_dir, filename)
    
    print(f"[{index}/{total}] İşleniyor: {url}")
    
    if "wikipedia.org" in url:
        content = scrape_wikipedia(url)
    else:
        content = scrape_general_blog(url)
        
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("--- METADATA ---\n")
            f.write("SOURCE_URL: " + url + "\n")
            f.write("FILE_NAME: " + filename + "\n")
            f.write("PROCESSED_DATE: " + time.strftime('%Y-%m-%d %H:%M:%S') + "\n")
            f.write("----------------\n\n")
            f.write(content)
        print(f"   💾 Kaydedildi -> {filepath}\n")
    except Exception as e:
        print(f"   ❌ Dosya yazma hatası ({filename}): {str(e)}\n")

def process_and_save(urls, output_dir="travel_data"):
    """Tüm URL listesini EŞZAMANLI (multithreading) işler ve kaydeder."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print("📁 '" + output_dir + "' klasörü oluşturuldu.")
        
    total = len(urls)
    print(f"🚀 Toplam {total} URL EŞZAMANLI (Multithread) işleme alınıyor...\n")
    
    # 10 iş parçacığı (thread) ile paralel çalıştırarak hızı 10 katına çıkarıyoruz
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for index, url in enumerate(urls, 1):
            futures.append(executor.submit(process_single_url, url, output_dir, index, total))
            
        for future in as_completed(futures):
            # Hataları yakalamak için
            try:
                future.result()
            except Exception as e:
                print(f"Bilinmeyen thread hatası: {e}")

def save_country_page_as_txt(url, output_dir="travel_data", country_name=None):
    """Bir ülke sayfasını metin dosyası olarak kaydeder."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p]
    if country_name:
        slug = country_name
    elif path_parts:
        slug = path_parts[-1]
    else:
        slug = "country"

    slug = re.sub(r'[^a-zA-Z0-9]+', '_', slug).strip('_') or "country"
    filename = f"country_{slug}.txt"
    filepath = os.path.join(output_dir, filename)
    content = scrape_gezipgordum_country_page(url)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("--- METADATA ---\n")
        f.write("SOURCE_URL: " + url + "\n")
        f.write("FILE_NAME: " + filename + "\n")
        f.write("PROCESSED_DATE: " + time.strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.write("----------------\n\n")
        f.write(content)
    return filepath


def discover_gezipgordum_country_urls(base_url="https://gezipgordum.com/avrupa/", max_results=50):
    """Gezip Gördüm ülke sayfalarını bir kategori sayfasından keşfeder."""
    headers = random.choice(HEADERS_LIST)
    try:
        response = requests.get(base_url, headers=headers, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"[Hata] {base_url} çekilemedi: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    urls = []
    seen = set()
    for link in soup.find_all("a", href=True):
        href = link.get("href")
        if not href:
            continue
        try:
            parsed = urlparse(href)
        except Exception:
            continue
        if not parsed.netloc or "gezipgordum.com" not in parsed.netloc:
            continue
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) < 2:
            continue
        if path_parts[0] != "avrupa":
            continue
        if len(path_parts) != 2:
            continue
        country_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if country_url.endswith("/") and country_url not in seen:
            seen.add(country_url)
            urls.append(country_url)
        if len(urls) >= max_results:
            break

    return urls


def collect_gezipgordum_country_files(base_url="https://gezipgordum.com/avrupa/", output_dir="travel_data", max_results=50):
    """Ülke sayfalarını bulur, txt dosyalarına dönüştürür ve yazdırır."""
    country_urls = discover_gezipgordum_country_urls(base_url=base_url, max_results=max_results)
    if not country_urls:
        fallback_urls = [
            "https://gezipgordum.com/avrupa/italya/",
            "https://gezipgordum.com/avrupa/fransa/",
            "https://gezipgordum.com/avrupa/ispanya/",
            "https://gezipgordum.com/avrupa/almanya/",
            "https://gezipgordum.com/avrupa/yunanistan/",
        ]
        country_urls = fallback_urls

    saved_files = []
    for index, country_url in enumerate(country_urls, 1):
        country_name = country_url.rstrip("/").split("/")[-1]
        print(f"[{index}/{len(country_urls)}] Ülke verisi kaydediliyor: {country_name}")
        filepath = save_country_page_as_txt(country_url, output_dir=output_dir, country_name=country_name)
        saved_files.append(filepath)
    return saved_files


urls_list = [
    "https://tr.wikipedia.org/wiki/Carnavalet_M%C3%BCzesi",
    "https://tr.wikipedia.org/wiki/Picasso_M%C3%BCzesi_(Paris)",
    "https://tr.wikipedia.org/wiki/Louvre_M%C3%BCzesi",
    "https://tr.wikipedia.org/wiki/Paris",
    "https://tr.wikipedia.org/wiki/Fransa",
    "https://tr.wikipedia.org/wiki/Notre_Dame_Katedrali",
    "https://tr.wikipedia.org/wiki/Champs-%C3%89lys%C3%A9es",
    "https://tr.wikipedia.org/wiki/Eyfel_Kulesi",
    "https://tr.wikipedia.org/wiki/Marsilya",
    "https://gezipgordum.com/marsilya-gezilecek-yerler/",
    "https://nasilgezdim.net/2018/11/23/toulouse-gezi-rehberi-ve-toulouse-gezilecek-yerler/",
    "https://www.enuygun.com/bilgi/en-guzel-fransa-sehirleri/",
    "https://tr.wikipedia.org/wiki/T%C3%BCrkiye",
    "https://tr.wikipedia.org/wiki/%C4%B0talya",
    "https://tr.wikipedia.org/wiki/Japonya",
    "https://tr.wikipedia.org/wiki/Almanya",
    "https://tr.wikipedia.org/wiki/%C4%B0ngiltere",
    "https://tr.wikipedia.org/wiki/%C4%B0spanya",
    "https://tr.wikipedia.org/wiki/Amerika_Birle%C5%9Fik_Devletleri",
    "https://tr.wikipedia.org/wiki/M%C4%B1s%C4%B1r",
    "https://tr.wikipedia.org/wiki/Yunanistan",
    "https://tr.wikipedia.org/wiki/Hindistan",
    "https://tr.wikipedia.org/wiki/%C3%87in",
    "https://tr.wikipedia.org/wiki/Brezilya",
    "https://tr.wikipedia.org/wiki/Kanada",
    "https://tr.wikipedia.org/wiki/Rusya",
    "https://tr.wikipedia.org/wiki/Hollanda",
    "https://tr.wikipedia.org/wiki/Bel%C3%A7ika",
    "https://tr.wikipedia.org/wiki/%C4%B0svi%C3%A7re",
    "https://tr.wikipedia.org/wiki/Toulouse",
    "https://tr.wikipedia.org/wiki/Roma"
]


if __name__ == "__main__":
    print("""
============================================================
              AI TRAVEL PLANNER SCRAPER & EXTRACTOR
============================================================
    """)
    process_and_save(urls_list)
    print("✨ İşlem tamamlandı! Veriler 'travel_data' klasörüne kaydedildi.")