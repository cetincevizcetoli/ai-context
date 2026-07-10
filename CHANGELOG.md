# Değişiklik Günlüğü

## 1.5.0

- Klasör merkezli proje haritası eklendi.
- Klasörler için İÇERİK, KARMA, LİSTE, ÖZET, SEÇİLİ ve GİZLE davranışları eklendi.
- `assets/` içindeki kod ve medya dosyaları ayrıştırıldı.
- `docs/`, `.agents/` ve benzeri klasörlerden tek tek dosya seçimi eklendi.
- `.git/`, `env/`, `uploads/`, yedek ve çalışma klasörleri içlerine girilmeden özetlenir hale getirildi.
- Seçilmeyen dosyaların proje haritasında yalnızca adlarıyla gösterilmesi eklendi.
- `-it -xe sql` davranışı düzeltildi: SQL dosyaları haritada kalır, içerikleri okunmaz.
- `-it -xf DOSYA` davranışı düzeltildi: dosya adı haritada kalır, içeriği okunmaz.
- Klasör İÇERİK olarak seçilse bile `-xe` ve `-xf` içerik filtrelerinin geçerliliğini koruması sağlandı.
- `-gf yol/dosya` ile genel uzantı veya dosya filtresine tek dosyalık istisna eklenmesi sağlandı.
- `-it` kullanılmadığında eski dosya/uzantı tabanlı davranış korundu.
- Token bütçesi, hassas dosya koruması ve Git hızlandırması korundu.
- Otomatik test sayısı 26'ya çıkarıldı.

## 1.4.0

- Kod modüllere ayrıldı; `ai_context.py` uyumluluk girişi olarak bırakıldı.
- Hızlı metadata ve Git taraması eklendi.
- Proje türü tanıma, token bütçesi ve hassas dosya koruması eklendi.
