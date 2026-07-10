# Değişiklik Günlüğü

## 1.4.0

- Mevcut v1.3.18 komutları korundu.
- Kod modüllere ayrıldı; eski `ai_context.py` uyumluluk girişi olarak bırakıldı.
- İçerik okumadan hızlı metadata taraması eklendi.
- Git depolarında `git ls-files -co --exclude-standard` tabanlı tarama eklendi.
- Python, Node.js, PHP/Composer, Rust, Go, Java, Ruby, Elixir, Flutter ve Docker proje tanıma eklendi.
- Uzantı, dosya sayısı, toplam boyut ve yaklaşık token gösteren interaktif seçim eklendi.
- Aynı uzantı grubunda yalnızca bazı dosyalar öneriliyorsa `[~]` kısmi seçim davranışı eklendi.
- Token bütçesi ve büyük dosyaları yalnızca isim olarak raporlama eklendi.
- `.env`, anahtar ve kimlik dosyaları için hassas içerik koruması eklendi.
- `--changed-only`, `--output`, `--no-open`, `--allow-sensitive` seçenekleri eklendi.
- Bilinmeyen argümanların sessizce yok sayılması kaldırıldı.
- İç içe Markdown kod blokları için dinamik çit uzunluğu eklendi.
- 15 otomatik test eklendi.
