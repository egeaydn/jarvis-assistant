# 🤖 EGE ASSISTANT — Development Roadmap

> **Proje amacı:**
> Python ile geliştirilen, kullanıcının yazılı veya sesli komutlarını anlayabilen ve bilgisayarda belirli işlemleri gerçekleştirebilen kişisel bir AI Assistant geliştirmek.
>
> Bu proje boyunca klasik şekilde önce Python kursu bitirip sonra proje yapmayacağız.
>
> **Öğren → Uygula → Boz → Düzelt → Devam et** yaklaşımıyla ilerleyeceğiz.
>
> AI araçlarını ve vibe coding'i kullanacağız ancak yazılan kodların temel mantığını anlamadan ilerlemeyeceğiz.

---

# 🎯 Final Vision

Projenin ileride ulaşmasını istediğimiz nokta:

```text
┌─────────────────────────────────────────────┐
│                                             │
│              🤖 EGE ASSISTANT               │
│                                             │
│        "Bugün sana nasıl yardımcı olabilirim?"│
│                                             │
│  🎙️ Dinliyor...                              │
│                                             │
└─────────────────────────────────────────────┘
```

Kullanıcı:

> "Chrome'u aç."

Assistant:

```text
🧠 Komut analiz ediliyor...

🔧 Tool seçildi:
open_application("chrome")

🚀 Chrome açılıyor...
```

İlerleyen aşamalarda:

* Uygulamaları açabilecek
* Uygulamaları kapatabilecek
* Açık uygulamaları görebilecek
* Dosya arayabilecek
* Dosya açabilecek
* İnternette arama yapabilecek
* Sesli komutları anlayabilecek
* Sesli cevap verebilecek
* Ekranı analiz edebilecek
* AI Agent mantığıyla Tool Calling kullanabilecek
* Daha karmaşık görevleri adım adım gerçekleştirebilecek

---

# 🗺️ Genel Roadmap

```text
PHASE 0
│
├── Proje ortamının kurulması
│
▼
PHASE 1
│
├── Python ile bilgisayar kontrolü
│
▼
PHASE 2
│
├── Text tabanlı Assistant
│
▼
PHASE 3
│
├── Tool System
│
▼
PHASE 4
│
├── LLM + Tool Calling
│
▼
PHASE 5
│
├── AI Agent
│
▼
PHASE 6
│
├── Voice Assistant
│
▼
PHASE 7
│
├── Screen Vision
│
▼
PHASE 8
│
├── Modern Desktop UI
│
▼
PHASE 9
│
└── Autonomous Assistant
```

---

# 🟢 PHASE 0 — Project Setup

## Amaç

Projeyi düzgün bir yapıyla başlatmak.

İlk hedef:

```text
ege-assistant/
│
├── main.py
├── requirements.txt
├── README.md
└── roadmap.md
```

Daha sonra proje büyüdükçe:

```text
ege-assistant/
│
├── app/
│   ├── brain/
│   ├── tools/
│   ├── services/
│   ├── ui/
│   └── config/
│
├── tests/
│
├── main.py
├── requirements.txt
├── README.md
└── roadmap.md
```

## Öğreneceğimiz Python Konuları

Bu aşamada sadece ihtiyacımız olan kadar:

* Python dosyaları
* `import`
* Fonksiyonlar
* `if`
* `try / except`
* Virtual environment
* `pip`
* Package mantığı

## Hedef

```bash
python main.py
```

çalıştığında:

```text
🤖 Ege Assistant başlatıldı.
```

görmek.

### Done When

* [ ] Python kurulu
* [ ] VS Code hazır
* [ ] Virtual environment oluşturuldu
* [ ] Git repository oluşturuldu
* [ ] İlk Python programı çalışıyor

---

# 🟡 PHASE 1 — Computer Control

## Amaç

Python'ın bilgisayar üzerinde işlem yapabilmesini sağlamak.

Bu aşamada henüz AI yok.

Önce elimizde çalışan **tool'lar** olacak.

Örnek:

```text
open_application("chrome")
```

veya:

```text
get_running_apps()
```

## Tool'lar

### 1. Open Application

```text
Kullanıcı:
Chrome'u aç

↓

Python:
Chrome.exe çalıştır

↓

Chrome açılır
```

Desteklenecek uygulamalar:

* Chrome
* VS Code
* Spotify
* Discord
* Steam
* Notepad

### 2. Close Application

Örnek:

```text
Discord'u kapat
```

Python:

```text
Running processes
        ↓
Discord bulunur
        ↓
Process terminate edilir
```

### 3. Get Running Applications

Örnek çıktı:

```text
Şu anda açık uygulamalar:

- Chrome
- VS Code
- Discord
- Spotify
```

### 4. System Information

Assistant şunları okuyabilecek:

* CPU kullanımı
* RAM kullanımı
* Disk kullanımı
* Çalışan process sayısı

Örnek:

```text
CPU: %34

RAM: %62

Running Processes: 187
```

## Kullanılacak Teknolojiler

* `subprocess`
* `os`
* `psutil`

## Done When

Şu komutlar Python üzerinden çalışıyor:

```text
open_application("chrome")

close_application("discord")

get_running_apps()

get_system_info()
```

---

# 🟠 PHASE 2 — Text Based Assistant

## Amaç

Kullanıcının doğal dil benzeri komutlar yazabilmesi.

İlk versiyon:

```text
You: chrome aç

Assistant: Chrome açılıyor...
```

Başlangıçta gerçek AI kullanmayacağız.

Basit command parser:

```text
"chrome aç"
      ↓
Command Parser
      ↓
Application = chrome
Action = open
      ↓
open_application("chrome")
```

Örnek komutlar:

```text
chrome aç

spotify aç

discord'u kapat

açık uygulamaları göster

sistem bilgilerini göster
```

## Öğreneceğimiz Python Konuları

* String işlemleri
* Dictionary
* List
* Fonksiyon parametreleri
* Return
* Basic class mantığı

## Done When

Terminalde:

```text
🤖 Ege Assistant hazır.

Sen:
>
```

çalışıyor.

Komut yazıldığında işlem gerçekleştiriliyor.

---

# 🔵 PHASE 3 — Tool System

## Amaç

Assistant'ın yapabileceği işlemleri modüler hale getirmek.

Artık böyle dağınık bir yapı istemiyoruz:

```python
if "chrome" in command:
    ...

if "spotify" in command:
    ...

if "discord" in command:
    ...
```

Onun yerine:

```text
User
  ↓
Assistant
  ↓
Tool Manager
  ↓
┌───────────────────┐
│ Open App Tool     │
│ Close App Tool    │
│ File Search Tool  │
│ System Info Tool  │
│ Web Search Tool   │
└───────────────────┘
```

## Tool Yapısı

Örnek:

```python
def open_application(app_name):
    pass
```

Başka bir tool:

```python
def get_system_info():
    pass
```

Her tool ayrı bir göreve sahip olacak.

## Planlanan Tool'lar

### Application Tools

```text
open_application()

close_application()

get_running_apps()
```

### File Tools

```text
find_file()

open_file()

search_files()
```

### System Tools

```text
get_cpu_usage()

get_ram_usage()

get_disk_usage()
```

### Browser Tools

```text
open_website()

search_web()
```

## Done When

Yeni bir özellik eklemek için sadece yeni bir tool dosyası oluşturabiliyoruz.

---

# 🧠 PHASE 4 — LLM Integration

## Amaç

Artık komutları `if` bloklarıyla anlamaya çalışmak yerine bir LLM kullanmak.

Örnek:

```text
User:

"Spotify'ı aç ve lo-fi müzik ara."
```

LLM bunu analiz eder:

```json
{
    "tool": "open_application",
    "arguments": {
        "application": "spotify"
    }
}
```

Sonra:

```text
Tool çağrılır

↓

Spotify açılır

↓

İkinci işlem gerçekleştirilir
```

## Mimari

```text
USER
 │
 ▼
LLM
 │
 │ "Kullanıcı ne istiyor?"
 ▼
TOOL CALL
 │
 ├── open_application()
 │
 ├── close_application()
 │
 ├── search_files()
 │
 └── get_system_info()
```

## Model Seçenekleri

Başlangıçta:

* Ollama ile local model

Daha sonra isteğe bağlı:

* Cloud API
* Daha güçlü tool-calling modelleri

## Öğreneceğimiz Konular

* API mantığı
* JSON
* LLM
* Prompt
* Tool Calling
* Function Calling

## Done When

Şu komutlar doğal dil ile çalışıyor:

```text
Chrome'u aç.

Bilgisayarımda Discord açık mı?

CPU kullanımım kaç?

Masaüstümdeki PDF dosyalarını bul.
```

---

# 🤖 PHASE 5 — AI Agent

## Amaç

Assistant'ın tek bir komutu birden fazla adıma bölebilmesi.

Örnek:

```text
"İndirilenler klasörümü kontrol et ve PDF'leri aç."
```

Assistant düşünür:

```text
STEP 1

Downloads klasörünü bul
        ↓

STEP 2

Dosyaları listele
        ↓

STEP 3

PDF dosyalarını filtrele
        ↓

STEP 4

Dosyayı aç
```

## Agent Loop

```text
User Request
      ↓
LLM
      ↓
Plan oluştur
      ↓
Tool seç
      ↓
Tool çalıştır
      ↓
Sonucu değerlendir
      ↓
Başka işlem gerekiyor mu?
      ↓
EVET ──────────┐
               │
               ▼
              LLM
               │
HAYIR          │
  │            │
  ▼            │
Response ◄─────┘
```

## Burada Öğreneceğimiz Konular

* AI Agent
* ReAct Pattern
* Planning
* Tool Execution
* Agent Loop
* Memory

## Done When

Assistant birden fazla tool kullanarak görev tamamlayabiliyor.

---

# 🎙️ PHASE 6 — Voice Assistant

## Amaç

Assistant ile konuşabilmek.

Mimari:

```text
🎙️ Microphone

      ↓

Speech To Text

      ↓

"Chrome'u aç"

      ↓

LLM

      ↓

Tool Calling

      ↓

Chrome açılır

      ↓

Text To Speech

      ↓

🔊 "Chrome açıldı."
```

## Özellikler

* Mikrofon dinleme
* Speech-to-Text
* Wake word

Örnek:

```text
"Hey Ege"
```

veya ileride farklı bir isim.

Sonra:

```text
"Chrome'u aç."
```

## Text To Speech

Assistant sesli cevap verecek.

Örnek:

> 🔊 "Chrome açılıyor."

## Done When

Klavye kullanmadan:

```text
🎙️ "Spotify'ı aç."
```

dediğimizde işlem gerçekleşiyor.

---

# 👁️ PHASE 7 — Screen Vision

## Amaç

Assistant'ın ekranı analiz edebilmesi.

Örnek:

```text
"Ekranımda ne görüyorsun?"
```

Sistem:

```text
Screenshot
     ↓
Vision Model
     ↓
Analysis
```

Assistant:

> "VS Code açık. Terminalde bir Python hata mesajı görünüyor."

## Kullanım Senaryoları

### Error Analysis

```text
"Bu hata ne?"
```

Assistant:

```text
Screenshot
     ↓
Error Detection
     ↓
LLM Analysis
```

### UI Understanding

```text
"Bu sayfada ne var?"
```

### Computer Vision + AI

İleride:

```text
"Şu butona tıkla."
```

Assistant:

```text
Screen Analysis
      ↓
Element Detection
      ↓
Mouse Action
```

⚠️ Bu aşamada güvenlik sistemi önemli olacak.

Assistant ekranda gördüğü her şeye kafasına göre tıklamayacak.

---

# 🖥️ PHASE 8 — Modern Desktop UI

## Amaç

Terminalden kurtulmak.

Modern bir desktop assistant arayüzü oluşturmak.

Önerilen teknoloji:

```text
PySide6
```

## UI Fikri

```text
┌─────────────────────────────────────┐
│ 🤖 EGE ASSISTANT                    │
├─────────────────────────────────────┤
│                                     │
│  👤 Chrome'u aç                     │
│                                     │
│  🤖 Chrome açılıyor...              │
│                                     │
│  ─────────────────────────────      │
│                                     │
│  CPU        ███████░░ 72%           │
│  RAM        █████░░░░░ 48%          │
│                                     │
├─────────────────────────────────────┤
│ 💬 Bir şey yaz...              🎙️   │
└─────────────────────────────────────┘
```

## Özellikler

* Chat UI
* Voice button
* Tool execution log
* System information
* Floating mode
* Dark mode

## Done When

Uygulama terminalden bağımsız çalışıyor.

---

# 🧠 PHASE 9 — Autonomous Assistant

## Amaç

Final boss. 💀

Assistant artık daha karmaşık görevleri gerçekleştirebilecek.

Örnek:

> "İndirilenler klasörümü düzenle."

Assistant önce sorabilir:

> "Hangi kurala göre düzenlememi istersin?"

Sonra:

```text
Downloads
    ↓
Dosyaları analiz et
    ↓
File types belirle
    ↓
Klasör oluştur
    ↓
Dosyaları taşı
    ↓
Sonucu bildir
```

Başka örnek:

> "Bu projeyi çalıştırmayı dene."

Assistant:

```text
Project analiz edilir
        ↓
package.json / requirements.txt bulunur
        ↓
Gerekli komut belirlenir
        ↓
Terminal açılır
        ↓
Komut çalıştırılır
        ↓
Hata varsa analiz edilir
```

---

# 🔐 Security System

Bu proje bilgisayarı kontrol edeceği için bazı işlemler onay gerektirecek.

Örneğin:

```text
⚠️ Dosya silme işlemi

Assistant:

"C:\Users\Ege\Desktop\test.txt"

dosyasını silmek istiyor.

[ Onayla ] [ İptal ]
```

Onaysız yapılmayacak işlemler:

* Dosya silme
* Dosya taşıma
* Program kapatma
* Terminal komutu çalıştırma
* Sistem ayarlarını değiştirme
* Çoklu mouse/klavye aksiyonları

Kural:

> **Assistant güçlü olacak ama kafasına göre Windows'u yakmayacak.**

---

# 📚 Python Learning Strategy

Python'ı ayrı bir ders gibi bitirmeye çalışmayacağız.

İhtiyaç çıktıkça öğreneceğiz.

Örnek:

### `function` lazım oldu

```python
def open_application(name):
    ...
```

→ Fonksiyon nedir, neden kullanıyoruz?

### `dictionary` lazım oldu

```python
apps = {
    "chrome": "...",
    "spotify": "..."
}
```

→ Dictionary neden var?

### `class` lazım oldu

```python
class ToolManager:
    ...
```

→ Class burada neden mantıklı?

Yani yaklaşım:

```text
PROBLEM
   ↓
İhtiyacımız olan Python konusu
   ↓
Mini açıklama
   ↓
Kod
   ↓
Projeye entegre et
```

---

# 🛠️ Development Philosophy

Bu projede vibe coding kullanacağız.

Ama şu kurallar geçerli:

## ❌ Yapmayacağımız şey

```text
"Cursor, bana komple Jarvis yap."

→ 400 dosya

→ 27 hata

→ Kimse ne olduğunu bilmiyor

→ Proje mezarlığı
```

## ✅ Yapacağımız şey

```text
Küçük feature seç
        ↓
Ne yapacağını belirle
        ↓
AI ile kod üret
        ↓
Kodu incele
        ↓
Çalıştır
        ↓
Hata al
        ↓
Hata nedenini anlamaya çalış
        ↓
Düzelt
        ↓
Git commit
        ↓
Sonraki feature
```

---

# 🚀 Version Roadmap

## v0.1 — Computer Control

* [ ] Open application
* [ ] Close application
* [ ] Running apps
* [ ] System info

---

## v0.2 — Text Assistant

* [ ] Command input
* [ ] Command parser
* [ ] Basic responses
* [ ] Error handling

---

## v0.3 — Tool System

* [ ] Tool manager
* [ ] Modular architecture
* [ ] File tools
* [ ] Browser tools

---

## v0.4 — LLM Brain

* [ ] Ollama integration
* [ ] Prompt system
* [ ] Tool calling
* [ ] JSON response handling

---

## v0.5 — AI Agent

* [ ] Multi-step tasks
* [ ] Agent loop
* [ ] Tool result analysis
* [ ] Conversation memory

---

## v0.6 — Voice

* [ ] Microphone input
* [ ] Speech-to-text
* [ ] Text-to-speech
* [ ] Voice commands

---

## v0.7 — Vision

* [ ] Screenshot capture
* [ ] Vision model
* [ ] Screen analysis
* [ ] Error detection

---

## v0.8 — Desktop UI

* [ ] PySide6 UI
* [ ] Chat interface
* [ ] System dashboard
* [ ] Floating assistant

---

## v1.0 — EGE ASSISTANT

* [ ] Stable architecture
* [ ] Tool calling
* [ ] Voice
* [ ] Vision
* [ ] AI Agent
* [ ] Security confirmation system
* [ ] Modern UI
* [ ] Settings
* [ ] Logging
* [ ] Installer / executable

---

# 🔥 Immediate Next Step

İlk hedefimiz:

```text
v0.1 — COMPUTER CONTROL
```

İlk çalışan feature:

```text
🤖 EGE ASSISTANT

Sen:
> Chrome'u aç

Assistant:
> Chrome açılıyor...

[ Chrome gerçekten açılır ]
```

Buradan sonra adım adım sistemi büyüteceğiz.

---

# 🧠 Golden Rule

Bu projede amaç:

```text
Sadece çalışan kod ❌
```

değil.

Amaç:

```text
Çalışan kod
+
Ne yaptığını anlayabilmek
+
Gerektiğinde değiştirebilmek
+
Üzerine yeni özellik ekleyebilmek
```

---

## LET'S BUILD IT. 🚀

**İlk checkpoint:**

> Python ortamını hazırlayıp `Ege Assistant v0.1` projesini ayağa kaldırmak.
