# ✈️ AI Travel Planner (Yerel RAG Asistanı)

Bu proje, **Microsoft Staj Programı - Aşama 1 (Microsoft Foundry Local ile Yerel RAG Uygulaması)** kapsamında geliştirilmiş, tamamen yerel bilgisayar üzerinde (offline) çalışan bir **RAG (Retrieval-Augmented Generation)** belge soru-cevap ve seyahat asistanıdır.

Proje, internet bağlantısına ihtiyaç duymadan, sağlanan Wikipedia verilerini analiz eder, zenginleştirilmiş veri enjeksiyonlarıyla birleştirir ve kullanıcı sorularına akıllı, bağlam tabanlı (context-aware) yanıtlar üretir.

---

## 🎯 Aşama 1 Teslim Kriterleri Uyumluluğu

Bu proje, staj programının Aşama 1 gereksinimlerini %100 karşılayacak şekilde tasarlanmıştır:
1. **Offline Soru-Cevap Uygulaması:** Önceden belirlenmiş Wikipedia seyahat veri seti (chunking + embedding ile) SQLite üzerinde tutulmakta ve tamamen yerel Foundry sunucusu üzerinden internetsiz (offline) çalışmaktadır.
2. **Sıfır Halüsinasyon (Uydurma Koruması):** İleri düzey Prompt Mühendisliği ile korunan sistem, kendisine verilen veri tabanında yer almayan tek bir kelimeyi bile uydurmaz. Sorunun cevabı bağlamda (context) yoksa kesinlikle "Veritabanında bu konu hakkında yeterli bilgi yok" diyerek sınırlarını bilir.
3. **Kaynak Gösterme Şartı (Citations):** Yapay zekanın sunduğu her türlü bilgi, kaynağıyla birlikte belirtilir (Örn: `Bkz: country_istanbul.txt, Bölüm 152`).
4. **Coğrafi ve Mantıksal Sınırlar:** Sistem, 5 günlük bir plan yapması istendiğinde "St. Patrick's Day" veya "İstanbul Bienali" gibi yılda bir kez olan etkinlikleri (özel olarak o tarihler sorulmadıkça) sıradan planlara eklemez. Ayrıca coğrafi sınır ihlali yapmaz.

---

## ✨ Öne Çıkan Gelişmiş Özellikler (Yeni!)

- **Tıklanabilir Google Haritalar Entegrasyonu:** RAG sisteminin önerdiği her bir spesifik mekan ve plaj, otomatik olarak **Google Haritalar** arama bağlantısına dönüştürülür ve tıklanınca yeni bir sekmede açılır.
- **Veri Zenginleştirme (Data Injection):** Wikipedia verileri sadece tarihsel ve coğrafi olduğundan, asistanın daha turistik ve büyüleyici cevaplar verebilmesi için sisteme `inject_beaches.py` ve `inject_istanbul.py` scriptleri aracılığıyla spesifik turistik mekan (Ayasofya, Yerebatan Sarnıcı) ve plaj (Kaputaş, Lara Beach vb.) verileri İngilizce olarak enjekte edilmiştir.
- **Nizami Markdown Seyahat Formatı:** Asistan, seyahat planlarını düz bir metin olarak değil; gün gün kalın başlıklar (`## Day 1`) ve temiz madde işaretleriyle tam bir turizm acentesi profesyonelliğinde formatlayarak sunar.

---

## 🛠️ Temel Teknolojiler ve Mimari

- **Microsoft Foundry Local**: Dil modelini (LLM) cihaz üzerinde çalıştıran, bulut veya GPU API aboneliği gerektirmeyen yerel AI çalışma zamanı.
- **Sentence-Transformers (PyTorch & CUDA)**: Metnin anlamını sayısal vektörlerle (embedding) temsil etme ve RAG bellek aramasını sağlama.
- **SQLite**: Belge metinlerini ve yüksek boyutlu embedding vektörlerini saklayan hafif, yerel veritabanı.
- **Flask**: Modern, estetik ve kullanıcı dostu bir web sohbet arayüzü sunan Python kütüphanesi.
- **Deep-Translator**: İngilizce çalışan LLM çıktılarını anlık olarak (HTML ve Markdown etiketlerini bozmadan) kullanıcının diline çeviren stream (akış) tampon sistemi.

---

## 🚀 Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla uygulayın. (Not: Bu proje **Windows 11** ve **NVIDIA CUDA** destekli ekran kartı gerektirmektedir.)

### 1. Gereksinimlerin Yüklenmesi
Öncelikle bir Python sanal ortamı (`venv`) oluşturun ve aktif edin. Ardından bağımlılıkları yükleyin:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Veritabanının Hazırlanması ve Zenginleştirilmesi
Projedeki verileri (Wikipedia metinleri) parçalara (chunks) bölmek, GPU üzerinden vektörleştirmek ve ardından özel turistik veri yamalarını eklemek için şu komutları sırasıyla çalıştırın:
```powershell
python enrich_with_wikipedia.py
python inject_beaches.py
python inject_istanbul.py
```
> Bu işlemler veritabanını baştan oluşturur ve turistik yamaları (plajlar, müzeler) sisteme gömer. Ekran kartınızın hızına bağlı olarak ilk adım birkaç dakika sürebilir.

### 3. Uygulamanın Başlatılması
Veritabanı hazırlandıktan sonra, görsel arayüzü başlatmak için Flask sunucusunu başlatan script'i kullanın:
```powershell
python start_ai_travel_planner.py
```
Komut çalıştıktan sonra tarayıcınızda otomatik olarak **http://127.0.0.1:5000** adresinde AI Travel Planner açılacaktır.

---

## 👥 Geliştirici
- **Geliştirici:** Sudem Kavuzkoz
- **Kapsam:** Microsoft Staj Programı - Aşama 1 Projesi
