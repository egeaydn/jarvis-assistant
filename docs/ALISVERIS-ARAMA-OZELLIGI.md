# 🛒 Özellik Planı — Çoklu Site Ürün Arama (Shopping Search)

> Durum: **PLANLAMA** — henüz kod yazılmadı. Bu dosya hazır olduğunda "readme'ye göre ilerle ve başla" denilince uygulanacak yol haritasıdır.

---

## 1. Kullanıcı Senaryosu

Kullanıcı asistana örneğin şunu söyler:

> "Masa lambası almak istiyorum" / "Masa lambası ara"

Asistan bunu bir **satın alma niyeti** olarak algılar ve:

1. Sorguyu (`masa lambası`) Türkiye'de yaygın kullanılan alışveriş sitelerinin **arama sonucu URL'lerine** dönüştürür.
2. Chrome'u açar (kapalıysa başlatır, açıksa mevcut pencereye ekler) ve her site için **ayrı bir sekme** açar.
3. Kullanıcı ekranında üst tarafta her sitenin kendi arama sonuçları sekme halinde belirir — sanki biri o siteye girip ürünü kendisi aramış gibi.

Önemli sınır: Bu özellik **web scraping / veri kazıma yapmaz**, fiyat karşılaştırması üretmez, sitelerin HTML'ini indirip ayrıştırmaz. Sadece doğru "arama sonucu" URL'sini oluşturup tarayıcıda açar. Bunun nedenleri:

- Bu siteler (Hepsiburada, Trendyol, Amazon, N11, Sahibinden vb.) bot/anti-scraping korumaları kullanıyor; otomatik veri çekmek ToS ihlaline ve IP engellemesine yol açabilir.
- Kullanıcının istediği deneyim zaten "sekmeleri açık görmek" — ekstra veri işlemeye gerek yok.

---

## 2. Kapsam (MVP)

### Dahil edilecek siteler (Faz 1)

| Site | Arama URL Şablonu | Not |
|---|---|---|
| Trendyol | `https://www.trendyol.com/sr?q={q}` | Doğrulandı, stabil format |
| Hepsiburada | `https://www.hepsiburada.com/ara?q={q}` | Doğrulandı, stabil format |
| Amazon.com.tr | `https://www.amazon.com.tr/s?k={q}` | Doğrulandı, Amazon genel arama formatı |
| N11 | `https://www.n11.com/arama?q={q}` | Doğrulandı, stabil format |

`{q}` = `urllib.parse.quote_plus(query)` ile URL-encode edilmiş sorgu.

### Faz 2'ye bırakılacak (ikinci el / opsiyonel siteler)

| Site | Durum | Neden sonraya bırakıldı |
|---|---|---|
| Sahibinden.com | ⚠️ Doğrulama gerekiyor | Arama URL yapısı kategoriye göre değişebiliyor, kategori-agnostik genel arama endpoint'i test edilmeli |
| Letgo / Dolap | ⚠️ Doğrulama gerekiyor | İkinci el pazarları için URL formatı implementasyon sırasında canlı test edilecek |

Bu siteler MVP'de **kapalı (disabled)** olarak listede tutulacak; implementasyon sırasında gerçek tarayıcı testiyle URL formatı doğrulanınca aktif edilecekler. Yanlış/kırık bir URL açmaktansa, doğrulanana kadar devre dışı bırakmak tercih edilir.

---

## 3. Mimari Tasarım (Projeye Uygun)

Mevcut proje mimarisi (`app/tools/*` → `ToolManager` → `LLMManager` şeması → `Agent`) korunacak, yeni katman eklenmeyecek.

```
app/tools/shopping_tools.py     ← YENİ dosya, tüm mantık burada
        │
        ▼
app/tools/tool_manager.py       ← main.py'de tm.register(...) ile kayıt (mevcut sistem, değişmeyecek)
        │
        ▼
app/brain/llm_manager.py        ← GROQ_TOOLS listesine + Gemini FunctionDeclaration listesine yeni tool şeması eklenecek
        │
        ▼
app/brain/agent.py              ← SYSTEM_PROMPT'a "satın alma niyeti" kuralı eklenecek (CONFIRMATION_REQUIRED'a eklenmeyecek — salt okunur/zararsız işlem)
        │
        ▼
main.py > build_tool_manager()  ← import + tm.register("search_shopping", ...)
```

### Neden yeni dosya (`shopping_tools.py`) ve `browser_tools.py`'a eklenmiyor?

`browser_tools.py` genel amaçlı (tek URL / tek arama) kalsın; alışveriş özel mantığı (site listesi, çoklu sekme açma, sonuç raporlama) kendi dosyasında izole edilsin. Bu, `AGENTS.md` kuralı olan **"Keep code modular"** ile uyumlu.

---

## 4. Fonksiyon Tasarımı

### `app/tools/shopping_tools.py`

```python
SHOPPING_SITES: Dict[str, str] = {
    "trendyol":    "https://www.trendyol.com/sr?q={q}",
    "hepsiburada": "https://www.hepsiburada.com/ara?q={q}",
    "amazon":      "https://www.amazon.com.tr/s?k={q}",
    "n11":         "https://www.n11.com/arama?q={q}",
}

def build_search_urls(query: str, sites: Optional[List[str]] = None) -> Dict[str, str]:
    """Sorgu için her sitenin arama URL'sini üretir. Bilinmeyen site adı atlanır."""

def search_products(query: str, sites: Optional[List[str]] = None) -> Dict[str, Any]:
    """Chrome'da her site için ayrı sekme açar; hangi sitelerin açıldığını
    ve açılamayanları (varsa) döndürür."""
```

**Davranış detayları:**

- `query` boşsa `ValueError` (mevcut projedeki hata konvansiyonuna uygun — bkz. `browser_tools.open_website`).
- `sites=None` → varsayılan olarak MVP'deki 4 site (Trendyol, Hepsiburada, Amazon, N11) kullanılır.
- Kullanıcı "sahibindende de bak" derse LLM, `sites` parametresine `["sahibinden"]` gibi ekleyebilecek (ileride Faz 2 aktive olunca).
- Dönen sözlük örneği: `{"opened": ["trendyol", "hepsiburada", "amazon", "n11"], "failed": [], "query": "masa lambası"}` → Agent bu sonucu kullanıcıya "4 sitede 'masa lambası' araması açıldı: Trendyol, Hepsiburada, Amazon, N11" şeklinde özetler.

### Chrome'da Çoklu Sekme Açma Stratejisi

İki seçenek değerlendirildi:

1. **`webbrowser` modülü ile döngü** (`webbrowser.open(url, new=2)` her URL için) — basit ama bazı durumlarda her çağrıda yeni pencere açabilir, sıralama garanti değildir.
2. **Chrome'u doğrudan process olarak, tüm URL'leri argüman listesi halinde başlatmak** (`subprocess.Popen([chrome_path, url1, url2, url3, url4])`) — Chrome, birden fazla URL argümanını **aynı pencerede ayrı sekmeler** olarak açar (Chrome zaten çalışıyorsa mevcut pencereye sekme ekler, çalışmıyorsa yeni pencere + sekmeler açar). Bu, istenen "üstte alışveriş sitelerinin sekmeleri" görünümünü daha güvenilir verir.

→ **Seçilen yaklaşım: Seçenek 2.** `app_tools.py` içindeki mevcut `APP_PATHS["chrome"]` adaylarını (`_PROGRAMFILES`, `_PROGRAMFILES86`) tekrar kullanarak chrome.exe yolu bulunacak; bulunamazsa `webbrowser` modülüne (Seçenek 1) **fallback** yapılacak (kullanıcının chrome kurulu olmadığı ama başka varsayılan tarayıcısı olan senaryoları da desteklemek için).

---

## 5. Tool Kaydı ve Şema Değişiklikleri

### `main.py`

```python
from app.tools.shopping_tools import search_products
...
tm.register(
    "search_products",
    "Girilen urunu Turkiyedeki alisveris sitelerinde (Trendyol, Hepsiburada, Amazon, N11) arar ve sonuc sayfalarini Chrome'da sekme olarak acar",
    search_products,
    {"query": "str", "sites": "list[str] (opsiyonel)"},
)
```

### `app/brain/llm_manager.py`

`GROQ_TOOLS` listesine ve Gemini `FunctionDeclaration` listesine eşdeğer şema eklenecek:

```python
{"type": "function", "function": {
    "name": "search_products",
    "description": "Kullanicinin almak istedigi bir urunu Turkiye alisveris sitelerinde (Trendyol, Hepsiburada, Amazon, N11) arar; her sitenin arama sonucunu Chrome'da ayri sekme olarak acar.",
    "parameters": {"type": "object",
        "properties": {
            "query": {"type": "string", "description": "Aranacak urun adi, orn: masa lambasi"},
            "sites": {"type": "array", "items": {"type": "string"}, "description": "Opsiyonel: sadece belirli siteler (trendyol, hepsiburada, amazon, n11)"}},
        "required": ["query"]}}}
```

### `app/brain/agent.py` — `SYSTEM_PROMPT`

Yeni kural eklenecek:

```
- Kullanıcı bir ürün satın almak / bulmak istediğini belirtirse ("... almak istiyorum",
  "... arıyorum", "... satın alacağım" gibi ifadeler) search_products tool'unu çağır.
```

`CONFIRMATION_REQUIRED` kümesine **eklenmeyecek** — işlem yalnızca tarayıcıda salt-okunur sayfa açar, sistemde kalıcı/geri alınamaz bir değişiklik yapmaz.

---

## 6. Güvenlik & Kod Kalitesi Notları

- Sorgu, URL'ye eklenmeden önce mutlaka `urllib.parse.quote_plus` ile encode edilecek (mevcut `search_web` fonksiyonundaki pattern) → URL injection / kırık link riski engellenir.
- `sites` parametresiyle gelen değerler `SHOPPING_SITES` sözlüğünde whitelist kontrolünden geçirilecek; sözlükte olmayan bir site adı sessizce atlanacak (hata fırlatılmayacak, sadece `failed` listesine eklenecek).
- Chrome process başlatma hataları (`FileNotFoundError`, `OSError`) `try/except` ile yakalanacak ve `webbrowser` fallback'ine düşülecek (AGENTS.md rule_3: OS/subprocess çağrılarında hata yönetimi).
- Fonksiyonlara tip ipuçları (`str`, `Optional[List[str]]`, `Dict[str, Any]`) ve standart docstring eklenecek (AGENTS.md rule_2).

---

## 7. Test Planı (`tests/test_shopping_tools.py`)

Var olan test tarzına uygun (bkz. `tests/test_file_manager_tools.py`) şu senaryolar test edilecek:

1. `build_search_urls("masa lambası")` → 4 site için doğru encode edilmiş URL üretiyor mu (`%20` yerine `+` — `quote_plus` davranışı).
2. Boş sorgu → `ValueError`.
3. `sites=["trendyol"]` verildiğinde sadece 1 URL üretiliyor mu.
4. Bilinmeyen site adı (`sites=["xyz"]`) → sessizce atlanıyor, `failed` listesine düşüyor.
5. `search_products` içindeki Chrome başlatma çağrısı `unittest.mock.patch` ile mocklanarak gerçek tarayıcı açılmadan doğrulanacak (CI/test ortamında pencere açılmasını engellemek için).

---

## 8. Uygulama Adımları (Checklist — "başla" dendiğinde bu sırayla ilerlenecek)

- [ ] `app/tools/shopping_tools.py` oluştur: `SHOPPING_SITES`, `build_search_urls`, `search_products`
- [ ] `tests/test_shopping_tools.py` yaz ve çalıştır
- [ ] `main.py` → import + `tm.register("search_products", ...)`
- [ ] `app/brain/llm_manager.py` → `GROQ_TOOLS` + Gemini şemasına `search_products` ekle
- [ ] `app/brain/agent.py` → `SYSTEM_PROMPT`'a satın alma niyeti kuralı ekle
- [ ] Manuel test: `python main.py --text` ile "masa lambası almak istiyorum" komutu dene, 4 sekmenin doğru açıldığını doğrula
- [ ] README.md → "Araç (Tool) Kataloğu" bölümüne `search_products` satırı ekle
- [ ] (Faz 2) Sahibinden / Dolap URL formatlarını canlı doğrula, `SHOPPING_SITES`'a ekle

---

## 9. Gelecek Genişletme Fikirleri (Şimdilik Kapsam Dışı)

- Kullanıcının en son aramalarını `ConversationMemory`'de tutup "aynı ürünü tekrar ara" gibi kısayollar.
- Kategoriye özel siteler (elektronik → Teknosa/MediaMarkt, moda → Zara/Boyner) — kullanıcıdan gelen ürün tipine göre site listesini otomatik daraltma (basit anahtar kelime eşlemesiyle, LLM tool-calling'e ek yük bindirmeden).
- Fiyat/ürün verisi çekme (gerçek scraping) — hukuki ve teknik risk nedeniyle şu an **planlanmıyor**.
