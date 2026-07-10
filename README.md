# AI-Context v1.5.0

`ai-context`, bir proje klasörünü yapay zekâ modellerine verilebilecek tek bir Markdown bağlamına dönüştürür.

v1.5.0 iki ayrı kullanım biçimini birlikte korur:

1. **Klasik mod:** `-it` yazılmaz. Dosya ve uzantı kurallarına göre otomatik rapor üretir.
2. **Akıllı harita modu:** `-it` yazılır. Projenin klasör yapısını gösterir; hangi klasörlerin içeriğinin okunacağını seçtirir.

## Kurulum

Wheel dosyasını indirdiğiniz klasörde:

```bash
python -m pip install --upgrade ai_context-1.5.0-py3-none-any.whl
```

Kaynak kod üzerinden geliştirme kurulumu:

```bash
python -m pip install -e .
```

Sürüm kontrolü:

```bash
ai-context --version
```

## En basit kullanım

### Klasik otomatik kullanım

```bash
ai-context
```

`-it` kullanılmadığında eski dosya/uzantı tabanlı davranış devam eder.

### Akıllı klasör haritası

```bash
ai-context -it
```

Akıllı modda klasörler şu davranışlardan biriyle gösterilir:

- **İÇERİK:** Güvenli metin dosyalarının içeriği rapora eklenir.
- **KARMA:** Önemli kodlar okunur, diğer dosyalar yalnızca adlarıyla görünür.
- **LİSTE:** Dosya adları görünür, içerik okunmaz.
- **ÖZET:** Yalnızca klasörün varlığı ve kısa özeti gösterilir.
- **SEÇİLİ:** Klasör içinden belirli dosyalar seçilir.
- **GİZLE:** Klasör raporda gösterilmez.

## Akıllı mod ile içerik filtreleri

Klasör seçimi ile içerik filtresi farklı katmanlardır.

Örneğin bütün proje haritasını görmek, fakat hiçbir SQL dosyasının içeriğini okumamak için:

```bash
ai-context -it -xe sql
```

Rapor haritasında SQL dosyası görünür:

```text
app/
├── main.php [İÇERİK]
└── schema.sql [HARİÇ UZANTI (.sql) - varlığı gösterildi, içerik eklenmedi]
```

Birden fazla uzantıyı içerikten çıkarmak için:

```bash
ai-context -it -xe sql json log
```

Belirli bir dosyanın adını haritada tutup içeriğini almamak için:

```bash
ai-context -it -xf app/debug.php
```

Klasörü **İÇERİK** yapsanız bile `-xe` ve `-xf` filtreleri geçerliliğini korur.

Genel olarak SQL içeriğini kapatıp yalnızca tek bir SQL dosyasını istisna olarak almak için mevcut `-gf` seçeneği kullanılabilir:

```bash
ai-context -it -xe sql -gf config/schema.sql
```

Bu durumda `config/schema.sql` okunur, diğer SQL dosyaları yalnızca haritada görünür.

## Klasik mod ile filtrelerin farkı

`-it` olmadan:

```bash
ai-context -xe sql
```

SQL dosyaları klasik rapora hiç alınmaz. Bu, eski davranıştır.

`-it` ile:

```bash
ai-context -it -xe sql
```

SQL dosyalarının varlığı proje haritasında korunur, içerikleri okunmaz.

## Günlük kullanım örnekleri

Akıllı seçim, token bilgisi ve pano:

```bash
ai-context -it -c -tk
```

SQL ve günlük dosyalarının içeriğini almadan:

```bash
ai-context -it -xe sql log -c
```

Bir klasörü özet olarak tutmak:

```bash
ai-context -it -xd uploads env
```

Yalnızca Git'te değişen veya yeni dosyalar:

```bash
ai-context -it --changed-only
```

50.000 token bütçesi:

```bash
ai-context -it --budget 50000
```

Belirli çıktı klasörü:

```bash
ai-context -it --output ./reports --no-open
```

## Güvenlik

Aşağıdaki türlerin içerikleri varsayılan olarak korunur:

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

Hassas bir dosyanın varlığı haritada gösterilebilir, fakat içeriği varsayılan olarak okunmaz.

Bilinçli olarak belirli bir dosyayı zorlamak için:

```bash
ai-context -it -gf path/to/example.env
```

Geniş izin:

```bash
ai-context -it --allow-sensitive
```

Gerçek sırları bir yapay zekâ modeline göndermeden önce dikkatle kontrol edin.

## Parametreler

| Komut | Açıklama |
|---|---|
| `-c`, `--clipboard` | Sonucu panoya kopyalar |
| `-tk`, `--tokens` | Tahmini token sayısını gösterir |
| `-to`, `--tree-only` | Yalnızca proje ağacını çıkarır |
| `-ms`, `--max-size KB` | Boyut sınırını aşan dosyaları atlar |
| `-i`, `--include-ext` | Klasik moda ek uzantılar dahil eder |
| `-t`, `--target` | Belirli dosya veya yolları hedefler |
| `-u`, `--unsafe` | Klasik modda bilinmeyen metin türlerini de alır |
| `-xd`, `--exclude-dir` | Klasörü atlar; akıllı haritada özet olarak gösterebilir |
| `-xf`, `--exclude-file` | Dosyayı hariç tutar; `-it` modunda adı kalır, içeriği okunmaz |
| `-xe`, `--exclude-ext` | Uzantıyı hariç tutar; `-it` modunda adı kalır, içeriği okunmaz |
| `-git`, `--git-ignore` | Git görünür dosya listesini kullanır |
| `-gf`, `--git-force` | Belirtilen dosyayı filtrelere rağmen zorla dahil eder |
| `-it`, `--interactive` | Klasör merkezli akıllı proje haritası |
| `--budget TOKEN` | Token bütçesi; `0` sınırsız |
| `--changed-only` | Yalnızca Git değişikliklerini alır |
| `--allow-sensitive` | Hassas dosya seçimine izin verir |
| `--no-auto-git` | Akıllı modda otomatik Git taramasını kapatır |
| `--map-limit ADET` | Klasör başına haritada gösterilecek dosya adı sınırı |
| `--output KLASÖR` | Çıktı klasörünü belirler |
| `--no-open` | Rapor klasörünü otomatik açmaz |
| `--version` | Sürümü gösterir |

## Mimari

```text
ai_context.py                 Eski kurulumlar için uyumluluk girişi
ai_context_core/
├── cli.py                    Komut satırı ve çalışma akışı
├── scanner.py                Git/dosya sistemi taraması
├── git_tools.py              Git hızlandırması
├── classifier.py             Proje ve dosya sınıflandırması
├── selection.py              Klasör seçimi, içerik filtreleri ve token bütçesi
├── report.py                 Markdown proje haritası ve içerikler
├── clipboard.py              Pano desteği
├── config.py                 Varsayılan kurallar
├── models.py                 Veri modelleri
└── utils.py                  Yardımcı işlevler
```

## Test

```bash
python -m unittest discover -s tests -v
```

Mevcut paket 26 otomatik test içerir.

MIT License. Created by Ahmet Çetin.
