import os
import sqlite3
import requests
import json
import numpy as np
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch

# Model entegrasyonu koruması
try:
    from model import generate_response, generate_response_stream
except ImportError:
    def generate_response(user_prompt, system_prompt=""):
        return "Model modülü bulunamadı. Lütfen model.py dosyanızı kontrol edin."
    def generate_response_stream(user_prompt, system_prompt=""):
        yield "Model modülü bulunamadı."

load_dotenv()

app = Flask(__name__)

# --- YAPILANDIRMA VE VERİTABANI YOLLARI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "travel_rag.db")
DOCS_DIR = os.path.join(BASE_DIR, "travel_data")

LOCAL_LLM_BASE = os.getenv("LOCAL_LLM_BASE", "http://localhost:8000/v1")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "phi-4-mini")
OWM_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

RAG_SIMILARITY_THRESHOLD = 0.22  
RAG_TOP_K = 3

# GPU / CPU Seçimi
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Embedding modeli için kullanılan cihaz: {device.upper()}")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device=device)

# Harita koordinat havuzu (Dinamik yükleme)
try:
    with open(os.path.join(BASE_DIR, "country_coordinates.json"), "r", encoding="utf-8") as f:
        COUNTRY_COORDINATES = json.load(f)
except Exception:
    COUNTRY_COORDINATES = {}

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """SQLite RAG Veritabanı Şemasının Kurulması ve Versiyon Kontrolü (Migration)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Şema çakışmalarını ve 'Unique Code' hatasını çözmek için Versiyon Kontrolü
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_info (version INTEGER);")
    cursor.execute("SELECT version FROM schema_info LIMIT 1;")
    row = cursor.fetchone()
    
    if row is None or row["version"] < 2:
        print("! Veritabanı yapısı güncelleniyor (Versiyon 2)... Eski kısıtlamalar kaldırılıyor.")
        cursor.execute("DROP TABLE IF EXISTS document_chunks;")
        cursor.execute("DROP TABLE IF EXISTS countries;")
        cursor.execute("DROP TABLE IF EXISTS schema_info;")
        cursor.execute("CREATE TABLE schema_info (version INTEGER);")
        cursor.execute("INSERT INTO schema_info (version) VALUES (2);")
        conn.commit()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        code TEXT NOT NULL,
        lat REAL,
        lon REAL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER,
        source TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        embedding BLOB NOT NULL,
        FOREIGN KEY (country_id) REFERENCES countries (id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries (id)
    );
    """)
    
    conn.commit()
    conn.close()

    # Belgeleri klasörden dinamik olarak tara ve RAG sistemine yükle
    import_documents_from_folder()

def chunk_text(text, chunk_size=600, overlap=90):
    """Metinleri anlamlı parçalara (chunk) böler."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    buffer = ""

    for para in paragraphs:
        candidate = f"{buffer} {para}".strip() if buffer else para
        if len(candidate) <= chunk_size:
            buffer = candidate
        else:
            if buffer: chunks.append(buffer)
            if len(para) <= chunk_size:
                buffer = para
            else:
                start = 0
                while start < len(para):
                    end = start + chunk_size
                    chunks.append(para[start:end].strip())
                    start += chunk_size - overlap
                buffer = ""
    if buffer: chunks.append(buffer)
    return [c for c in chunks if c]

def import_documents_from_folder():
    """travel_data içerisindeki 300+ blog ve rehber dosyasını hatasız şekilde vektörel dizine ekler."""
    if not os.path.isdir(DOCS_DIR):
        print(f"Hata: '{DOCS_DIR}' klasörü bulunamadı!")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    files = [f for f in os.listdir(DOCS_DIR) if f.lower().endswith(".txt")]
    print(f"Klasörde {len(files)} adet kaynak belge bulundu. İndeksleniyor...")

    for filename in files:
        clean_name = filename.lower().replace("country_", "").replace(".txt", "").replace("_", " ").strip()
        display_name = filename.replace(".txt", "").strip() # Dosya adının tamamını koruyarak ayırt edici yapıyoruz
        code = "TR"  # Varsayılan genel kod (Artık benzersiz olmak zorunda değil)
        
        # Akıllı lokasyon eşleştirici
        import random
        coords = [25.0 + random.uniform(-5, 5), 15.0 + random.uniform(-5, 5)] # Fallback
        if clean_name in COUNTRY_COORDINATES:
            coords = COUNTRY_COORDINATES[clean_name]

        # Güvenli Ekleme Aşaması
        try:
            cursor.execute("INSERT INTO countries (name, code, lat, lon) VALUES (?, ?, ?, ?)", 
                           (display_name, code, coords[0], coords[1]))
            conn.commit()
            country_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Eğer isim zaten varsa ID değerini güvenle çek
            cursor.execute("SELECT id FROM countries WHERE name = ?", (display_name,))
            res = cursor.fetchone()
            country_id = res["id"] if res else None

        if country_id is None:
            continue

        # Mükerrer veri kontrolü
        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE country_id = ?", (country_id,))
        if cursor.fetchone()[0] > 0:
            continue

        filepath = os.path.join(DOCS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()

        chunks = chunk_text(raw_text)
        if not chunks: continue

        print(f"-> {display_name[:40]}... için {len(chunks)} blok CUDA/CPU ile işleniyor...")
        chunk_embeddings = embedding_model.encode(chunks, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)

        for idx, (chunk, vector) in enumerate(zip(chunks, chunk_embeddings)):
            cursor.execute("""
                INSERT INTO document_chunks (country_id, source, chunk_index, chunk_text, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, (country_id, filename, idx, chunk, vector.tobytes()))
        
        conn.commit()

    conn.close()
    print("Tum seyahat belgeleri RAG veritabani ile basariyla esitlendi!")

init_db()

# --- API ENDPOINTS ---

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/countries", methods=["GET"])
def get_countries():
    """Tüm kayıtlı lokasyonları harita pinleri için koordinatlarıyla döner."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, code, lat, lon FROM countries")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/api/chat-history/<int:country_id>", methods=["GET"])
def get_chat_history(country_id):
    """Belirli bir ülke/lokasyon için geçmiş sohbetleri döner."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history WHERE country_id = ? ORDER BY timestamp ASC", (country_id,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/api/generate-itinerary", methods=["POST"])
def generate_itinerary():
    """Gelişmiş Vektör Arama RAG Katmanı ve Phi-4 Mini Yanıt Üretici (Streaming)"""
    data = request.get_json() or {}
    messages = data.get("messages", [])
    country_id = data.get("country_id")

    if not messages or not country_id:
        return jsonify({"error": "Eksik veri gönderildi."}), 400

    import time
    start_time = time.time()

    from translator import translate_tr_to_en, translate_stream_en_to_tr
    from langdetect import detect

    user_query = messages[-1]['content']
    
    # Kullanıcının dilini tespit et
    try:
        user_lang = detect(user_query)
    except:
        user_lang = 'tr'  # Algılanamazsa varsayılan Türkçe
        
    is_turkish = (user_lang == 'tr')
    
    if is_turkish:
        english_query = translate_tr_to_en(user_query)
        print(f"[{time.time() - start_time:.2f}s] [Çeviri] Soru çevrildi: {english_query}")
    else:
        english_query = user_query
        print(f"[{time.time() - start_time:.2f}s] [Dil Algılandı] Soru zaten İngilizce.")

    # HIZ OPTİMİZASYONU: İşlemciyi yormamak için eski sohbet geçmişini (history) iptal ediyoruz. Sadece anlık soru!
    history_messages = []
    
    # "Tatil planı" tarzı genel isteklerde RAG parametrelerini esnetelim
    query_lower = user_query.lower()
    is_plan_request = any(w in query_lower for w in ["plan", "program", "rota", "günlük", "tur", "gezilecek"])
    
    # Eşik değerini eski mantıklı seviyesine getiriyoruz
    current_threshold = 0.20 if is_plan_request else 0.25
    
    # KAPSAMLI RAG VE HIZ DENGESİ: 20 çok yavaştı, 5 çok az veri veriyordu.
    # En ideal denge olarak 10 parça (yaklaşık 1500 kelime) veriyoruz. 
    current_top_k = 10 if is_plan_request else 6

    # RAG Vektör Arama – İngilizce sorguyu vektörleştir
    vec_start = time.time()
    query_vector = embedding_model.encode(english_query, normalize_embeddings=True).astype(np.float32)
    print(f"[{time.time() - vec_start:.2f}s] Vektörleştirme tamamlandı.")

    # Keyword boosting için hem orijinal (Türkçe) hem de çevrilmiş (İngilizce) sorgulardan kelimeleri çıkarıyoruz.
    # 3 harften büyük kelimeleri alıp noktalama işaretlerini temizliyoruz
    import re
    user_words = [re.sub(r'[^\w\s]', '', w).lower() for w in user_query.split() if len(w) > 3]
    eng_words = [re.sub(r'[^\w\s]', '', w).lower() for w in english_query.split() if len(w) > 3]
    query_words = list(set(user_words + eng_words))

    db_start = time.time()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, chunk_index, chunk_text, embedding, source FROM document_chunks WHERE country_id = ?", (country_id,))
    rows = cursor.fetchall()
    
    scored_chunks = []
    for row in rows:
        vector = np.frombuffer(row["embedding"], dtype=np.float32)
        similarity = float(np.dot(vector, query_vector))
        
        # --- Keyword Boosting (Hibrit Arama) ---
        chunk_text_lower = row["chunk_text"].lower()
        boost = 0.0
        for word in query_words:
            if word in chunk_text_lower:
                boost += 0.15 # Kelime eşleşmesi başına bonus puan
                
        final_score = similarity + boost
        
        if final_score >= current_threshold:
            scored_chunks.append((final_score, row["chunk_text"], row["source"], row["chunk_index"]))
            
    conn.close()
    print(f"[{time.time() - db_start:.2f}s] Veritabanı Vektör araması tamamlandı.")

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = scored_chunks[:current_top_k]

    if top_chunks:
        context_parts = []
        used_chunks_info = []
        used_sources = set()
        
        for i, (score, text, src, c_index) in enumerate(top_chunks, 1):
            # Küçük modeller XML etiketlerini okumakta zorlanır ve tembellik edip (Bkz: 1) yazar.
            # Bunu engellemek için kaynakları çok açık ve kopyalanabilir bir metin olarak veriyoruz.
            context_parts.append(f"--- SOURCE: {src}, PART: {c_index} ---\n{text}\n")
            used_sources.add(src)
            
            # Find exact line number by opening the file
            exact_line = "Bilinmiyor"
            search_key = text[:40].replace('\n', ' ').strip()
            
            try:
                filepath = os.path.join(DOCS_DIR, src)
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if search_key in line:
                            exact_line = line_num
                            break
            except Exception:
                pass
                
            used_chunks_info.append({
                'dosya': src,
                'bolum': c_index,
                'skor': score,
                'arama': search_key + "...",
                'satir': exact_line
            })
            
        context_str = "\n\n".join(context_parts)
        used_sources = list(used_sources)
    else:
        # Hiçbir şey bulunamazsa bile genel bilgi ver
        context_str = "Bu bölge hakkında genel turistik tavsiyeler ver. Temsili restoranlar ve popüler yerler öner."
        used_chunks_info = []
        used_sources = ["Genel Asistan Modu"]

    # Canlı Hava Durumu
    weather_info = "Hava durumu verisine şu an ulaşılamıyor."
    if OWM_API_KEY:
        try:
            cursor = get_db_connection().cursor()
            cursor.execute("SELECT name FROM countries WHERE id = ?", (country_id,))
            c_name = cursor.fetchone()["name"]
            url = f"https://api.openweathermap.org/data/2.5/weather?q={c_name}&appid={OWM_API_KEY}&units=metric&lang=tr"
            w_res = requests.get(url, timeout=4).json()
            weather_info = f"Bölge Hava Durumu: {w_res['weather'][0]['description'].title()}, Sıcaklık: {w_res['main']['temp']}°C"
        except Exception:
            pass

    system_prompt = (
        "You are a smart, highly enthusiastic, and professional travel assistant.\n"
        "Read the provided SOURCE texts below. You MUST base your entire response ONLY on these texts. Write comprehensive, engaging, and beautifully detailed descriptions.\n"
        "CRITICAL RULE 1 - NO HALLUCINATIONS: DO NOT invent, guess, or add any places, beaches, hotels, or tourist attractions from your own memory. EVERY place you mention MUST exist in the provided SOURCE texts. If the texts do not have the answer, say 'Veritabanında bu konu hakkında yeterli bilgi yok.'\n"
        "CRITICAL RULE 2 - ITINERARY PLANNING: If the user asks for a trip plan, extract the places explicitly mentioned in the SOURCE texts and organize them day by day. DO NOT schedule annual, seasonal, or specific-date festivals (like St. Patrick's Day, Halloween, or Biennials) in a generic itinerary unless the user explicitly mentions those dates. You can use your logic to structure the days, but YOU CANNOT ADD NEW PLACES.\n"
        "CRITICAL RULE 3 - GEOGRAPHY: Analyze the user's requested city and country carefully. If the retrieved SOURCE texts mention places that belong to other cities or countries, you MUST ignore those unrelated places. Only suggest places that strictly belong to the user's requested city.\n"
        "CRITICAL RULE 4 - GOOGLE MAPS: Format every place as a markdown link: [Place Name](https://www.google.com/maps/search/?api=1&query=Place+Name+CityName).\n"
        "CRITICAL RULE 5 - FORMAT: You MUST output ONLY in English. Do NOT output any pseudo code. Do NOT output Python code.\n"
        "CRITICAL RULE 6 - CITATIONS: When you write a fact, cite it exactly like this: (Bkz: [filename], Bölüm [part])."
    )

    user_prompt = f"Context:\n{context_str}\n\nUser Question:\n{english_query}"

    def generate():
        try:
            ai_response_full = ""

            gen_start = time.time()
            print(f"[{gen_start - start_time:.2f}s] LLM'e istek gönderiliyor...")

            # Modele İngilizce sor, İngilizce stream al
            english_generator = generate_response_stream(user_prompt, system_prompt, history=history_messages)
            
            first_token_received = False

            if is_turkish:
                # Kullanıcı Türkçe sorduysa, İngilizce cevabı anlık olarak Türkçeye çevirerek yolla
                for chunk in translate_stream_en_to_tr(english_generator):
                    if not first_token_received:
                        print(f"[{time.time() - gen_start:.2f}s] İlk çevrilmiş metin (TTFT) ekrana basıldı!")
                        first_token_received = True
                    ai_response_full += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            else:
                # Kullanıcı İngilizce sorduysa doğrudan İngilizce cevabı yolla
                for chunk in english_generator:
                    if not first_token_received:
                        print(f"[{time.time() - gen_start:.2f}s] İlk kelime (TTFT) ekrana basıldı!")
                        first_token_received = True
                    ai_response_full += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            print(f"[{time.time() - gen_start:.2f}s] Tüm LLM Stream ve Çeviri işlemi BİTTİ.")

            # Kaynakça ekle
            sources_text = ""
            if used_chunks_info and "böyle bir bilgi yok" not in ai_response_full.lower():
                sources_text = "\n\n---\n**📚 Kullanılan Kaynaklar ve Kanıtlar (RAG Raporu):**\n"
                for info in used_chunks_info[:5]:  # Sadece en yüksek skorlu ilk 5 chunk'ı göster
                    sources_text += (
                        f"- **{info['dosya']}** (Bölüm {info['bolum']})\n"
                        f"  - *Kosinüs Benzerliği:* `{info['skor']:.2f}`\n"
                        f"  - *Tam Satır:* `{info['satir']}`\n"
                        f"  - *CTRL+F Arama:* \"{info['arama']}\"\n"
                    )
                ai_response_full += sources_text
                yield f"data: {json.dumps({'chunk': sources_text})}\n\n"

            # Veritabanına kaydet (Stream bittikten sonra)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (country_id, role, content) VALUES (?, ?, ?)",
                (country_id, 'user', user_query)
            )
            cursor.execute(
                "INSERT INTO chat_history (country_id, role, content) VALUES (?, ?, ?)",
                (country_id, 'assistant', ai_response_full)
            )
            conn.commit()
            conn.close()

            yield f"data: {json.dumps({'sources': used_sources})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    from flask import Response
    return Response(generate(), mimetype='text/event-stream')

# --- SPA ÖNYÜZ TASARIMI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global RAG Travel Planner</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <style>
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        #map { height: 100%; width: 100%; background: #0f172a; }
        
        .leaflet-tile-container {
            filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
        }
        .leaflet-container { background: #0f172a !important; }
        
        /* Google Maps Linklerini Şık Butonlara Dönüştüren CSS */
        .prose a {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background-color: #1e293b !important;
            color: #38bdf8 !important;
            padding: 0.4rem 0.8rem;
            border-radius: 0.75rem;
            text-decoration: none !important;
            font-weight: 600;
            font-size: 12px;
            margin: 0.25rem 0;
            border: 1px solid #334155;
            transition: all 0.2s ease;
        }
        .prose a:hover {
            background-color: #0284c7 !important;
            color: #ffffff !important;
            border-color: #0284c7;
        }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans overflow-hidden">

    <div class="flex h-screen w-screen flex-col md:flex-row">
        
        <!-- SOL TARAF: DÜNYA HARİTASI -->
        <main class="w-full md:w-3/5 h-1/2 md:h-full relative border-b md:border-b-0 md:border-r border-slate-800">
            <div class="absolute top-4 left-4 z-[1000] bg-slate-950/80 backdrop-blur-md p-4 rounded-2xl border border-slate-800 shadow-xl max-w-sm">
                <h1 class="text-xl font-black bg-gradient-to-r from-blue-400 to-sky-400 bg-clip-text text-transparent tracking-tight">AI DÜNYA REHBERİ</h1>
                <p class="text-[11px] text-slate-400 mt-1">Sistemdeki 300+ belgeden yüklenen rehberleri görmek ve chatbotu başlatmak için haritadaki yeşil pinlere tıklayın.</p>
            </div>
            <div id="map"></div>
        </main>

        <!-- SAĞ TARAF: CHATBOT EKRANI -->
        <aside id="chat-panel" class="w-full md:w-2/5 h-1/2 md:h-full flex flex-col bg-slate-950">
            
            <header class="p-4 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-2.5 h-2.5 rounded-full bg-slate-600 dynamic-status-pulse"></div>
                    <h2 id="active-country-title" class="text-md font-bold text-slate-300">Lütfen Haritadan Seçim Yapın</h2>
                </div>
                <span id="source-badge" class="text-[10px] bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded text-blue-400 hidden">RAG Hazır</span>
            </header>

            <div id="chat-container" class="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-4">
                <div class="flex gap-3 items-start" id="welcome-msg">
                    <div class="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                        <i class="fa-solid fa-map-marked-alt"></i>
                    </div>
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-none p-3 text-sm max-w-[85%] text-slate-300 leading-relaxed">
                        Merhaba! Haritadan bir lokasyon seçtiğinizde o rehbere ait tüm detaylar (gezilecek yerler, harita konumları, lezzet noktaları) asistanınıza yüklenecektir.
                    </div>
                </div>
                <div id="chat-messages" class="space-y-4"></div>
            </div>

            <div class="p-4 bg-slate-900/40 border-t border-slate-800">
                <div class="relative flex items-center">
                    <input type="text" id="chat-input" disabled 
                           placeholder="Önce haritadan bir hedef seçmelisiniz..." 
                           class="w-full bg-slate-900 border border-slate-800 rounded-xl py-3 pl-4 pr-12 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition disabled:opacity-40 disabled:cursor-not-allowed"
                           onkeydown="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()" id="send-btn" disabled
                            class="absolute right-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 text-white rounded-lg transition disabled:text-slate-600">
                        <i class="fa-solid fa-location-arrow"></i>
                    </button>
                </div>
                <div class="flex justify-between items-center mt-2 text-[10px] text-slate-600 px-1">
                    <span>Engine: Phi-4 Mini & SQLite Vector Index</span>
                    <span>Status: Aktif</span>
                </div>
            </div>

        </aside>
    </div>

    <script>
        // Markdown parser konfigürasyonu (Linkleri yeni sekmede açmak için)
        const renderer = new marked.Renderer();
        renderer.link = function(arg1, arg2, arg3) {
            let href, title, text;
            if (typeof arg1 === 'object' && arg1 !== null) {
                // Marked v8+ (token nesnesi)
                href = arg1.href;
                title = arg1.title;
                text = arg1.text || arg1.raw; // Fallback to raw if text is undefined
            } else {
                // Eski sürüm Marked
                href = arg1; title = arg2; text = arg3;
            }
            return `<a target="_blank" rel="noopener noreferrer" href="${href}" title="${title || ''}">${text}</a>`;
        };
        marked.setOptions({ renderer: renderer });

        let map;
        let selectedCountryId = null;
        let selectedCountryName = "";
        let chatHistory = [];

        function initMap() {
            map = L.map('map', { zoomControl: false }).setView([35.0, 20.0], 3);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18
            }).addTo(map);

            L.control.zoom({ position: 'bottomleft' }).addTo(map);

            // Dinamik Pinleri Yükleme
            fetch('/api/countries')
                .then(res => res.json())
                .then(countries => {
                    countries.forEach(country => {
                        let marker = L.circleMarker([country.lat, country.lon], {
                            radius: 8,
                            fillColor: "#10b981",
                            color: "#ffffff",
                            weight: 1.5,
                            opacity: 1,
                            fillOpacity: 0.85
                        }).addTo(map);

                        // Uzun dosya isimlerini haritada temiz göstermek için kısaltma uyguluyoruz
                        let shortName = country.name.length > 35 ? country.name.substring(0, 35) + "..." : country.name;
                        marker.bindTooltip(`<b>${shortName}</b>`, { direction: 'top' });

                        marker.on('click', () => {
                            setActiveCountry(country.id, country.name);
                        });
                    });
                });
        }

        function setActiveCountry(id, name) {
            selectedCountryId = id;
            selectedCountryName = name;
            
            document.getElementById('welcome-msg').style.display = 'none';
            document.querySelector('.dynamic-status-pulse').className = "w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse dynamic-status-pulse";
            document.getElementById('active-country-title').innerText = `💬 Seyahat Rehberi Aktif`;
            
            const inputEl = document.getElementById('chat-input');
            inputEl.disabled = false;
            inputEl.placeholder = "Bu rehberdeki popüler yerleri veya müzeleri sorun...";
            
            document.getElementById('send-btn').disabled = false;
            document.getElementById('chat-messages').innerHTML = '';
            
            chatHistory = [];
            
            // Fetch past chat history
            fetch(`/api/chat-history/${id}`)
                .then(res => res.json())
                .then(history => {
                    if (history.length > 0) {
                        history.forEach(msg => {
                            appendMessage(msg.role, msg.content, false);
                            chatHistory.push(msg);
                        });
                    } else {
                        appendMessage('assistant', `**${name}** başlıklı kaynak başarıyla yüklendi! Doküman içerisindeki tarihi alanlar, restoranlar ve lokasyon detayları sorgulanmaya hazır. Ne öğrenmek istersiniz?`, false);
                    }
                    setTimeout(() => {
                        document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
                    }, 100);
                });
            
            inputEl.focus();
        }

        function appendMessage(role, text, scrollToBottom = true) {
            const container = document.getElementById('chat-messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = `flex gap-3 items-start ${role === 'user' ? 'justify-end' : ''}`;
            
            const icon = role === 'user' ? 'fa-user' : 'fa-robot';
            const bgClass = role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none';
            const orderClass = role === 'user' ? 'order-2' : '';

            msgDiv.innerHTML = `
                <div class="w-8 h-8 rounded-xl ${role==='user'?'bg-blue-500/20 text-blue-400':'bg-emerald-500/10 text-emerald-400'} flex items-center justify-center text-xs shrink-0 ${orderClass}">
                    <i class="fa-solid ${icon}"></i>
                </div>
                <div class="${bgClass} rounded-2xl p-3 text-sm max-w-[85%] prose prose-invert leading-relaxed">
                    ${marked.parse(text)}
                </div>
            `;
            container.appendChild(msgDiv);
            if (scrollToBottom) {
                document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
            }
        }

        function sendMessage() {
            const input = document.getElementById('chat-input');
            const query = input.value.trim();
            if (!query || !selectedCountryId) return;

            appendMessage('user', query);
            input.value = '';
            
            chatHistory.push({ role: 'user', content: query });

            const sendBtn = document.getElementById('send-btn');
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';

            fetch('/api/generate-itinerary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: chatHistory,
                    country_id: selectedCountryId
                })
            })
            .then(async response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = "";
                
                // Mesaj baloncuğunu oluştur
                const container = document.getElementById('chat-messages');
                const msgDiv = document.createElement('div');
                msgDiv.className = `flex gap-3 items-start`;
                msgDiv.innerHTML = `
                    <div class="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xs shrink-0">
                        <i class="fa-solid fa-robot"></i>
                    </div>
                    <div class="bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none rounded-2xl p-3 text-sm max-w-[85%] prose prose-invert leading-relaxed content-div">
                        <i class="fa-solid fa-circle-notch fa-spin text-slate-500"></i>
                    </div>
                `;
                container.appendChild(msgDiv);
                const contentDiv = msgDiv.querySelector('.content-div');
                document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;

                let isFirstChunk = true;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\\n\\n');
                    
                    for (let line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.substring(6);
                            if (!dataStr) continue;
                            try {
                                const data = JSON.parse(dataStr);
                                if (data.error) {
                                    fullText = `⚠️ Hata: ${data.error}`;
                                    contentDiv.innerHTML = marked.parse(fullText);
                                } else if (data.chunk !== undefined) {
                                    if (isFirstChunk) {
                                        fullText = "";
                                        isFirstChunk = false;
                                    }
                                    fullText += data.chunk;
                                    contentDiv.innerHTML = marked.parse(fullText);
                                    document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
                                } else if (data.sources) {
                                    chatHistory.push({ role: 'assistant', content: fullText });
                                    const badge = document.getElementById('source-badge');
                                    badge.style.display = 'inline-block';
                                    badge.innerText = `RAG Bloğu: ${data.sources.length} Kaynak`;
                                }
                            } catch (e) {
                                // Gelen data JSON parse edilemezse atla
                            }
                        }
                    }
                }
            })
            .catch(() => {
                appendMessage('assistant', '❌ Yapay zeka motorundan yanıt alınamadı.');
            })
            .finally(() => {
                sendBtn.disabled = false;
                sendBtn.innerHTML = '<i class="fa-solid fa-location-arrow"></i>';
            });
        }

        window.addEventListener('DOMContentLoaded', initMap);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)