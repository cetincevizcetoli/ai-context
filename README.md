# AI-Context v1.5.0

`ai-context`, bir proje klasörünü yapay zekâ modellerine verilebilecek tek bir Markdown bağlamına dönüştürür.

v1.5.0 artık yalnızca uzantı seçmez. Önce projenin **klasör haritasını** çıkarır, her bölüme uygun bir davranış önerir ve yalnızca gerekli dosyaların içeriğini okur.

## Temel fikir

Bir projenin yapısını bilmek ile bütün dosyalarını okumak aynı şey değildir.

Yeni sürüm her klasöre şu davranışlardan birini verir:

| Mod | Davranış |
|---|---|
| `İÇERİK` | Güvenli metin dosyalarının içeriğini rapora ekler |
| `KARMA` | Önemli kodları okur, diğer dosyaları yalnızca adlarıyla gösterir |
| `LİSTE` | Dosya adlarını ve klasör yapısını gösterir, içerik okumaz |
| `ÖZET` | Yalnızca klasörün varlığını ve kısa özetini gösterir |
| `SEÇİLİ` | Klasör içinden yalnızca kullanıcının seçtiği dosyaları okur |
| `GİZLE` | Bölümü raporda göstermez |

Örnek:

```text
assets/
├── css/
│   └── site.css [İÇERİK]
├── js/
│   └── app.js [İÇERİK]
└── img/
    └── hero.webp [BINARY - yalnızca dosya adı]

docs/
└── architecture.md [yalnızca dosya adı]

env/ [özet klasör; içerik taranmadı]
.env [HASSAS - varlığı gösterildi, içerik eklenmedi]
```

## v1.5.0 yenilikleri

- Uzantı merkezli ekran yerine klasör merkezli **Proje Haritası**.
- `.git`, `env`, `vendor`, `node_modules`, `uploads`, `_backups` gibi klasörlerin varlığını gösterip içlerine girmeyen hızlı özet taraması.
- `docs`, `.agents`, `tools` gibi klasörlerde tek tek önemli dosya seçebilme.
- `assets` gibi karma klasörlerde CSS/JS içeriğini okuyup görsel, video ve fontları yalnızca adlarıyla gösterme.
- Git ile hızlı dosya listesi ve ayrıca dosya sistemiyle hafif yapı keşfi.
- Marker dosyası olmasa da PHP, Python ve JavaScript ağırlıklı projeleri tanıma.
- Klasör başına haritada gösterilecek dosya adı sınırı.
- Hassas dosyanın içeriğini gizlerken varlığını proje haritasında gösterebilme.
- v1.4.0 ve v1.3.18 komutlarıyla geriye uyumluluk.

## Kurulum

Kaynak kod klasöründe:

```bash
python -m pip install -e .
```

GitHub üzerinden güncelleme:

```bash
python -m pip install --upgrade git+https://github.com/cetincevizcetoli/ai-context.git
```

Wheel dosyasını indirdiyseniz:

```bash
python -m pip install --upgrade ai_context-1.5.0-py3-none-any.whl
```

## En basit kullanım

Raporlamak istediğiniz proje klasöründe terminal açın:

```bash
ai-context -it
```

Program buna benzer bir plan gösterir:

```text
 No  Mod      Klasör / bölüm         Dosya      Boyut      İçerik       Rol
---  -------  --------------------  -------  ---------  ----------  -----------------------------
  1  KARMA    Kök dosyalar               12     44 KB       8.200  Proje giriş ve yapılandırma
  2  LİSTE    .agents/                    3      8 KB           0  Dosya adları görünür
  3  ÖZET     .git/                       0      0 B            0  Varlığı önemli
  4  İÇERİK   app/                       24    180 KB      46.000  Uygulamanın çalışan kodu
  5  KARMA    assets/                    59     14 MB      22.000  Kod + medya adları
  6  LİSTE    docs/                       6     31 KB           0  İçerik isteğe bağlı
  7  ÖZET     uploads/                   48     92 MB           0  İçerik taranmaz
```

Öneriyi kullanmak için yalnızca `Enter` tuşuna basın.

Bir klasörü değiştirmek için numarasını yazın. Örneğin `docs/` satırı 6 ise:

```text
Seçiminiz: 6
```

Ardından:

```text
1) İÇERİK
2) KARMA
3) LİSTE
4) ÖZET
5) SEÇİLİ
6) GİZLE
7) DOSYALAR
```

`5` seçildiğinde klasör içinden yalnızca gerekli dosyalar içerik olarak eklenebilir.

## Günlük kullanım

Akıllı harita ve pano:

```bash
ai-context -it -c
```

Token tahminiyle:

```bash
ai-context -it -c -tk
```

50.000 token bütçesiyle:

```bash
ai-context -it --budget 50000 -c
```

Yalnızca Git'te değişen veya yeni dosyalar:

```bash
ai-context -it --changed-only
```

Klasör başına bütün dosya adlarını göstermek için:

```bash
ai-context -it --map-limit 0
```

Varsayılan sınır klasör başına 120 dosya adıdır.

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

Bu dosyaların varlığı proje haritasında gösterilebilir, içerikleri eklenmez.

Tek bir hassas örnek dosyayı bilinçli olarak eklemek için:

```bash
ai-context -gf path/to/example.env
```

Etkileşimli seçimde hassas dosya seçimine izin vermek için:

```bash
ai-context -it --allow-sensitive
```

Gerçek anahtarları veya parolaları bir yapay zekâ servisine göndermeden önce mutlaka kontrol edin.

## Parametreler

### Geriye uyumlu seçenekler

| Komut | Açıklama |
|---|---|
| `-c`, `--clipboard` | Sonucu panoya kopyalar |
| `-tk`, `--tokens` | Tahmini token sayısını gösterir |
| `-to`, `--tree-only` | Yalnızca proje haritasını çıkarır |
| `-ms`, `--max-size KB` | Boyut sınırını aşan dosyaları atlar |
| `-i`, `--include-ext` | Ek uzantıları dahil eder |
| `-t`, `--target` | Belirli dosya veya yolları hedefler |
| `-u`, `--unsafe` | Bilinmeyen metin türlerini de dahil eder |
| `-xd`, `--exclude-dir` | Klasörleri hariç tutar |
| `-xf`, `--exclude-file` | Dosyaları hariç tutar |
| `-xe`, `--exclude-ext` | Uzantıları hariç tutar |
| `-git`, `--git-ignore` | Git görünür dosya listesini kullanır |
| `-gf`, `--git-force` | Belirtilen dosyayı zorla dahil eder |

### Akıllı proje haritası seçenekleri

| Komut | Açıklama |
|---|---|
| `-it`, `--interactive` | Klasör merkezli akıllı seçim ekranı |
| `--budget TOKEN` | Token bütçesi, `0` sınırsız |
| `--map-limit ADET` | Klasör başına gösterilecek azami dosya adı, `0` sınırsız |
| `--changed-only` | Yalnızca Git değişiklikleri |
| `--allow-sensitive` | Hassas dosyaların elle seçilebilmesine izin verir |
| `--no-auto-git` | Otomatik Git hızlandırmasını kapatır |
| `--output KLASÖR` | Çıktı klasörünü belirler |
| `--no-open` | Rapor klasörünü otomatik açmaz |
| `--version` | Sürümü gösterir |

## Mimari

```text
ai_context.py                 Eski kurulumlar için uyumluluk girişi
ai_context_core/
├── cli.py                    Komut satırı ve akış yönetimi
├── scanner.py                Git taraması + hafif proje yapısı keşfi
├── git_tools.py              Git hızlandırması ve değişen dosyalar
├── classifier.py             Proje, dosya ve güvenlik sınıflandırması
├── selection.py              Klasör modları, dosya seçimi ve token bütçesi
├── report.py                 Proje haritası ve Markdown raporu
├── clipboard.py              Platformlar arası pano desteği
├── config.py                 Güvenli varsayılanlar
├── models.py                 Veri modelleri
└── utils.py                  Yardımcı işlevler
```

## Test

```bash
python -m unittest discover -s tests -v
```

MIT License. Created by Ahmet Çetin.
