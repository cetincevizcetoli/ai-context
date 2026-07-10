# Değişiklik Günlüğü

## 1.5.0

- Etkileşimli seçim uzantı merkezli yapıdan klasör merkezli **Proje Haritası** modeline geçirildi.
- `İÇERİK`, `KARMA`, `LİSTE`, `ÖZET`, `SEÇİLİ` ve `GİZLE` klasör davranışları eklendi.
- `.git`, `env`, `vendor`, `node_modules`, `uploads`, `_backups`, arşiv ve önbellek klasörlerinin varlığını gösteren fakat içlerine girmeyen hafif yapı taraması eklendi.
- Git taraması kullanıldığında `.gitignore` dışında kalan fiziksel klasörlerin varlığını da görebilen ikili tarama modeli eklendi.
- `docs`, `.agents`, `tools` gibi klasörlerden tek tek içerik dosyası seçme eklendi.
- `assets` ve benzeri karma klasörlerde kod içeriği ile binary dosya adları birlikte raporlanabilir hale getirildi.
- Hassas ve Git tarafından yok sayılan kök dosyalarının varlığı içerik okunmadan proje haritasına eklenir hale getirildi.
- Klasör başına dosya adı sınırı için `--map-limit` eklendi.
- Marker dosyası olmayan PHP, Python ve JavaScript/TypeScript projeleri için uzantı tabanlı proje tanıma eklendi.
- Rapor iki katmana ayrıldı: tam/kompakt proje haritası ve yalnızca seçilen dosya içerikleri.
- Eski uzantı gruplama yardımcıları geriye uyumluluk için korundu.
- Otomatik test sayısı 21'e çıkarıldı.

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
