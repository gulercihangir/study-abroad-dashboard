# Patika — Proje Bağlamı (Claude Code için)

## Ürün nedir

**Patika**, yurt dışında lisans okumak isteyen öğrenciler (özellikle Türk öğrenciler) için bir
üniversite eşleştirme ve danışmanlık platformu. İki katmanlı hizmet sunuyor:

- **Öğrenci tarafı (ücretsiz):** 9 soruluk bir anket (bölüm, bütçe, bölge, öğrenme tarzı, kariyer
  hedefi, kampüs ortamı, öğrenci hayatı tercihi, öncelik kaydırıcıları, diploma türü) → gerçek
  üniversite/bölüm verisiyle ağırlıklı puanlama → en uygun 5 sonuç, her biri gerekçeli.
- **Danışmanlık tarafı (ücretli):** Öğrenci ilk 30 dakika ücretsiz bir danışman görüşmesi alıyor,
  isterse ücretli hizmete geçiyor. Danışmanlar ayrı bir panelden atanmış öğrencilerin profilini,
  checklist'ini, dökümanlarını ve mesajlarını yönetiyor.

**Konumlandırma:** "Kara kutu değil, şeffaf — her sonucun bir gerekçesi var." Bu, rakiplerden
(geleneksel danışmanlık firmaları, tahmin bazlı portallar) ayıran temel fark. Yeni özellik
eklerken (özellikle AI ile ilgili) bu şeffaflığı zedelememeye dikkat et.

## Kurucu

Güler Cihangir — TU/e (Eindhoven University of Technology), Endüstri Mühendisliği, son sınıf.
Eylül 2026'da Amsterdam'da bir Digital Transformation stajına başlıyor (yarı zamanlı bandwidth).
Solo founder, teknik ürünün tamamını tek başına inşa etti. Fikir, kendi danışmanlık deneyiminden
çıktı — tek bir danışmana bağımlı kalmak, Euro cinsinden yüksek ücretler.

## Teknoloji altyapısı

- **Backend:** Python + Flask, Flask-SQLAlchemy, Flask-Login (Student ve Consultant için
  polymorphic auth — `get_id()` sırasıyla `s-{id}` / `c-{id}` prefix'i ile ayrılıyor), Flask-Admin
  (Bootstrap4 darkly tema), Flask-Babel (TR/EN çoklu dil desteği)
- **Veritabanı:** Geliştirmede SQLite, canlıda **Neon** (kalıcı, ücretsiz PostgreSQL — Render'ın
  kendi ücretsiz Postgres'i 30 günde silindiği için Neon'a geçildi)
- **AI:** Google Gemini (`gemini-3.1-flash-lite`, ücretsiz katmanı olduğu için Claude yerine
  tercih edildi) — motivasyon mektubu değerlendirmesi ve (yeni eklenen) AI danışman sohbeti için
- **E-posta:** Resend (`onboarding@resend.dev` üzerinden) — henüz domain doğrulanmadığı için
  sadece Resend hesabına kayıtlı adrese gönderim yapabiliyor, gerçek öğrencilere şifre sıfırlama
  maili gitmiyor. `patika.online` domain'i satın alındı (Namecheap), Render'a bağlanıyor ama SSL
  sertifikası günlerdir "Pending" durumunda takıldı — çözülmedi, devam eden bir sorun.
- **Hosting:** Render (web servisi, Gunicorn), GitHub (`github.com/gulercihangir/study-abroad-dashboard`,
  push'ta otomatik deploy)
- **Diğer API:** WhereNext (getwherenext.com) — ücretsiz yaşam maliyeti verisi

## Veri modeli (özet)

`University` (artık `country` alanı var — çoklu ülke desteği), `Program`, `Student`, `Consultant`
(`is_admin` flag ile admin/normal danışman ayrımı var), `SavedAnswers`, `ChecklistItem`,
`ConsultationLead`, `Document` (LargeBinary, öğrenci döküman yükleme), `Message` (öğrenci↔danışman
mesajlaşma — bu tamamlanmış durumda, sadece plan değil).

## Puanlama motoru önemli detayı

`score_program()` içinde **Türkçe bölüm adı eşleştirmesi** var (`MAJOR_ALIASES` sözlüğü) —
öğrenciler bölümü Türkçe yazdığı için ("Bilgisayar Mühendisliği" gibi) bu olmadan hiçbir eşleşme
bulunamıyordu. Ayrıca kelime bazlı fallback eşleştirme (`_major_token_overlap_ratio`) var,
paraphrase'leri (örn. "Industrial Engineering" vs "Industrial Design Engineering") yakalamak için.

## Danışman ataması artık manuel değil

Önceki tasarımda öğrenci-danışman eşleştirmesi admin panelinden elle yapılıyordu. Şimdi
**"bekleyen öğrenci havuzu"** sistemi var: atanmamış öğrenciler tüm danışmanlara görünüyor,
herhangi biri "accept" ile atomik bir DB update'i ile üstlenebiliyor (iki danışmanın aynı anda
aynı öğrenciyi almasını önlüyor).

## Şu an üzerinde çalışılan özellik

**AI Danışman sohbeti** — öğrencinin sonuç sayfasında bir chat arayüzü. Önceki tasarımda
sadece ekrandaki sonuçlarla sınırlıydı (RAG mantığı, halüsinasyon riski olmadan); bilinçli bir
karar olarak bu kısıtlama kaldırıldı — artık genel amaçlı, serbest bir AI ajanı gibi davranıyor,
ekrandaki sonuçları bağlam olarak kullanıyor ama üniversite önerme/genel tavsiye vermekle
sınırlı değil. (Not: bu, önceki "kara kutu değil, şeffaf" konumlandırmasıyla gerilim yaratıyor —
kurucunun bilinçli tercihi.) Döküman kontrolü hâlâ bağlayıcı/kesin bir doğrulama olarak
sunulmuyor, mevcut motivasyon mektubu özelliğindeki gibi "genel, ilk bakış" çerçevesinde.

## Diğer bilinmesi gerekenler

- **Pitch deck** hazır (14 slayt, python-pptx ile üretildi), BIC Angels Investment'a (İstanbul
  merkezli, edtech/SaaS odaklı melek yatırımcı ağı) 500K-1M TL aralığında bir seed yatırım için
  hazırlanıyor.
- **CSV toplu içe/dışa aktarma** var artık (üniversite/program verisi için) — admin panelinden
  elle tek tek girmek yerine.
- **Blog + SEO sayfaları** eklendi (Türkçe içerik: Hollanda başvuru rehberi, numerus fixus
  açıklaması, yaşam maliyeti karşılaştırması), robots.txt, sitemap.xml, PWA service worker.
- Kod tabanı, bu konuşmada takip edilenden çok daha ileri durumda — muhtemelen ayrı Claude Code
  oturumlarında geliştirilmiş. Yeni bir değişiklik önerirken önce mevcut kodu oku, tahmin etme.
