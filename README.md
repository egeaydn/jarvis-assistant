# JARVIS — Otonom Sesli ve Görsel Masaüstü Asistanı

JARVIS, Windows üzerinde çalışan; doğal dil komutlarını yorumlayan, çok adımlı görevleri kendi başına planlayıp yürüten, ekranı görebilen ve sesli etkileşim kurabilen bir masaüstü yapay zekâ asistanıdır. Proje kod adı `ege-assistant`'tır; uygulama kimliği ve arayüzü ise `JARVIS` olarak sunulur.

Sistem, klasik "if/else komut eşleştirme" mantığından uzaklaşıp bir **ReAct (Reason + Act) ajan döngüsü** üzerine kurulmuştur: kullanıcı isteği LLM tarafından analiz edilir, gerekli araç (tool) seçilir, çalıştırılır, sonucu gözlemlenir ve gerekiyorsa yeni bir adım planlanır. Bu döngü, riskli işlemler öncesinde kullanıcıdan onay isteyen bir güvenlik katmanı ile sarmalanmıştır.

---

## İçindekiler

- [Mimari Genel Bakış](#mimari-genel-bakış)
- [Dizin Yapısı](#dizin-yapısı)
- [Çalışma Modları](#çalışma-modları)
- [Ajan Döngüsü (ReAct)](#ajan-döngüsü-react)
- [Araç (Tool) Kataloğu](#araç-tool-kataloğu)
- [Güvenlik Onay Sistemi](#güvenlik-onay-sistemi)
- [Sesli Etkileşim Alt Sistemi](#sesli-etkileşim-alt-sistemi)
- [Ekran Analizi (Screen Vision)](#ekran-analizi-screen-vision)
- [Alışveriş Araması (Shopping Search)](#alışveriş-araması-shopping-search)
- [Masaüstü Arayüzü (PySide6)](#masaüstü-arayüzü-pyside6)
- [LLM Sağlayıcı Katmanı](#llm-sağlayıcı-katmanı)
- [Kurulum](#kurulum)
- [Ortam Değişkenleri](#ortam-değişkenleri)
- [Kullanım](#kullanım)
- [Derleme (PyInstaller ile .exe üretimi)](#derleme-pyinstaller-ile-exe-üretimi)
- [Test](#test)
- [Bilinen Sınırlamalar](#bilinen-sınırlamalar)
- [Yol Haritası](#yol-haritası)

---

## Mimari Genel Bakış

Uygulama beş katmana ayrılmıştır:

```
main.py                    → giriş noktası, mod seçimi (GUI / --voice / --text)
app/brain/                 → LLM yönetimi, ajan döngüsü, konuşma hafızası
app/tools/                 → çalıştırılabilir araçlar ve merkezi araç kayıt sistemi
app/services/              → STT, TTS, wake-word, ekran yakalama, durum makinesi
app/ui/                    → PySide6 tabanlı HUD arayüzü ve stil tanımları
app/config/                → Windows başlangıç kaydı (autostart) yönetimi
```

Veri akışı özetle şu şekildedir:

```
Kullanıcı girdisi (metin veya ses)
        ↓
Agent.run()
        ↓
LLMManager.chat()  ──→  Groq veya Gemini function calling
        ↓
ToolManager.execute(tool_adı, **args)
        ↓
app/tools/* içindeki fonksiyon çalışır
        ↓
Gözlem (observation) LLM'e geri beslenir
        ↓
Yeterli bilgi toplandığında final_answer üretilir
```

`main.py`, üç farklı çalışma modunu tek bir `Agent` / `ToolManager` kurulumu üzerinden başlatır; bu sayede GUI, sesli CLI ve metin CLI modları aynı araç kümesini ve aynı güvenlik kurallarını paylaşır.

---

## Dizin Yapısı

```
ege-assistant/
├── main.py                          # Giriş noktası; tool kaydı ve mod seçimi
├── build_exe.py                     # PyInstaller ile tek dosyalık .exe üretimi
├── Jarvis.spec                      # PyInstaller derleme spesifikasyonu
├── requirements.txt
├── AGENTS.md                        # Depo genelinde geçerli kodlama kuralları
├── RoadMap.md                       # Faz faz geliştirme planı
├── assets/                          # Uygulama ikonları (.ico / .png / .svg)
├── app/
│   ├── brain/
│   │   ├── agent.py                 # ReAct döngüsü + güvenlik onay wrapper'ı
│   │   ├── llm_manager.py           # Groq / Gemini çift sağlayıcılı function calling
│   │   ├── memory.py                # Konuşma hafızası + ajan adım logu
│   │   └── command_parser.py        # Faz 2'den kalma basit anahtar kelime ayrıştırıcı
│   ├── tools/
│   │   ├── tool_manager.py          # Merkezi araç kayıt ve çalıştırma sistemi
│   │   ├── app_tools.py             # Uygulama açma/kapatma, alias ve process eşleme
│   │   ├── file_tools.py            # Dosya arama/açma
│   │   ├── file_manager_tools.py    # Klasör listeleme, taşıma, kopyalama, silme
│   │   ├── browser_tools.py         # URL açma, web arama
│   │   ├── shopping_tools.py        # Çoklu site ürün arama (Trendyol, Hepsiburada, Amazon, N11)
│   │   ├── screen_tools.py          # Ekran analizi ve ekran görüntüsü alma sarmalayıcıları
│   │   ├── system_tools.py          # CPU/RAM/Disk bilgisi
│   │   └── autonomous_tools.py      # Terminal komutu çalıştırma, klasör düzenleme
│   ├── services/
│   │   ├── stt.py                   # Google Speech API ile konuşma tanıma
│   │   ├── tts.py                   # pyttsx3 / Windows SAPI5 ile seslendirme
│   │   ├── wake_word.py             # "Hey Jarvis" arka plan dinleme motoru
│   │   ├── wake_word_validator.py   # Deterministik, yerel wake-word doğrulama
│   │   ├── audio_listener.py        # speech_recognition mikrofon sarmalayıcısı
│   │   ├── assistant_state.py       # Thread-safe asistan durum makinesi
│   │   └── vision.py                # mss ile ekran yakalama + Gemini görüntü analizi
│   ├── ui/
│   │   ├── window.py                # Ana pencere, tray icon, thread worker'ları
│   │   └── styles.py                # Qt stylesheet (QSS) tanımları
│   └── config/
│       └── startup.py               # winreg tabanlı Windows autostart yönetimi
└── tests/
    ├── test_toolmanager.py
    ├── test_parser.py
    ├── test_file_manager_tools.py
    ├── test_shopping_tools.py
    └── test_wake_word_validator.py
```

---

## Çalışma Modları

`main.py`, komut satırı argümanına göre üç moddan birini başlatır:

| Komut                | Mod                     | Açıklama |
|----------------------|-------------------------|----------|
| `python main.py`     | Grafik Arayüz (varsayılan) | PySide6 HUD penceresi, wake-word dinleme, tray icon, sistem göstergeleri |
| `python main.py --voice` | Sesli CLI            | Terminal üzerinden Enter'a basıp konuşarak etkileşim |
| `python main.py --text`  | Metin CLI             | Terminal üzerinden yazılı komut girişi |

GUI modunda konsol penceresi `_hide_console_window()` ile gizlenir (yalnızca geliştirme ortamında; derlenmiş `.exe` zaten konsolsuz çalışır). Her üç modda da aynı `Agent` örneği ve aynı `ToolManager` kaydı kullanılır; davranış farkı yalnızca girdi/çıktı katmanındadır.

---

## Ajan Döngüsü (ReAct)

`app/brain/agent.py` içindeki `Agent` sınıfı, `LLMManager`'ın function-calling döngüsünü sarmalayarak üç ek sorumluluk katar:

1. **Adım loglama** — her araç çağrısı bir `AgentStepRecord` (thought / action / action_input / observation) olarak `ConversationMemory` içine kaydedilir ve `gecmis` komutu ile görüntülenebilir.
2. **Güvenlik onayı** — `CONFIRMATION_REQUIRED` kümesinde tanımlı araçlar çağrılmadan önce `confirm_fn` üzerinden kullanıcı onayı istenir.
3. **Konuşma hafızası yönetimi** — kullanıcı/asistan mesajları `ConversationMemory` içinde tutulur ve `LLMManager`'a bağlam olarak aktarılır.

Döngü sonsuz çalışmaya karşı `MAX_STEPS` (8 adım) sınırıyla ve LLM'in döndürdüğü `FINISH` token'ı ile korunur. Bir hata oluşursa `AgentResult.success = False` olarak işaretlenir ve hata mesajı kullanıcıya iletilir.

---

## Araç (Tool) Kataloğu

Tüm araçlar `main.py > build_tool_manager()` içinde `ToolManager.register()` ile kayıt edilir ve hem Groq (OpenAI formatı) hem de Gemini (`FunctionDeclaration`) şemalarına `llm_manager.py` içinde ayrı ayrı çevrilir.

**Uygulama Kontrolü** (`app_tools.py`)
- `open_application(app_name)` — 30'dan fazla alias eşlemesiyle (chrome, discord, vscode, steam, ssms, xampp, geforce vb.) uygulama başlatır.
- `close_application(app_name)` — `psutil` ile eşleşen process'i sonlandırır.
- `get_running_apps()` — çalışan process listesini döndürür.

**Sistem Bilgisi** (`system_tools.py`)
- `get_system_info()` — CPU, RAM, disk kullanım yüzdeleri ve process sayısı.

**Tarayıcı / Web** (`browser_tools.py`)
- `open_website(url)`, `search_web(query)`.

**Alışveriş Araması** (`shopping_tools.py`)
- `search_products(query, sites=None)` — girilen ürünü Trendyol, Hepsiburada, Amazon.com.tr ve N11'de arar; sonuç sayfalarını Chrome'da ayrı sekme olarak açar (Chrome bulunamazsa varsayılan tarayıcıya geri döner). Çalışma prensibinin ayrıntısı için bkz. [Alışveriş Araması (Shopping Search)](#alışveriş-araması-shopping-search) bölümü ve [docs/ALISVERIS-ARAMA-OZELLIGI.md](docs/ALISVERIS-ARAMA-OZELLIGI.md).

**Dosya Arama** (`file_tools.py`)
- `find_file(filename)`, `open_file(filepath)`.

**Dosya / Klasör Yönetimi** (`file_manager_tools.py`)
- `list_directory(path)`, `get_common_path(location)`, `create_folder(folder_name, parent_path)`
- `filter_files_by_extension(path, extension)`, `get_file_info(filepath)`
- `move_file(src, dst)`, `copy_file(src, dst)`, `delete_file(filepath)` — **güvenlik onayı gerektirir**

**Ekran Analizi** (`screen_tools.py`, `vision.py`)
- `analyze_screen(prompt)` — ekran görüntüsünü `mss` ile yakalar, Gemini Vision (`gemini-3.6-flash`) ile analiz eder.
- `capture_screenshot(save_path)` — ekran görüntüsünü PNG olarak kaydeder.

**Otonom Görevler** (`autonomous_tools.py`)
- `run_terminal_command(command, cwd)` — PowerShell komutu çalıştırır, stdout/stderr/çıkış kodunu döndürür, 30 saniyelik zaman aşımı ile korunur. **Güvenlik onayı gerektirir.**
- `organize_folder(folder_path, rule)` — dosyaları uzantısına göre `Belgeler`, `Resimler`, `Arşivler`, `Videolar`, `Sesler`, `Kurulumlar` kategorilerine ayırıp alt klasörlere taşır. **Güvenlik onayı gerektirir.**

---

## Güvenlik Onay Sistemi

`agent.py > CONFIRMATION_REQUIRED` kümesinde tanımlı beş araç (`delete_file`, `move_file`, `copy_file`, `run_terminal_command`, `organize_folder`) çağrılmadan önce mutlaka onay ister:

- **CLI modlarında**: terminal üzerinden `e/h` (evet/hayır) sorusu.
- **GUI modunda**: `AgentWorker` içindeki `QMutex` + `QWaitCondition` köprüsü ile ana thread'e sinyal gönderilir, modern bir onay penceresi açılır ve kullanıcı onaylamadan (varsayılan zaman aşımı: 5 dakika) işlem gerçekleşmez.

Kullanıcı reddederse araç çalıştırılmaz; agent bu durumu `"İşlem kullanıcı tarafından iptal edildi."` gözlemiyle bir sonraki adıma taşır.

---

## Sesli Etkileşim Alt Sistemi

- **Wake-word motoru** (`services/wake_word.py`): arka planda mikrofonu dinler, yalnızca `AssistantStateManager` durumu `IDLE_WAKE_LISTENING` iken tetiklenir. Varsayılan yol Google STT + yerel doğrulama katmanıdır; `PICOVOICE_ACCESS_KEY` ve `PORCUPINE_KEYWORD_PATH` tanımlanırsa isteğe bağlı Porcupine motoruna geçilir.
- **Yerel doğrulama** (`services/wake_word_validator.py`): STT çıktısını LLM'e göndermeden, sıkı tam-eşleşme kurallarıyla (`hey jarvis`, `merhaba`, `merhaba ege` vb.) denetler; fuzzy eşleşme kullanılmaz, yanlış pozitifleri önlemek için tek kelimelik `jarvis` gibi ifadeler reddedilir.
- **Durum makinesi** (`services/assistant_state.py`): `IDLE_WAKE_LISTENING → GREETING → COMMAND_LISTENING → PROCESSING → SPEAKING` geçişlerini thread-safe (`RLock`) yönetir; mikrofon tray menüsünden kapatılabilir.
- **STT** (`services/stt.py`): Google Speech Recognition API, `tr-TR` varsayılan dil, otomatik ortam gürültüsü kalibrasyonu ve mikrofon erişim hatalarında yeniden deneme.
- **TTS** (`services/tts.py`): `pyttsx3` üzerinden Windows SAPI5 ile tamamen çevrimdışı seslendirme; sistemde Türkçe ses varsa otomatik seçilir.

---

## Ekran Analizi (Screen Vision)

`services/vision.py` iki bileşenden oluşur:

- `ScreenCapture` — `mss` kütüphanesi ile PyAutoGUI'ye kıyasla belirgin şekilde daha hızlı ekran/bölge yakalama yapar, PNG bytes veya dosya olarak döndürür.
- `VisionAnalyzer` — yakalanan görüntüyü Gemini (`gemini-3.6-flash`) modeline gönderir. Groq görüntü girişini desteklemediği için, aktif LLM sağlayıcısı ne olursa olsun görsel analiz her zaman Gemini üzerinden yürütülür ve `GEMINI_API_KEY` zorunludur.

---

## Alışveriş Araması (Shopping Search)

`app/tools/shopping_tools.py`, kullanıcının satın almak istediği bir ürünü Türkiye'de yaygın kullanılan alışveriş sitelerinde arayıp sonuç sayfalarını tarayıcıda sekme olarak açan bir araçtır. Bu modül veri kazıma (scraping) yapmaz; yalnızca ilgili sitenin arama sonucu URL'sini oluşturup açar, sanki kullanıcı o siteye girip kendisi aramış gibi bir deneyim sağlar.

### Desteklenen siteler

| Site | Arama URL Şablonu |
|---|---|
| Trendyol | `https://www.trendyol.com/sr?q={q}` |
| Hepsiburada | `https://www.hepsiburada.com/ara?q={q}` |
| Amazon.com.tr | `https://www.amazon.com.tr/s?k={q}` |
| N11 | `https://www.n11.com/arama?q={q}` |

`{q}`, aranacak ürün adının `urllib.parse.quote` ile kodlanmış halidir (boşluklar `%20` olarak kodlanır). `quote_plus`'ın ürettiği `+` karakteri bazı sitelerin arama kutusunda kelime ayracı olarak değil literal karakter olarak göründüğü için tercih edilmemiştir.

### Çalışma akışı

1. Kullanıcı bir satın alma niyeti belirttiğinde ("... almak istiyorum", "... arıyorum" gibi ifadeler), LLM `search_products(query, sites=None)` tool'unu çağırır.
2. `SYSTEM_PROMPT` içindeki kural gereği LLM, `query` parametresine kullanıcının tüm cümlesini değil, yalnızca ürünü tanımlayan kısa anahtar kelimeleri (ürün adı + varsa ölçü/renk/marka gibi ayırt edici özellikler) gönderir. Örnek: "kardeşimin fotoğrafını asmak için 15x20 bir çerçeve arıyorum bulabilir misin" ifadesinden `query="15x20 çerçeve"` çıkarılır.
3. `build_search_urls(query, sites)`, `SHOPPING_SITES` sözlüğündeki şablonları encode edilmiş sorgu ile doldurarak her site için bir URL üretir; `sites` parametresi verilmezse dört sitenin tamamı kullanılır, bilinmeyen site adları sessizce atlanır.
4. `_find_chrome_path()`, `app_tools.APP_PATHS["chrome"]` içindeki aday kurulum yollarını kontrol ederek sistemde kurulu Chrome'un tam yolunu bulur.
5. Chrome bulunursa `subprocess.Popen([chrome_path, *urls])` çağrılır; tüm URL'ler tek seferde process argümanı olarak verildiği için Chrome bunları aynı pencerede ayrı sekmeler halinde açar (Chrome zaten çalışıyorsa mevcut pencereye sekme eklenir).
6. Chrome bulunamaz veya başlatma sırasında `OSError` oluşursa, `webbrowser.open(url, new=2)` ile sistemin varsayılan tarayıcısına geri dönülür.
7. Fonksiyon `{"opened": [...], "failed": [...], "query": ...}` biçiminde bir sonuç döndürür; Agent bu sonucu kullanıcıya kısa bir Türkçe özet olarak iletir.

Özelliğin kapsamı, tasarım kararları ve ileride eklenmesi planlanan siteler (Sahibinden, Dolap vb.) için bkz. [docs/ALISVERIS-ARAMA-OZELLIGI.md](docs/ALISVERIS-ARAMA-OZELLIGI.md).

---

## Masaüstü Arayüzü (PySide6)

`app/ui/window.py`, çerçevesiz (frameless) bir `QMainWindow` üzerine kurulu holografik bir HUD tasarımıdır:

- **Arc Reactor animasyonu** — `QPainter` ile çizilen, sürekli dönen ve merkezde nabız gibi atan özel bir widget (`ArcReactorWidget`).
- **Sistem tepsisi (tray) entegrasyonu** — pencere kapatıldığında arka plana küçülür, çift tıklamayla geri gelir.
- **Canlı sistem göstergeleri** — CPU/RAM/Disk kullanımı 1 saniyede bir `psutil` ile güncellenir.
- **Windows başlangıcında otomatik çalışma** — `app/config/startup.py` üzerinden `winreg` ile kayıt defterine yazılır; geliştirme modunda `pythonw.exe`, derlenmiş modda doğrudan `.exe` yolu kullanılır.
- **Thread mimarisi** — `AgentWorker`, `VoiceWorker` ve `TTSWorker` sınıfları ağır işlemleri (LLM çağrısı, mikrofon dinleme, seslendirme) arayüz thread'inin dışında çalıştırarak donmayı engeller. Güvenlik onayları `QMutex` + `QWaitCondition` ile thread'ler arası senkronize edilir.
- **Taşınabilir ikon çözümü** — `FramelessWindowHint` kullanan pencerelerde görev çubuğunun `python.exe` simgesine düşmesini önlemek için Win32 API (`LoadImageW`, `SetClassLongPtrW`) doğrudan çağrılır.

---

## LLM Sağlayıcı Katmanı

`app/brain/llm_manager.py`, tek bir arayüz (`chat()`, `reset()`) arkasında iki sağlayıcıyı destekler:

| Sağlayıcı | Model | Kullanım |
|-----------|-------|----------|
| **Groq** (varsayılan) | `openai/gpt-oss-120b` | OpenAI uyumlu function-calling formatı, ücretsiz kota |
| **Gemini** | `gemini-3.6-flash` | Google GenAI SDK, `FunctionDeclaration` şeması, ekran analizi için zorunlu |

Sağlayıcı seçimi `LLM_PROVIDER` ortam değişkeni (`groq` | `gemini`) veya `LLMManager(provider=...)` parametresiyle yapılır. Sistem promptu (`SYSTEM_PROMPT`), agent'a Türkçe yanıt verme, karmaşık görevleri adımlara bölme, proje çalıştırma/hata ayıklama akışı (bağımlılık dosyalarını tespit et → çalıştır → hata varsa analiz edip düzelt) ve riskli işlemlerde kullanıcıyı bilgilendirme kurallarını tanımlar.

---

## Kurulum

### Gereksinimler

- Python 3.12 veya üzeri
- Windows 10/11 (uygulama; `winreg`, SAPI5 ve process yönetimi Windows'a özgüdür)
- Mikrofon (sesli mod ve wake-word için)

### Adımlar

```powershell
# Sanal ortam oluştur
python -m venv .venv

# Sanal ortamı aktive et
.venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

`requirements.txt` içeriği:

```
psutil, PySide6, google-genai, groq, python-dotenv
SpeechRecognition, pyaudio, pyttsx3
pvporcupine, pvrecorder   (isteğe bağlı wake-word motoru)
mss, pillow
pytest, pyinstaller       (geliştirme / paketleme)
```

---

## Ortam Değişkenleri

Kök dizinde bir `.env` dosyası oluşturun:

```env
# Zorunlu — en az bir LLM sağlayıcı anahtarı gereklidir
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here      # Ekran analizi (Vision) için zorunlu

# İsteğe bağlı
LLM_PROVIDER=groq                            # groq | gemini (varsayılan: groq)
WAKE_STT_LANGUAGE=tr-TR                      # Wake-word STT dili (BCP-47)
PICOVOICE_ACCESS_KEY=                        # Porcupine motoru için
PORCUPINE_KEYWORD_PATH=                      # Özel .ppn anahtar kelime dosyası yolu
```

`GEMINI_API_KEY` tanımlı değilse `analyze_screen` ve `capture_screenshot` dışındaki tüm araçlar Groq üzerinden çalışmaya devam eder; yalnızca ekran analizi kullanılamaz.

---

## Kullanım

```powershell
# Grafik arayüz (önerilen, varsayılan mod)
python main.py

# Sesli CLI modu
python main.py --voice

# Metin CLI modu
python main.py --text
```

Metin ve sesli CLI modlarında kullanılabilecek özel komutlar:

| Komut | Açıklama |
|-------|----------|
| `sifirla` / `reset` | Konuşma geçmişini ve ajan hafızasını temizler |
| `gecmis` / `history` | Son ajan adımlarını (thought/action/observation) gösterir |
| `cikis` / `exit` / `quit` | Programdan çıkar |

Örnek çok adımlı görev:

```
Sen: indirilenler klasörümdeki pdf dosyalarını belgeler altında yeni bir klasöre taşı

Agent:
  1) list_directory("indirilenler")
  2) filter_files_by_extension("indirilenler", "pdf")
  3) create_folder("PDF Arsivi", "belgeler")
  4) move_file(...) × N   → her biri için güvenlik onayı istenir
```

---

## Derleme (PyInstaller ile .exe üretimi)

```powershell
python build_exe.py
```

`build_exe.py`, sanal ortamdaki `pyinstaller.exe`'yi bularak aşağıdaki ayarlarla tek dosyalık bir derleme yapar (`Jarvis.spec` ile eşdeğer):

- `--onefile` — tek bir çalıştırılabilir dosya
- `--windowed` — konsol penceresi açılmaz
- `--add-data=assets;assets` — ikon ve varlıkları pakete gömer
- `--icon=assets/ege-assistant-icon.ico`

Derleme sonunda çıktı `dist/Jarvis.exe` altında oluşur. `.exe` başlangıçta autostart ile çalıştırılırsa (`app/config/startup.py`), `--minimized` argümanıyla tray moduna küçülmüş olarak açılır.

---

## Test

```powershell
pytest
```

Mevcut test dosyaları:

- `tests/test_toolmanager.py` — `ToolManager` kayıt/çalıştırma davranışı
- `tests/test_parser.py` — `app/brain/command_parser.py` içindeki Faz 2 anahtar kelime ayrıştırıcı
- `tests/test_file_manager_tools.py` — dosya/klasör araçlarının uç durumları
- `tests/test_shopping_tools.py` — `shopping_tools.py` içindeki URL oluşturma, site filtreleme ve Chrome/tarayıcı fallback senaryoları
- `tests/test_wake_word_validator.py` — wake-word doğrulama kurallarının kabul/red senaryoları

---

## Bilinen Sınırlamalar

- STT ve wake-word varsayılan yolu internet bağlantısı gerektirir (Google Speech API); çevrimdışı alternatif yalnızca Porcupine motoru etkinleştirildiğinde kısmen sağlanır.
- `run_terminal_command` sabit 30 saniyelik zaman aşımına sahiptir; uzun süren komutlar (örn. büyük paket kurulumları) bu sınırı aşabilir.
- Uygulama açma/kapatma ve autostart mekanizması Windows'a özgüdür (`winreg`, `.exe` alias eşlemeleri); macOS/Linux desteklenmez.
- `command_parser.py` yalnızca erken faz (Faz 2) anahtar kelime eşleştirmesi için korunmaktadır ve ana ajan döngüsü tarafından kullanılmamaktadır.

---

## Yol Haritası

Ayrıntılı faz planı için bkz. [RoadMap.md](RoadMap.md). Özetle:

```
Faz 0  Proje kurulumu                      tamamlandı
Faz 1  Bilgisayar kontrolü (psutil/subprocess)  tamamlandı
Faz 2  Metin tabanlı asistan                tamamlandı
Faz 3  Araç (tool) sistemi                  tamamlandı
Faz 4  LLM + function calling               tamamlandı
Faz 5  AI Agent (ReAct) + dosya yönetimi    tamamlandı
Faz 6  Sesli asistan (STT/TTS)              tamamlandı
Faz 7  Ekran analizi (Screen Vision)        tamamlandı
Faz 8  Modern masaüstü arayüzü (PySide6)   tamamlandı
Faz 9  Otonom asistan (terminal + klasör düzenleme)  tamamlandı
```

Bu belge, kod tabanının güncel (main branch) durumunu yansıtır; `AGENTS.md` içindeki katkı kurallarına (modüler yapı, tip ipuçları, `try/except` ile hata yönetimi) uygun şekilde güncellenmelidir.
