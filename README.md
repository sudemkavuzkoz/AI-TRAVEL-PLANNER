# ✈️ AI Travel Planner (Yerel RAG Asistanı)

Bu proje, **Microsoft Staj Programı - Aşama 1 (Microsoft Foundry Local ile Yerel RAG Uygulaması)** kapsamında geliştirilmiş, tamamen yerel bilgisayar üzerinde (offline) çalışan bir **RAG (Retrieval-Augmented Generation)** belge soru-cevap ve seyahat asistanıdır.

Proje, internet bağlantısına ihtiyaç duymadan, sağlanan seyahat, Wikipedia ve TripAdvis verilerini analiz eder ve kullanıcı sorularına akıllı, bağlam tabanlı (context-aware) yanıtlar üretir.

---

## 🎯 Aşama 1 Teslim Kriterleri Uyumluluğu

Bu proje, staj programının Aşama 1 gereksinimlerini %100 karşılayacak şekilde tasarlanmıştır:
1. **Offline Soru-Cevap Uygulaması:** Önceden belirlenmiş Wikipedia seyahat veri seti (chunking + embedding ile) SQLite üzerinde tutulmakta ve tamamen yerel Foundry sunucusu üzerinden internetsiz (offline) çalışmaktadır.
2. **Kaynak Gösterme ve "Bilmiyorum" Kuralı:** Sistem özel bir prompt (istem) mühendisliği ile korunmaktadır. LLM her cümlesinin sonuna kaynak dosya ve bölüm eklemek zorundadır (Örn: `Bkz: country_istanbul.txt, Bölüm 152`). Eğer bağlamda kesinlikle hiçbir veri yoksa sistem "Veritabanında bu konu hakkında yeterli bilgi yok" (bilmiyorum) yanıtı verecek şekilde katı kurallara tabidir.
3. **Temiz Kod ve README:** Projede modüler (database, embedding, app) bir mimari kullanılmış ve bu belge kurulum için detaylı olarak hazırlanmıştır.
4. **Google Maps Entegrasyonu:** (Ekstra) Sistem, ürettiği lokasyon isimlerini otomatik olarak tıklanabilir Google Maps butonlarına çevirir.

---

## 🛠️ Temel Teknolojiler ve Mimari

- **Microsoft Foundry Local**: Dil modelini (LLM) cihaz üzerinde çalıştıran, bulut veya GPU API aboneliği gerektirmeyen yerel AI çalışma zamanı (Phi-4-mini veya Qwen2.5-1.5B gibi modellerle uyumlu).
- **Sentence-Transformers (PyTorch & CUDA)**: Metnin anlamını sayısal vektörlerle (embedding) temsil etme ve RAG bellek aramasını sağlama.
- **SQLite**: Belge metinlerini ve yüksek boyutlu embedding vektörlerini saklayan hafif, yerel veritabanı.
- **Flask**: Modern, estetik ve kullanıcı dostu bir web sohbet arayüzü sunan Python kütüphanesi.
- **Deep-Translator & LangDetect**: İngilizce çalışan LLM çıktılarını anlık olarak kullanıcının diline çeviren stream (akış) tampon sistemi.

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

### 2. Veritabanının Doldurulması (Embedding İşlemi)
Projedeki verileri (Wikipedia metinleri) parçalara (chunks) bölmek, GPU üzerinden vektörleştirmek ve SQLite veritabanına kaydetmek için aşağıdaki komutu çalıştırın:
```powershell
python enrich_with_wikipedia.py
```
> Bu işlem veritabanını baştan oluşturur. Ekran kartınızın hızına bağlı olarak birkaç dakika sürebilir.

### 3. Uygulamanın Başlatılması
Veritabanı hazırlandıktan sonra, görsel arayüzü başlatmak için Flask sunucusunu başlatan script'i kullanın:
```powershell
python start_ai_travel_planner.py
```
Komut çalıştıktan sonra tarayıcınızda otomatik olarak **http://127.0.0.1:5000** adresinde AI Travel Planner açılacaktır.

---

## 🧠 Nasıl Çalışır? (Prompt & RAG Mantığı)
Sistem halüsinasyonları (uydurma cevapları) önlemek için katı bir sistem komutuyla çalışır:
- Kullanıcı sorusu anlık olarak embedding vektörüne çevrilir.
- Veritabanında kosinüs benzerliği (cosine similarity) hesaplanarak soruya **en yakın 6 ila 10 belge parçası (chunk)** bulunur.
- Bu parçalar bağlam olarak Foundry Local üzerinden LLM'e beslenir.
- **Seyahat Planı Kuralı:** Eğer kullanıcı "4 günlük gezi planla" gibi bir şey isterse, yapay zeka metinlerdeki turistik mekanları analiz eder ve bu mekanları kullanarak mantıklı bir seyahat programı tasarlar (veritabanı dışına çıkmasına asla izin verilmez).

## 👥 Geliştirici
- Geliştirici: Sudem
- Kapsam: Microsoft Staj Programı - Aşama 1 Projesi
