import wikipediaapi

wiki = wikipediaapi.Wikipedia(
    user_agent="MyTestApp/1.0 (iletisim@epostaniz.com)",
    language="en"
)

sayfa = wiki.page("France")

if sayfa.exists():
    print(f"--- {sayfa.title} SAYFASININ TÜM İÇERİĞİ ---\n")
    
    # sayfa.text sayfanın tüm metnini getirir
    print(sayfa.text)
    
else:
    print("Sayfa bulunamadı.")