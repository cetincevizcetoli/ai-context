# 🤖 AI-Context (v11.6)

**TR:** `ai-context`, yerel kaynak kodlarınızı Yapay Zeka (LLM) modellerine (Claude, ChatGPT, Gemini vb.) aktarmak için optimize edilmiş profesyonel bir "bağlam döküm" (context dumper) aracıdır. Tüm projenizi veya seçtiğiniz dosyaları tek bir Markdown dosyasına dönüştürür, panoya kopyalar ve token sayısını hesaplar.

**EN:** `ai-context` is a professional context dumping tool optimized for providing your codebase to LLMs (Claude, ChatGPT, Gemini, etc.). It converts your entire project or specific files into a single, clean Markdown file, copies it to the clipboard, and estimates token counts.

---

## 🚀 Özellikler / Features

- **📂 Tree-Only Modu:** Projenin sadece klasör ağacını döküm alır (İçerik okumaz). / Dumps only folder structure (No content).
- **🧠 Smart Filter:** `.gitignore` kurallarını otomatik tanır ve uygular.
- **🛡️ Binary Shield:** Resim, video, PDF ve derlenmiş dosyaları otomatik ayıklar.
- **📋 Instant Copy:** Tek tıkla tüm dökümü panoya (clipboard) kopyalar.
- **📊 Token Counter:** Çıktının tahmini Token maliyetini anlık hesaplar.

---

## 🛠 Kurulum / Installation

### 1. Pip ile Yükleme (Önerilen / Recommended)
Klasörün içine girin ve terminalde şu komutu çalıştırın:
pip install .

### 2. Manuel Kullanım / Manual Usage
python ai_context.py . -c -tk

---

## 📖 Kullanım Örnekleri / Usage Examples

> **Önemli / Important:** Tüm parametreler tek tire (-) ile kullanılmaktadır.
> All parameters are used with a single dash (-).

**TR: Sadece klasör yapısını al ve panoya kopyala:**
**EN: Get folder structure only and copy to clipboard:**
ai-context -to -c

**TR: Tüm projeyi tara, token sayısını göster ve kopyala:**
**EN: Scan project, show tokens, and copy:**
ai-context . -c -tk

**TR: Belirli klasörleri tarama dışı bırak:**
**EN: Exclude specific directories:**
ai-context -xd vendor node_modules tmp -c

---

## ⚙️ Parametreler / Arguments

| Komut / Cmd | Açıklama (TR) | Description (EN) |
| :--- | :--- | :--- |
| -to | Sadece klasör yapısını dök | Tree-only mode (structure only) |
| -c | Panoya kopyala | Copy to clipboard |
| -tk | Token sayısını göster | Show estimated token count |
| -t | Sadece belirli dosyaları tara | Target specific files only |
| -xd | Klasörleri hariç tut | Exclude directories |
| -xf | Dosyaları hariç tut | Exclude files |
| -xe | Uzantıları hariç tut | Exclude extensions |
| -u | Tüm dosya tiplerini oku | Unsafe mode (Read all extensions) |
| -h | Yardım menüsünü göster | Show help menu |

---

## 🚀 Git Güncelleme / Git Update

git add ai-context.py README.md
git commit -m "Update: v11.6 - Tree-only mode and single-dash argument support"
git push origin main

---

## ⚖️ Lisans / License
MIT License. Created by [Ahmet Çetin].