# AI-Context v1.4.0

`ai-context`, bir proje klasörünü yapay zekâ modellerine verilebilecek tek bir Markdown bağlamına dönüştürür. v1.4.0 mevcut komutları korur ve üzerine hızlı Git taraması, proje türü tanıma, etkileşimli uzantı seçimi, hassas dosya koruması ve token bütçesi ekler.

## Neler yeni?

- **Tek keşif taraması:** İlk aşamada dosya içerikleri okunmaz. Yalnızca yol, uzantı, boyut ve sınıf bilgisi toplanır.
- **Git hızlandırması:** Interaktif mod bir Git deposunda `git ls-files -co --exclude-standard` kullanır.
- **Akıllı proje tanıma:** Python, Node.js, PHP/Composer, Rust, Go, Java, Docker ve başka proje işaretlerini tanır.
- **Etkileşimli seçim:** Bulunan uzantıları dosya sayısı, toplam boyut ve yaklaşık token ile gösterir.
- **Token bütçesi:** Bütçe aşılırsa en büyük dosyaları yalnızca isim olarak rapora koyabilir.
- **Hassas dosya kalkanı:** `.env`, özel anahtarlar ve kimlik dosyaları varsayılan olarak engellenir.
- **Geriye uyumluluk:** v1.3.18 seçenekleri korunur.

## Kurulum

```bash
pip install -e .
```

GitHub üzerinden güncelleme:

```bash
pip install --upgrade git+https://github.com/cetincevizcetoli/ai-context.git
```

## Hızlı kullanım

Eski kullanım aynen devam eder:

```bash
ai-context -c -tk
ai-context -git -c
ai-context -ms 500 -i cfg log
ai-context -t app.py templates/index.html
```

Yeni akıllı mod:

```bash
ai-context -it
```

50.000 token bütçesiyle:

```bash
ai-context -it --budget 50000 -c
```

Yalnızca Git'te değişen veya yeni dosyalar:

```bash
ai-context -it --changed-only
```

Belirli çıktı klasörü:

```bash
ai-context -it --output ./reports --no-open
```

## Interaktif ekran

Program uzantıları buna benzer gösterir:

```text
 No  Seç  Tür / uzantı             Dosya       Boyut       Token
---  ---  ----------------------  -------  ----------  ----------
  1  [x]  .py                          24    142.0 KB      36.352
  2  [x]  .html                         8     34.0 KB       8.704
  3  [~]  .json                        12      1.2 MB     314.000
  4  [ ]  .png (binary)                20      8.4 MB           0
  5  [!]  Hassas dosyalar               2      2.1 KB         530
```

Komutlar:

- `Enter`: önerilen dosyaları kullanır. `[~]` işaretli gruplarda yalnızca gerçekten önerilen dosyalar alınır.
- `all`: bütün güvenli grupları seçer.
- `1,3,5-7`: verilen grup numaralarını seçer.
- `list 3`: grubun dosyalarını gösterir.
- `q`: işlemi iptal eder.

## Güvenlik

Aşağıdaki türler varsayılan olarak içerikten çıkarılır:

```text
.env
.env.production
*.pem
*.key
*.p12
id_rsa
credentials.json
secrets.json
service-account.json
```

Tek bir hassas dosyayı bilinçli olarak eklemek için tam yolu zorlayabilirsiniz:

```bash
ai-context -gf path/to/example.env
```

Geniş izin:

```bash
ai-context -it --allow-sensitive
```

Bu seçenek gerçek sırları bir LLM'e göndermeden önce dikkatle kullanılmalıdır.

## Parametreler

### Mevcut seçenekler

| Komut | Açıklama |
|---|---|
| `-c`, `--clipboard` | Sonucu panoya kopyalar |
| `-tk`, `--tokens` | Tahmini token sayısını gösterir |
| `-to`, `--tree-only` | Yalnızca klasör ağacını çıkarır |
| `-ms`, `--max-size KB` | Boyut sınırını aşan dosyaları atlar |
| `-i`, `--include-ext` | Ek uzantıları dahil eder |
| `-t`, `--target` | Belirli dosya veya yolları hedefler |
| `-u`, `--unsafe` | Bilinmeyen metin türlerini de dahil eder |
| `-xd`, `--exclude-dir` | Klasörleri hariç tutar |
| `-xf`, `--exclude-file` | Dosyaları hariç tutar |
| `-xe`, `--exclude-ext` | Uzantıları hariç tutar |
| `-git`, `--git-ignore` | Git görünür dosya listesini kullanır |
| `-gf`, `--git-force` | Belirtilen dosyayı zorla dahil eder |

### v1.4 seçenekleri

| Komut | Açıklama |
|---|---|
| `-it`, `--interactive` | Akıllı keşif ve seçim ekranı |
| `--budget TOKEN` | Token bütçesi, `0` sınırsız |
| `--changed-only` | Yalnızca Git değişiklikleri |
| `--allow-sensitive` | Hassas dosya seçimine izin verir |
| `--no-auto-git` | Interaktif Git hızlandırmasını kapatır |
| `--output KLASÖR` | Çıktı klasörünü belirler |
| `--no-open` | Rapor klasörünü otomatik açmaz |
| `--version` | Sürümü gösterir |

## Mimari

```text
ai_context.py                 Eski kurulumlar için uyumluluk girişi
ai_context_core/
├── cli.py                    Komut satırı ve akış yönetimi
├── scanner.py                Tek geçişli hızlı dosya keşfi
├── git_tools.py              Git hızlandırması ve değişen dosyalar
├── classifier.py             Proje, dosya ve güvenlik sınıflandırması
├── selection.py              Interaktif seçim ve token bütçesi
├── report.py                 Markdown raporu
├── clipboard.py              Platformlar arası pano desteği
├── config.py                 Güvenli varsayılanlar
├── models.py                 Veri modelleri
└── utils.py                  Yardımcı işlevler
```

## Test

Standart kütüphane ile:

```bash
python -m unittest discover -s tests -v
```

MIT License. Created by Ahmet Çetin.
