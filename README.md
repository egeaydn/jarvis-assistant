# 🤖 JARVIS — Autonomous Voice & Vision Desktop Assistant

JARVIS (Just A Rather Very Intelligent System), Windows bilgisayarınızı ses, ekran görüntüsü ve terminal komutları aracılığıyla tamamen kontrol edebilmenizi sağlayan otonom ve modern bir yapay zekâ asistanıdır. 

Tony Stark'ın efsanevi asistanından ilham alan **holografik neon mavi HUD arayüzü**, arka planda kesintisiz çalışan **"Hey Jarvis" uyanma kelimesi (wake-word) motoru** ve çok adımlı ReAct planlama yeteneğiyle asistanlığın sınırlarını yeniden tanımlar.

---

## 🚀 Öne Çıkan Özellikler

### 1. 🎙️ Sesli Uyanma ve Akıllı Konuşma (Wake-Word & TTS)
- **Düşük Gecikmeli Wake-Word**: Arka planda `"Hey Jarvis"` veya `"Jarvis"` dediğiniz anda asistanınız uyanır. En yüksek hassasiyet için İngilizce ve Türkçe paralel ses analiz motoru barındırır.
- **Tony Stark Tarzı Seslendirme**: Uyanma anında rastgele seçilen İngilizce sesli yanıtlar verir (*"At your service, sir.", "Yes, sir?"* vb.).
- **Akıllı Ses Sınırlayıcı (Smart TTS)**: Kısa yanıtları sesli okurken, uzun raporları veya komut çıktılarını sesli olarak özet geçerek ekrana yansıtır.

### 2. 👁️ Ekran Analizi (Screen Vision)
- **Yüksek Hızlı Ekran Yakalama**: `mss` entegrasyonu sayesinde PyAutoGUI'ye kıyasla 3 kat daha hızlı ekran görüntüsü yakalar.
- **Gemini 3.6 Flash Entegrasyonu**: Ekranda ne olduğunu analiz edebilir, terminaldeki kod hatalarını okuyabilir, web sitelerindeki arayüzleri yorumlayabilir.

### 3. 🧠 Otonom ReAct Ajan Döngüsü (AI Agent)
- **Çok Adımlı Planlama**: Tek bir komutla sırasıyla klasörleri arayabilir, dosyaları filtreleyebilir ve doğru aracı seçip çalıştırabilir.
- **Terminal Komut Çalıştırma**: Projelerinizi test etmek, bağımlılık yüklemek veya kod çalıştırmak için terminal komutlarını (`PowerShell`) otonom yürütebilir.
- **Akıllı Klasör Düzenleme**: Klasörlerdeki tüm dosyaları analiz ederek uzantılarına göre alt klasörlere (`Belgeler`, `Resimler`, `Arşivler` vb.) otomatik taşır.

### 4. 🖥️ Bilim Kurgu HUD Arayüzü (PySide6)
- **Dönen Arc Reactor**: Yan panelde sürekli hareket eden ve nabız gibi atan holografik Arc Reactor dijital animasyonu.
- **Neon Mavi Tema**: Koyu antrasit ve neon mavi çizgiler içeren tamamen emojilerden arındırılmış ciddi ve şık arayüz tasarımı.
- **Sistem Tepsisi (Tray Icon)**: Kapat butonuna basıldığında arka plana (tepsiye) küçülür. Çift tıklama ile anında ekrana gelir.
- **Canlı Sistem Bilgisi**: CPU, RAM, Disk kullanımı ve aktif proses sayısını saniyelik güncelleyen göstergeler.

---

## 🛠️ Kurulum Adımları

### 1. Gereksinimler
Projenin çalışması için bilgisayarınızda **Python 3.10+** kurulu olmalıdır.

### 2. Bağımlılıkları Yükleme
Proje klasörünü açın ve bir sanal ortam oluşturup paketleri kurun:
```bash
# Sanal ortam oluşturma
python -m venv .venv

# Sanal ortamı aktif etme (Windows)
.venv\Scripts\activate

# Gerekli paketlerin yüklenmesi
pip install -r requirements.txt
```

### 3. API Anahtarlarını Tanımlama
Kök dizinde `.env` adında bir dosya oluşturun ve API anahtarlarınızı girin:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

---

## 💻 Kullanım Kılavuzu

### Uygulamayı Çalıştırma
```bash
# Grafik Arayüzü (GUI) Başlatma (Önerilen)
python main.py

# Sadece Sesli CLI Modu
python main.py --voice

# Sadece Yazılı CLI Modu
python main.py --text
```

### Tek Tıkla `.exe` Dosyası Oluşturma (PyInstaller)
Herhangi bir terminal açmadan doğrudan çift tıklayıp çalıştırabileceğiniz bir masaüstü uygulaması derlemek için:
```bash
python build_exe.py
```
Derleme bittiğinde, bağımsız çalışan **`Jarvis.exe`** dosyasını **`dist/`** klasörünün altında bulabilirsiniz.

---

## 🔒 Güvenlik Sistemi (Safety Confirmations)
Jarvis bilgisayarınızda kritik değişiklikler yapmadan önce onay ister.
- Dosya Silme (`delete_file`)
- Dosya Taşıma (`move_file`)
- Terminal Komutu Çalıştırma (`run_terminal_command`)
- Klasör Düzenleme (`organize_folder`)

Bu işlemler tetiklendiğinde arayüzde modern bir **Güvenlik Onayı** penceresi açılır. Siz onay vermediğiniz sürece hiçbir dosya silinmez veya komut yürütülmez.
