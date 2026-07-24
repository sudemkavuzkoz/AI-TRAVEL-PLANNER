# ✈️ AI Travel Planner (Yerel RAG Asistanı)

Bu proje, **Microsoft Staj Programı - Aşama 1** kapsamında geliştirilmiş, tamamen yerel bilgisayar üzerinde (offline) çalışan bir **RAG (Retrieval-Augmented Generation)** belge soru-cevap asistanıdır.

Proje, internet bağlantısına ihtiyaç duymadan, sağlanan seyahat, Wikipedia ve TripAdvisor verilerini analiz eder ve kullanıcı sorularına akıllı, bağlam tabanlı (context-aware) yanıtlar üretir.

---

## 🛠️ Temel Teknolojiler ve Mimari

Bu proje, Microsoft'un modern yerel yapay zeka araçlarıyla klasik RAG mimarisini birleştirmektedir:

- **Microsoft Foundry Local**: Dil modelini (LLM) cihaz üzerinde çalıştıran, bulut veya GPU API aboneliği gerektirmeyen yerel AI çalışma zamanı (Phi-4-mini veya Qwen2.5-1.5B gibi modellerle uyumlu).
- **Sentence-Transformers (PyTorch & CUDA)**: Metnin anlamını sayısal vektörlerle (embedding) temsil etme ve RAG bellek aramasını sağlama.
- **SQLite**: Belge metinlerini ve yüksek boyutlu embedding vektörlerini saklayan hafif, yerel veritabanı.
- **Flask**: Modern, estetik ve kullanıcı dostu bir web sohbet arayüzü sunan Python kütüphanesi.

### 📦 Kullanılan Python Kütüphaneleri
Bu projenin çalışmasını sağlayan temel kütüphaneler şunlardır:
- `openai`: Yerel Foundry (LM Studio) sunucusuna OpenAI uyumlu API formatında bağlanarak chat completions (soru-cevap) yapmak için kullanıldı.
- `flask`: Kullanıcı arayüzünü (web sayfasını) ve backend API rotalarını (Server-Sent Events destekli) sunmak için kullanıldı.
- `sentence-transformers`: Verisetindeki metinleri okuyup yüksek boyutlu vektörlere (embedding) çevirmek için kullanıldı.
- `numpy`: Kosinüs benzerliği (Cosine Similarity) matris hesaplamalarını çok hızlı ve optimize bir şekilde yapmak için kullanıldı.
- `deep-translator`: Gelen İngilizce LLM yanıtlarını eşzamanlı ve dinamik bir buffer (tampon) sistemiyle anlık (stream) olarak Türkçeye çevirmek için kullanıldı.
- `langdetect`: Kullanıcının sorduğu sorunun dilini analiz edip sistemin otomatik olarak Türkçe/İngilizce akışına karar vermesini sağlamak için kullanıldı.

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
Projedeki `travel_data` klasöründe bulunan tüm kaynak belgeleri parçalara (chunks) bölmek, GPU üzerinden vektörleştirmek ve veritabanına kaydetmek için aşağıdaki komutu çalıştırın:
```powershell
python import_wiki.py
```
> Bu işlem, ekran kartınızın hızına bağlı olarak 1-2 dakika sürebilir.

### 3. Uygulamanın Başlatılması
Veritabanı hazırlandıktan sonra, görsel arayüzü başlatmak için Flask sunucusunu başlatan script'i kullanın:
```powershell
python start_ai_travel_planner.py
```
Komut çalıştıktan sonra tarayıcınızda otomatik olarak **http://127.0.0.1:5000** adresinde AI Travel Planner açılacaktır. İlk sorunuzda dil modeli arka planda otomatik olarak indirilip GPU'ya yüklenecektir.

---

## 🧠 Nasıl Çalışır? (Prompt & RAG Mantığı)
Sistem halüsinasyonları (uydurma cevapları) önlemek için katı bir sistem komutuyla (prompt engineering) çalışır:
- Kullanıcı sorusu anlık olarak embedding vektörüne çevrilir.
- Veritabanında (SQLite) kosinüs benzerliği (cosine similarity) hesaplanarak soruya **en yakın 6 ila 10 belge parçası (chunk)** bulunur.
- Bu parçalar bir "Bağlam (Context)" olarak Foundry Local üzerinden LLM'e beslenir.
- Sistem kuralı olarak: **"Eğer aranan bilgi bağlamda kesinlikle yoksa, sadece 'Bu konu hakkında bilgi sahibi değilim.' de ve uydurma yapma."** talimatı uygulanır.

## 👥 Geliştirici
- Bu proje, staj programı Aşama 1 gereksinimlerini sağlamak amacıyla geliştirilmiştir.
