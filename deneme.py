import sys
# Eğer foundry kütüphanesi yüklüyse import edin
from foundry import FoundryManager 

def main():
    # 1. Foundry Yerel Sunucu Bağlantısını Başlatın
    # (Arka planda 'foundry server start' komutunun açık olduğundan emin olun)
    manager = FoundryManager()
    
    print("RTX 5060 için CUDA modeli hazırlanıyor...")
    
    try:
        # 2. Sizin belirttiğiniz satırla doğru model varyantını seçin
        chat_model = manager.catalog.get_model_variant("Phi-4-mini-instruct-cuda-gpu:5")
        
        # 3. Modeli RTX 5060'ın VRAM belleğine yükleyin
        print("Model ekran kartı belleğine (VRAM) yükleniyor...")
        loaded_model = chat_model.load()
        
        # 4. Model için prompt (girdi) hazırlayın
        # Phi-4 instruct modelleri soru-cevap formatında çok başarılıdır
        prompt = "Paris'te sadece 1 günüm var, kesinlikle görmem gereken en önemli 3 yer neresidir?"
        
        print("\n--- Model Yanıtı Başlıyor ---")
        
        # 5. Yanıtı oluşturun (Dilerseniz streaming/akış özelliğini de kullanabilirsiniz)
        response = loaded_model.complete(prompt)
        print(response.text)
        
        print("----------------------------")
        
    except Exception as e:
        print(f"Model çalıştırılırken bir hata oluştu: {e}", file=sys.stderr)
        print("Lütfen NVIDIA sürücülerinin ve Foundry servisinin aktif olduğunu kontrol edin.")

if __name__ == "__main__":
    main()