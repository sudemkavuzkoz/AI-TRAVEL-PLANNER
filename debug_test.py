import os
import sys
from dotenv import load_dotenv

print("==================================================")
print("[ ] MS FOUNDRY LOCAL - ADIM ADIM TEŞHİS BAŞLIYOR [ ]")
print("==================================================")

# --- 1. ADIM: .env DOSYASI KONTROLÜ ---
print("\n[ADIM 1] .env dosyası ve MODEL_ALIAS kontrol ediliyor...")
if not os.path.exists(".env"):
    print("[X] HATA: Proje dizininde .env dosyası bulunamadı!")
    sys.exit(1)

load_dotenv()
model_alias = os.getenv("MODEL_ALIAS")
print(f"[V] .env dosyası okundu.")
print(f"[i] Sitemdeki mevcut MODEL_ALIAS değeri: '{model_alias}'")

if not model_alias:
    print("[X] HATA: .env dosyasının içinde MODEL_ALIAS tanımlanmamış!")
    sys.exit(1)


# --- 2. ADIM: SDK İMPORT KONTROLÜ ---
print("\n[ADIM 2] Foundry bağlantısı için OpenAI SDK kontrol ediliyor...")
try:
    from openai import OpenAI
    print("[V] Başarılı: Gerekli kütüphane (openai) import edildi.")
except ImportError as e:
    print(f"[X] HATA: Kütüphane import edilemedi! requirements.txt kurulmamış olabilir.")
    print(f"📋 Teknik Detay: {e}")
    sys.exit(1)


# --- 3. ADIM: FOUNDRY SUNUCU KONTROLÜ ---
print("\n[ADIM 3] Foundry sunucusu kontrol ediliyor...")
import subprocess
try:
    status_output = subprocess.check_output(["foundry", "server", "status"], text=True, encoding='utf-8', errors='ignore')
    endpoint = "Bulunamadı"
    for line in status_output.splitlines():
        if line.startswith("Web URLs"):
            endpoint = line.replace("Web URLs", "").strip()
            break
    if endpoint != "Bulunamadı":
        print("[V] Başarılı: Foundry sunucusu arka planda çalışıyor.")
        print(f"🔗 Servis Endpoint Adresi: {endpoint}")
    else:
        print("[X] HATA: Foundry sunucusu yanıt veriyor ancak URL bulunamadı.")
        sys.exit(1)
except Exception as e:
    print("[X] HATA: Foundry sunucusu durum bilgisi alınamadı!")
    print("💡 İpucu: Arka planda Microsoft Foundry servisinin açık olduğundan emin olun.")
    print(f"📋 Teknik Detay: {e}")
    sys.exit(1)


# --- 4. ADIM: MODELİN YÜKLENMESİ ---
print(f"\n[ADIM 4] '{model_alias}' modeli kontrol ediliyor ve yükleniyor...")
try:
    print("⚡ Model foundry üzerinden yükleniyor (Bu işlem cache durumuna göre biraz sürebilir)...")
    load_result = subprocess.run(["foundry", "model", "load", model_alias], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if load_result.returncode != 0:
        print("\n🚨 KRİTİK TESPİT: Model yüklenemedi!")
        print(f"👉 NEDENİ: Sisteminizde '{model_alias}' adında bir model bulunmuyor veya donanım uyumsuzluğu (örn. OpenVINO) yaşandı.")
        print("👉 ÇÖZÜM: 'foundry model download Phi-4-mini-instruct-generic-cpu' gibi CPU destekli bir modeli indirmeyi deneyin.")
        print(f"📋 Detay: {load_result.stderr}")
        sys.exit(1)
    else:
        print(f"[V] Başarılı: Model '{model_alias}' başarıyla belleğe yüklendi ve istek almaya hazır!")
except Exception as e:
    print("[X] HATA: Model yükleme işlemi sırasında beklenmedik bir çökme yaşandı!")
    print(f"📋 Teknik Detay: {e}")
    sys.exit(1)

print("\n==================================================")
print("🎉 TEBRİKLER: Tüm yerel sistem testleri başarıyla geçti!")
print("Uygulamanızda hiçbir çalışma zamanı engeli bulunmuyor.")
print("==================================================")