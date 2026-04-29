# 🤖 AI-Context (v1.3.0)

**TR:** `ai-context`, yerel kaynak kodlarınızı Yapay Zeka (LLM) modellerine (Claude, ChatGPT, Gemini vb.) aktarmak için optimize edilmiş profesyonel bir "bağlam döküm" (context dumper) aracıdır. Tüm projenizi veya seçtiğiniz dosyaları tek bir Markdown dosyasına dönüştürür, panoya kopyalar ve token sayısını hesaplar. Raporlar, yetki hatalarını önlemek için otomatik olarak Masaüstü'ndeki `ai-reports` klasörüne kaydedilir.

**EN:** `ai-context` is a professional context dumping tool optimized for providing your codebase to LLMs (Claude, ChatGPT, Gemini, etc.). It converts your entire project or specific files into a single, clean Markdown file, copies it to the clipboard, and estimates token counts. Reports are automatically saved to the `ai-reports` folder on your Desktop to avoid permission issues.

---

## 🚀 Özellikler / Features

- **📏 Dinamik Boyut Filtresi / Dynamic Size Filter:** `-ms` parametresi ile belirlediğiniz KB'dan büyük dosyaları otomatik olarak atlayabilirsiniz. / Skip files larger than specified KB using `-ms`.
- **📂 Masaüstü Çıktısı / Desktop Output:** Raporlar artık her zaman Masaüstü'ne kaydedilir, böylece Program Files gibi klasörlerde yetki hatası almazsınız.
- **➕ Dinamik Dahil Etme / Dynamic Include:** `-i` parametresi ile listede olmayan özel uzantıları (.log, .cfg vb.) anlık olarak sürece dahil edebilirsiniz.
- **📂 Tree-Only Modu:** Projenin sadece klasör ağacını döküm alır (İçerik okumaz). / Dumps only folder structure (No content).
- **🧠 Gitignore Entegrasyonu / Gitignore Support:** `-git` parametresi ile `.gitignore` kurallarını otomatik tanır ve uygular. Engellenmiş dosyaları `-gf` ile zorla dahil edebilirsiniz.
- **🛡️ Binary Shield:** Resim, video, PDF ve derlenmiş dosyaları otomatik ayıklar.
- **📋 Instant Copy:** Tek tıkla tüm dökümü panoya (clipboard) kopyalar.
- **📊 Token Counter:** Çıktının tahmini Token maliyetini anlık hesaplar.

---

## 🛠 Kurulum / Installation

### 1. Diğer Kullanıcılar İçin (Normal Kurulum / Upgrade)
GitHub üzerinden doğrudan en güncel sürümü yüklemek veya güncellemek için:
```bash
pip install --upgrade git+[https://github.com/cetincevizcetoli/ai-context.git](https://github.com/cetincevizcetoli/ai-context.git)
```

### 2. Geliştirici Modunda Yükleme (Önerilen / Recommended)
Klasörün içine girin ve terminalde şu komutu çalıştırın. Bu sayede kodda yaptığınız değişiklikler anında komut satırına yansır:
```bash
pip install -e .
```

---

## 📖 Kullanım Örnekleri / Usage Examples

> **Önemli / Important:** Kısa parametreler tek tire (-), uzun parametreler çift tire (--) ile kullanılmaktadır.
> Short arguments use a single dash (-), long arguments use a double dash (--).

**TR: .gitignore kurallarını uygula ve panoya kopyala:**
**EN: Apply .gitignore rules and copy:**
`ai-context -git -c`

**TR: Gitignore açıkken .env dosyasını zorla dahil et:**
**EN: Force include .env file while using gitignore:**
`ai-context -git -gf .env -c`

**TR: 500 KB'dan büyük dosyaları atla ve kopyala:**
**EN: Skip files larger than 500 KB and copy:**
`ai-context -ms 500 -c`

**TR: Özel uzantıları (log, cfg) sürece dahil et:**
**EN: Include extra extensions (log, cfg):**
`ai-context -i log cfg -c`

**TR: Belirli bir dosyayı hedefle ve kopyala:**
**EN: Target a specific file and copy:**
`ai-context -t main.py -c`

**TR: Sadece klasör yapısını al ve panoya kopyala:**
**EN: Get folder structure only and copy to clipboard:**
`ai-context -to -c`

---

## ⚙️ Parametreler / Arguments

| Komut / Cmd | Açıklama (TR) | Description (EN) |
| :--- | :--- | :--- |
| -ms / --max-size | Maksimum dosya boyutu (KB) | Max file size filter (KB) |
| -i / --include-ext | Özel uzantı ekle | Include extra extensions |
| -to / --tree-only | Sadece klasör yapısını dök | Tree-only mode (structure only) |
| -git / --git-ignore | .gitignore kurallarını uygula | Apply .gitignore rules |
| -gf / --git-force | Git yoksaysa bile zorla ekle | Force include if git ignored |
| -c / --clipboard | Panoya kopyala | Copy to clipboard |
| -tk / --tokens | Token sayısını göster | Show estimated token count |
| -t / --target | Sadece belirli dosyaları tara | Target specific files only |
| -xd / --exclude-dir| Klasörleri hariç tut | Exclude directories |
| -xf / --exclude-file| Dosyaları hariç tut | Exclude files |
| -xe / --exclude-ext| Uzantıları hariç tut | Exclude extensions |
| -u / --unsafe | Tüm dosya tiplerini oku | Unsafe mode (Read all extensions) |
| -h / --help | Yardım menüsünü göster | Show help menu |

---

## ⚖️ Lisans / License
MIT License. Created by Ahmet Çetin.
