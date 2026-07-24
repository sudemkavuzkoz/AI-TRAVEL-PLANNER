import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_ALIAS = os.getenv("MODEL_ALIAS", "phi-4-mini")

# Default system prompt: The model must stick to the context provided,
# not make up any information that is not in the context ("I don't know" rule).
DEFAULT_SYSTEM_PROMPT = (
    "You are an expert, creative, and highly organized Travel Assistant. Your mission is to help users design memorable, tailored, and realistic vacation plans. When creating a travel itinerary, ensure you cover: Day-by-Day Itinerary: Clear, realistic schedule with morning, afternoon, and evening activities. Accommodation & Logistics: Suggestions on where to stay, local transport options, and ideal travel seasons. Culinary & Cultural Highlights: Must-try local food, iconic spots, and unique hidden gems. Practical Tips: General budget guidelines, safety advice, and packing tips. If the user provides limited details, craft a well-rounded plan for their destination and ask clarifying questions (about budget, trip duration, or travel style) to help fine-tune it.")
_client = None
_model_id = None
_init_error = None

def _init_foundry():
    global _client, _model_id, _init_error
    
    if _client is not None:
        return

    _init_error = None
    _model_id = MODEL_ALIAS
    endpoint = os.getenv("FOUNDRY_BASE_URL", "http://127.0.0.1:62976/v1")

    try:
        import subprocess
        
        # 1. Modeli yükle (Foundry CLI çok daha akıllı, cache'lenmiş olanı bulur)
        print(f"[{MODEL_ALIAS}] kontrol ediliyor ve yükleniyor...")
        load_result = subprocess.run(["foundry", "model", "load", MODEL_ALIAS], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if load_result.returncode != 0:
             # Eğer yükleme başarısız olursa (örneğin daemon kapalıysa), hatayı yakalayalım.
             pass

        # 2. Endpoint'i otomatik bul
        try:
            status_output = subprocess.check_output(["foundry", "server", "status"], text=True, encoding='utf-8', errors='ignore')
            for line in status_output.splitlines():
                if line.startswith("Web URLs"):
                    foundry_url = line.replace("Web URLs", "").strip()
                    endpoint = f"{foundry_url}/v1"
                    break
        except Exception:
            pass
            
        # 3. OpenAI uyumlu istemciyi yapılandır
        _client = OpenAI(
            base_url=endpoint,
            api_key="local"
        )
        
    except Exception as e:
        _init_error = (
            "❌ Sistemsel Bir Hata Oluştu!\n\n"
            f"Model ('{MODEL_ALIAS}') yüklenirken bir sorun yaşandı.\n"
            f"Teknik Detay: {e}\n\n"
            "Lütfen Microsoft Foundry Local servisinin arka planda açık olduğundan emin olun."
        )


def generate_response(prompt, system_prompt=None, history=None):
    """Sends a contextual prompt to the LLM model and generates a response.
    If system_prompt is not provided, DEFAULT_SYSTEM_PROMPT is used. The caller
    (e.g., app.py) can customize the context brought by RAG and the citation instruction from here.
    history: list of {"role": "user"|"assistant", "content": str} – previous conversation turns.
    """
    _init_foundry()

    if _init_error is not None:
        return _init_error

    messages = [{"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT}]
    if history:
        for msg in history:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        response = _client.chat.completions.create(
            model=_model_id,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            frequency_penalty=1.0,
            presence_penalty=0.0
        )
        return response.choices[0].message.content

    except Exception as e:
        return (
            "❌ Yanıt Üretilemedi!\n\n"
            "Yapay zeka modeli cevap oluştururken bir hata ile karşılaştı.\n"
            f"Teknik Detay: {e}"
        )

def generate_response_stream(prompt, system_prompt=None, history=None):
    """LLM modeline bağlamlı promptu iletip yanıtı stream olarak üretir.
    history: list of {"role": "user"|"assistant", "content": str} – previous conversation turns.
    """
    _init_foundry()

    if _init_error is not None:
        yield _init_error
        return

    messages = [{"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT}]
    if history:
        for msg in history:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        response = _client.chat.completions.create(
            model=_model_id,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            frequency_penalty=1.0,
            presence_penalty=0.0,
            stream=True
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"\n\n❌ Hata: {e}"