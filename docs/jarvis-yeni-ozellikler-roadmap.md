# JARVIS — Yeni Özellikler Roadmap'i

Bu doküman, mevcut JARVIS mimarisine (ReAct ajan döngüsü, `ToolManager`, `CONFIRMATION_REQUIRED` güvenlik katmanı, Groq/Gemini function calling) uygun şekilde eklenecek iki başlık altındaki yeni araçları (tools) tanımlar:

1. **Güvenlik/Onay Sistemine Uygun Risk Taşıyan Yenilikler**
2. **Günlük Kullanım / Prodüktivite Araçları**

Her madde: amaç, önerilen dosya/konum, fonksiyon imzası, gerekli kütüphaneler, `CONFIRMATION_REQUIRED` durumu ve uygulama notlarını içerir.

---

## 1. Güvenlik/Onay Sistemine Uygun Risk Taşıyan Yenilikler

Bu araçlar geri döndürülemez veya sistem/veri üzerinde ciddi etkisi olan işlemler yapar. **Tümü `agent.py > CONFIRMATION_REQUIRED` kümesine eklenmelidir.**

### 1.1 Sistem Güç Yönetimi (`system_power_tools.py`)

**Amaç:** "bilgisayarı kapat", "yeniden başlat", "uyku moduna al" gibi komutları güvenli şekilde çalıştırmak.

**Önerilen dosya:** `app/tools/system_power_tools.py`

**Fonksiyonlar:**
```python
def shutdown_system(delay_seconds: int = 30) -> dict:
    """Windows'u kapatır. delay_seconds kadar bekleme süresi ile iptal şansı tanır."""
    # subprocess: shutdown /s /t {delay_seconds}

def restart_system(delay_seconds: int = 30) -> dict:
    # subprocess: shutdown /r /t {delay_seconds}

def sleep_system() -> dict:
    # ctypes ile SetSuspendState çağrısı

def cancel_shutdown() -> dict:
    # subprocess: shutdown /a
```

**Güvenlik notları:**
- Onay penceresinde kalan süreyi (`delay_seconds`) net göster.
- `cancel_shutdown` onay GEREKTİRMEZ — kullanıcı fikrini değiştirdiğinde hızlı iptal edebilmeli.
- GUI modunda onay penceresinde geri sayım göstermek iyi bir UX katkısı olur.

**`CONFIRMATION_REQUIRED`'a eklenecekler:** `shutdown_system`, `restart_system`, `sleep_system`

---

### 1.2 E-posta Gönderme (`email_tools.py`)

**Amaç:** "şu kişiye şu içerikte mail at" gibi komutlarla SMTP üzerinden e-posta göndermek.

**Önerilen dosya:** `app/tools/email_tools.py`

**Gerekli kütüphane:** `smtplib` (stdlib, ek kurulum gerekmez), opsiyonel `email.mime`

**Fonksiyon imzası:**
```python
def send_email(to: str, subject: str, body: str, attachments: list[str] = None) -> dict:
    """SMTP üzerinden e-posta gönderir. .env'den SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD okunur."""
```

**`.env` eklenecek değişkenler:**
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=          # Gmail için "Uygulama Şifresi" kullanılmalı, normal şifre değil
```

**Güvenlik notları:**
- Onay penceresinde alıcı, konu ve gövdenin **tam metni** gösterilmeli (LLM'in yanlış içerik üretme riskine karşı).
- Ekli dosya varsa yol doğrulaması yapılmalı (mevcut dosya mı, boyutu makul mü).
- `CONFIRMATION_REQUIRED`'a eklenmeli.

---

### 1.3 Kayıt Defteri (Registry) Düzenleme (`registry_tools.py`)

**Amaç:** Autostart dışındaki registry işlemlerini (ileri düzey kullanıcılar için) kontrollü şekilde açmak.

**Fonksiyon imzası:**
```python
def set_registry_value(hive: str, key_path: str, value_name: str, value_data, value_type: str = "REG_SZ") -> dict
def delete_registry_key(hive: str, key_path: str) -> dict
```

**Güvenlik notları:**
- Yüksek risk — yanlış kullanımda sistem bozulabilir. Onay penceresinde **tam registry yolu** ve mevcut değer (varsa) gösterilmeli.
- Whitelist yaklaşımı düşünülebilir: yalnızca belirli hive'lara (`HKEY_CURRENT_USER` gibi) izin ver, `HKEY_LOCAL_MACHINE` için ekstra uyarı.
- `CONFIRMATION_REQUIRED`'a eklenmeli; önerilir ki ilk sürümde sadece `HKCU` desteklensin.

---

### 1.4 Ağ/Firewall Kontrolü (`network_tools.py`)

**Amaç:** "wifi'yi kapat", "belirli bir uygulamayı internetten kısıtla" gibi komutlar.

**Fonksiyon imzası:**
```python
def toggle_wifi(enable: bool) -> dict
    # netsh interface set interface "Wi-Fi" enabled/disabled

def block_app_network(app_path: str) -> dict
    # netsh advfirewall firewall add rule ...
```

**Güvenlik notları:**
- `toggle_wifi(enable=False)` ve `block_app_network` onay gerektirir; `enable=True` gerektirmeyebilir (zarar riski düşük).
- `CONFIRMATION_REQUIRED`'a şartlı ekleme: aynı fonksiyon farklı parametrelerle farklı risk taşıyorsa, `agent.py` içindeki onay kontrolüne parametre bazlı bir istisna eklenebilir (örn. yalnızca `enable=False` onay ister).

---

### 1.5 Toplu Dosya Silme / Geri Dönüşüm Kutusuna Taşıma (`file_manager_tools.py` genişletmesi)

**Amaç:** Mevcut `delete_file` kalıcı silme yapıyor; bunun yerine **Geri Dönüşüm Kutusu'na taşıma** seçeneği eklemek riski azaltır.

**Fonksiyon imzası:**
```python
def move_to_recycle_bin(filepath: str) -> dict
    # send2trash kütüphanesi ile

def bulk_delete(folder_path: str, pattern: str) -> dict
    """Belirli bir pattern'e (örn. '*.tmp') uyan tüm dosyaları siler/taşır."""
```

**Gerekli kütüphane:** `send2trash`

**Güvenlik notları:**
- `move_to_recycle_bin` daha düşük risk taşıdığı için **varsayılan silme davranışı bu olmalı**, `delete_file` (kalıcı) ayrı ve daha "ağır" bir onay metniyle sunulmalı ("Bu işlem GERİ ALINAMAZ" uyarısı).
- `bulk_delete` özellikle riskli — onay penceresinde etkilenecek dosya sayısı ve isim listesi (ilk 10 tanesi + "...ve N tane daha") gösterilmeli.
- İkisi de `CONFIRMATION_REQUIRED`'a eklenmeli.

---

## 2. Günlük Kullanım / Prodüktivite Araçları

Bu araçlar düşük risk taşır, genelde `CONFIRMATION_REQUIRED` gerektirmez (aksi belirtilmedikçe).

### 2.1 Hatırlatıcı & Alarm (`reminder_tools.py`)

**Amaç:** "yarın saat 15:00'te toplantı hatırlat", "10 dakika sonra hatırlat" gibi doğal dil zaman komutlarını işlemek.

**Önerilen dosya:** `app/tools/reminder_tools.py`
**Gerekli kütüphane:** `schedule` veya stdlib `threading.Timer`; doğal dil zaman ayrıştırma için `dateparser`

**Fonksiyonlar:**
```python
def set_reminder(message: str, when: str) -> dict:
    """when: 'yarın 15:00', '10 dakika sonra' gibi doğal dil ifadeleri dateparser ile parse edilir."""

def list_reminders() -> dict
def cancel_reminder(reminder_id: str) -> dict
```

**Uygulama notu:**
- Hatırlatıcılar `app/services/` altında yeni bir `reminder_service.py` ile arka planda çalışan bir thread/scheduler'a ihtiyaç duyar; tetiklendiğinde mevcut TTS servisi (`services/tts.py`) ile seslendirilebilir ve GUI'de bir bildirim (toast/tray notification) gösterilebilir.
- Kalıcılık için hatırlatıcılar basit bir JSON dosyasına (`data/reminders.json`) kaydedilmeli ki uygulama kapanıp açılınca kaybolmasın.

---

### 2.2 Hızlı Not Alma (`notes_tools.py`)

**Amaç:** "not al: ...", "notlarımı göster" gibi komutlarla zaman damgalı not tutmak.

**Fonksiyonlar:**
```python
def add_note(content: str, tag: str = None) -> dict
    # data/notes.md dosyasına zaman damgasıyla ekler

def list_notes(tag: str = None, limit: int = 10) -> dict
def search_notes(query: str) -> dict
```

**Uygulama notu:**
- Basit bir markdown dosyası (append-only) yeterli; ileride SQLite'a geçilebilir.
- `search_notes` basit string arama ile başlayabilir, gerekirse `difflib` ile fuzzy arama eklenir.

---

### 2.3 Pano (Clipboard) Yönetimi (`clipboard_tools.py`)

**Amaç:** "şunu kopyala", "kopyaladığımı oku", "pano geçmişini göster" gibi komutlar.

**Gerekli kütüphane:** `pyperclip`

**Fonksiyonlar:**
```python
def copy_to_clipboard(text: str) -> dict
def read_clipboard() -> dict
def get_clipboard_history(limit: int = 5) -> dict
    """Arka planda pano değişikliklerini izleyen bir servisin biriktirdiği son N kaydı döndürür."""
```

**Uygulama notu:**
- `get_clipboard_history` için `app/services/clipboard_listener.py` adında arka planda polling yapan (örn. her 1 saniyede pano içeriğini kontrol eden) hafif bir servis gerekir; değişiklik olursa `data/clipboard_history.json`'a eklenir (son N kayıtla sınırlı, dairesel buffer mantığıyla).

---

### 2.4 Pencere Yönetimi (`window_tools.py`)

**Amaç:** "Chrome'u tam ekran yap", "Discord'u küçült", "tüm pencereleri göster" gibi komutlar.

**Gerekli kütüphane:** `pygetwindow`

**Fonksiyonlar:**
```python
def maximize_window(app_name: str) -> dict
def minimize_window(app_name: str) -> dict
def close_window(app_name: str) -> dict
def list_open_windows() -> dict
def focus_window(app_name: str) -> dict
```

**Uygulama notu:**
- Mevcut `app_tools.py` içindeki alias eşleme mantığı (`APP_PATHS`/alias sözlüğü) burada da tekrar kullanılabilir — pencere başlığı ile alias'ı eşleştirerek doğru pencereyi bulmak gerekir (`pygetwindow.getWindowsWithTitle`).

---

### 2.5 Ses Seviyesi Kontrolü (`volume_tools.py`)

**Amaç:** "sesi kıs", "sesi %50 yap", "sessize al" gibi komutlar.

**Gerekli kütüphane:** `pycaw` (Windows Core Audio API sarmalayıcısı)

**Fonksiyonlar:**
```python
def set_volume(percent: int) -> dict
def mute_volume(mute: bool = True) -> dict
def get_volume() -> dict
```

---

### 2.6 Sabah Brifingi / Günlük Özet (`briefing_tools.py`)

**Amaç:** "günaydın" tetikleyicisinde hava durumu, sistem durumu ve varsa bekleyen hatırlatıcıları tek bir sesli özet olarak sunmak.

**Fonksiyon imzası:**
```python
def get_daily_briefing() -> dict
    """
    İçerik:
    - Hava durumu (bir hava API'si, örn. OpenWeatherMap; .env'e WEATHER_API_KEY eklenmeli)
    - get_system_info() çıktısından özet (CPU/RAM/Disk)
    - list_reminders() içinden bugüne ait olanlar
    """
```

**Uygulama notu:**
- Bu araç mevcut `get_system_info` (sistem), yeni `list_reminders` (2.1) ve yeni bir hava durumu entegrasyonunu birleştiren bir "orkestrasyon" tool'u niteliğinde — ayrı bir API çağrısı yazmak yerine mevcut araçları çağırıp birleştirebilir.
- Wake-word validator'a `"günaydın"` gibi ek bir tetikleyici ifade eklenmesi gerekebilir (`services/wake_word_validator.py`).

---

### 2.7 Konuşma Geçmişinde Arama (`memory_search_tools.py`)

**Amaç:** "geçen hafta ne yapmıştık", "dün hangi dosyayı taşımıştım" gibi geçmişe dönük sorguları `ConversationMemory` / `AgentStepRecord` üzerinden yanıtlamak.

**Fonksiyon imzası:**
```python
def search_agent_history(query: str, days_back: int = 7) -> dict
    """ConversationMemory içindeki AgentStepRecord kayıtlarını tarih ve anahtar kelimeye göre filtreler."""
```

**Uygulama notu:**
- Mevcut `gecmis`/`history` komutu son adımları gösteriyor; bu tool bunun üzerine tarih filtresi ve arama ekler.
- `ConversationMemory`'nin diske kalıcı kaydedilmesi gerekebilir (şu an muhtemelen sadece bellekte tutuluyor) — bu değişiklik `app/brain/memory.py` içinde yapılmalı.

---

## Uygulama Sırası Önerisi

Bağımlılık ve karmaşıklık göz önüne alınarak önerilen sıralama:

1. **Clipboard yönetimi (2.3)** — en basit, tek dosyalık kütüphane bağımlılığı, hemen test edilebilir.
2. **Pencere yönetimi (2.4)** ve **Ses kontrolü (2.5)** — mevcut `app_tools.py` alias mantığından faydalanır, düşük risk.
3. **Not alma (2.2)** — basit dosya I/O, servis gerektirmez.
4. **Hatırlatıcı (2.1)** — yeni bir arka plan servisi gerektirdiği için biraz daha karmaşık; not alma sonrası mantıklı.
5. **Toplu dosya silme / recycle bin (1.5)** — mevcut `file_manager_tools.py`'a doğal bir ek, güvenlik katmanını genişletme pratiği için iyi bir başlangıç.
6. **E-posta gönderme (1.2)** — yeni `.env` değişkenleri ve harici SMTP bağımlılığı içerir.
7. **Sabah brifingi (2.6)** — diğer tool'ları (sistem, hatırlatıcı) birleştirdiği için onlardan sonra gelmeli.
8. **Sistem güç yönetimi (1.1)** — riski yüksek, dikkatli test edilmeli, geç fazda.
9. **Ağ/Firewall (1.4)** ve **Registry (1.3)** — en riskli ve en niş ihtiyaçlar; en son, isteğe bağlı.
10. **Konuşma geçmişinde arama (2.7)** — `ConversationMemory`'nin kalıcı hale getirilmesini gerektirdiği için ayrı bir alt görev olarak planlanmalı.

## Genel Notlar

- Her yeni tool, mevcut `main.py > build_tool_manager()` içinde `ToolManager.register()` ile kaydedilmeli ve hem Groq hem Gemini şemalarına `llm_manager.py` içinde eklenmelidir.
- Riskli tool'lar eklendikçe `agent.py > CONFIRMATION_REQUIRED` kümesi güncellenmeli; onay penceresi metinleri her tool için **spesifik ve anlaşılır** olmalı (genel "emin misiniz?" yerine "3 dosya kalıcı olarak silinecek: a.txt, b.txt, c.txt" gibi).
- Yeni servis gerektiren özellikler (hatırlatıcı, clipboard geçmişi) `app/services/` altına, thread-safe tasarımla (mevcut `assistant_state.py`'deki `RLock` yaklaşımına benzer şekilde) eklenmelidir.
- Yeni `.env` değişkenleri `.env.example` dosyasına da eklenmelidir ki proje kurulumu tutarlı kalsın.
