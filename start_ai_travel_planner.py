import os
import subprocess
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = r'"c:\Users\Sudem\Desktop\AI TRAVEL PLANNER\venv\Scripts\python.exe"'


def run_step(command, description):
    print(f"\n=== {description} ===")
    # shell=True yerine doğrudan komut listesi kullanmak daha güvenlidir.
    completed = subprocess.run(command, cwd=ROOT, text=True, shell=True)
    if completed.returncode != 0:
        raise SystemExit(f"Adım başarısız: {description} (kod: {completed.returncode})")


def main():
    print("AI Travel Planner başlangıç akışı başlatıldı...")
    
    # Adım 1: Yerel Foundry AI servisinin ve modelin çalışır durumda olduğunu doğrula
    try:
        run_step(f'{PYTHON_EXE} debug_test.py', "Yerel AI ve model teşhisi çalıştırılıyor")
        print("\n✅ Teşhis başarıyla tamamlandı. Ana sunucuya geçiliyor.")
    except SystemExit as e:
        print(f"\n❌ KRİTİK HATA: {e}")
        print("🔴 Lütfen yukarıdaki teşhis adımlarını kontrol edip sorunu giderin.")
        print("🔴 Yaygın Sorunlar: a) MS Foundry uygulamasının açık olmaması, b) .env dosyasındaki MODEL_ALIAS'ın yanlış olması.")
        return

    # Adım 2: Ana Flask sunucusunu başlat
    run_step(f'{PYTHON_EXE} app.py', "AI Travel Planner sunucusu başlatılıyor")


if __name__ == "__main__":
    main()
