# SPESIFIKASI SISTEM & DOKUMENTASI TEKNIS (SYSTEM SPECIFICATION)
## Project: Django ITS (Media Track & Operations Management System)

---

## 1. Ringkasan Eksekutif & Tujuan Sistem

**Django ITS** (dikenal juga sebagai *Media Track & Request Management System*) adalah aplikasi manajemen operasional berbasis web yang dirancang khusus untuk industri periklanan luar ruang (Out-of-Home / OOH) dan Digital Signage / LED Videotron (MING Media & Promosi).

Sistem ini memfasilitasi dan mengotomatisasi siklus hidup:
1. **Documentation Request**: Permintaan pemotretan dan dokumentasi materi iklan di lokasi-lokasi billboard/videotron oleh tim lapangan.
2. **Maintenance & Troubleshoot LED**: *Ticketing system* untuk perbaikan fisik, troubleshooting modul videotron, inventaris perangkat keras, dan pelaporan kerusakan.
3. **Jadwal Tayang (Airing & Takeout Management)**: Penjadwalan materi tayang, verifikasi playlist (pagi, siang, malam), bukti foto tayang aktif, dan proses *takeout* (penurunan materi) saat masa kontrak habis.
4. **Takeout Alert & Notification Engine**: Mesin peringatan otomatis (*real-time alerting*) berbasis aturan dinamis (H-1, Jam-6, Overdue) untuk mencegah denda atau penayangan materi lewat batas kontrak.
5. **Master Data Registry & User Management**: Pengelolaan data referensi (Brand, Lokasi, LED Type, dsb.) dengan fitur import/preview/export Excel, serta audit pengguna (*Never Login* & Role-based authentication).

---

## 2. Arsitektur Sistem & Spesifikasi Teknologi

### 2.1 Technology Stack
| Komponen | Teknologi | Versi | Keterangan |
|---|---|---|---|
| **Framework Backend** | Django | `4.2.29` (LTS) | Dipilih untuk stabilitas dan kompatibilitas penuh dengan server basis data PostgreSQL 12. |
| **Bahasa Pemrograman** | Python | `3.10+` | Dijalankan di dalam isolasi virtual environment (`.venv`). |
| **Database (Dev/Local)** | SQLite 3 | `3.x` | `db.sqlite3` untuk *rapid prototyping* tanpa dependensi eksternal. |
| **Database (Staging/Prod)** | PostgreSQL | `12+` / `14+` | `psycopg2-binary==2.9.11` via `DATABASE_URL` atau konfigurasi `.env`. |
| **Authentication Engine** | Django Auth + Custom Backend | - | `backends.EmailBackend` (login menggunakan email sebagai identifier utama). |
| **Password Hashing** | BCrypt + PBKDF2 | `bcrypt==4.3.0` | Mendukung verifikasi migrasi legacy Laravel (`$2y$12$...`) dan hash native Django. |
| **Spreadsheet Engine** | openpyxl | `3.1.5` | Digunakan untuk ekspor master data ke `.xlsx` dan import preview dengan validasi deduplikasi. |
| **Media & Image Processing**| Pillow | `12.1.1` | Validasi ukuran file (maks. 10MB) dan penyimpanan bukti fisik foto. |
| **UI Framework & Layout** | AdminLTE 4 + Bootstrap 5 | `4.x` / `5.3.3` | Tema responsif bernuansa dark mode (`data-bs-theme="dark"`). |
| **Komponen UI Tambahan** | Select2 + OverlayScrollbars | `4.1` / `2.11` | Komponen autocomplete dropdown tag dinamis dan *smooth custom scrollbar*. |

### 2.2 Struktur File & Direktori Workspace
```
d:\code\django_its\djangtest\
├── .env / .env.example       # Konfigurasi environment (DB, SECRET_KEY, DEBUG, HOSTS)
├── dev.ps1                   # Automation helper PowerShell untuk dev lokal (runserver, migrate, seed)
├── manage.py                 # Django entrypoint script
├── requirements.txt          # Dependensi Python terkunci
├── notes.txt                 # Catatan operasional server, akun default, instruksi Gunicorn
├── backends.py               # Custom Auth Backend: login via email
├── seed_fresh_install.py     # Data seeder untuk instalasi baru (master data, rules, users)
├── migrate_data.py           # Pipeline migrasi data dari SQLite lama ke PostgreSQL
│
├── mysite/                   # Core Project Configuration
│   ├── settings.py           # Pengaturan konfigurasi, env parsing, hashers, database fallback
│   ├── urls.py               # Routing utama & static/media file serving
│   ├── wsgi.py / asgi.py     # Gateway interface untuk deployment
│
├── products/                 # Modul Utama Aplikasi
│   ├── models.py             # Domain models (Requests, Jadwal, Rules, Audit, Master Data)
│   ├── views.py              # Controller logic, permissions, filters, excel handlers
│   ├── urls.py               # Endpoint routing aplikasi
│   ├── forms.py              # Form validasi, widgets, custom validation (file size)
│   ├── notifications.py      # Rule evaluation engine untuk alert takeout
│   ├── tests.py              # Suite uji komprehensif (RBAC, Multi-lokasi, Alert, Status)
│   └── templates/            # Template HTML (AdminLTE 4)
│       ├── layouts/          # base.html, header.html, sidebar.html
│       └── products/         # Views spesifik per fitur dan partial modals AJAX
│
├── static/ & staticfiles/    # Asset statis frontend (AdminLTE dist, fonts, icons)
└── media/                    # Direktori upload file bukti kerja, foto kerusakan, materi
```

---

## 3. Autentikasi, Otorisasi & Role-Based Access Control (RBAC)

### 3.1 Mekanisme Login & Password Hashing
* **Identifier**: Pengguna login menggunakan alamat email resmi (misal: `ming@ming.com` atau `user@ming.com`).
* **Backend**: `backends.EmailBackend` melakukan pencarian *case-insensitive* (`email__iexact=username`).
* **Multi-Hasher Compatibility**:
  1. `django.contrib.auth.hashers.BCryptPasswordHasher`: Memungkinkan user hasil migrasi dari sistem Laravel (hash format `$2y$`) login langsung tanpa perlu reset password.
  2. `django.contrib.auth.hashers.PBKDF2PasswordHasher`: Digunakan untuk user baru yang didaftarkan melalui form manajemen user Django.

### 3.2 Matriks Hak Akses Peran (Roles Matrix)

Sistem membagi pengguna ke dalam 4 kelompok (`django.contrib.auth.models.Group`):

| Fitur / Tindakan | Admin (`admin` / Superuser) | Staff (`staff`) | Requester (`requester`) | Executor (`executor`) |
|---|:---:|:---:|:---:|:---:|
| **Dashboard Metrik Global** | Full | Full | Scoped | Scoped |
| **Submit Documentation Request** | Ya | Tidak | Ya | Tidak |
| **Submit Maintenance Request** | Ya | Tidak | Ya | Tidak |
| **Submit Jadwal Tayang** | Ya | Tidak | Ya | Tidak |
| **Lihat Semua Request (Global)** | Ya | Ya | Hanya Milik Sendiri | Hanya Tugas Sendiri |
| **Filter Selesai / Belum (Toggle Done)** | - | - | - | Ya (`show_done=1`) |
| **Edit Data Request** | Ya | Ya | Hanya Milik Sendiri | Tidak |
| **Hapus Request** | Ya | Ya | Ya (Milik Sendiri) | Tidak |
| **Assign Pelaksana (Dokumentator)** | Ya | Ya | Tidak | Tidak |
| **Upload Bukti Foto Selesai** | Ya | Ya | Tidak | Ya |
| **Manajemen Master Data (CRUD)** | Ya | Tidak | Tidak | Tidak |
| **Import / Export Excel Master Data** | Ya | Tidak | Tidak | Tidak |
| **Manajemen Aturan Notifikasi (Rules)** | Ya | Tidak | Tidak | Tidak |
| **Manajemen Akun User & Hak Login** | Ya | Tidak | Tidak | Tidak |

### 3.3 Penanganan Khusus User: `UserLoginRequirement`
* Relasi `OneToOne` ke model `User` (`requires_login: bool`).
* **Tujuan Bisnis**: Banyak akun user dibuat hanya untuk keperluan penugasan operasional di lapangan (*Dokumentator*) atau data historis dan tidak memerlukan akun login aktif.
* Akun dengan `requires_login=False` otomatis disaring dari daftar audit **User Belum Pernah Login** (`/users/never-login/`), menjaga kebersihan laporan audit kepatuhan IT.

---

## 4. Model Data & Skema Database (Data Models)

```
                    ┌────────────────────────┐
                    │      BrandMateri       │
                    └───────────┬────────────┘
                                │ 1:N
┌───────────────────┐    ┌──────┴───────────────┐    ┌───────────────────┐
│      Lokasi       │◄───┤ DocumentationRequest ├───►│      LEDType      │
└─────────┬─────────┘M:N └──────┬───────────────┘N:1 └───────────────────┘
          │                     │
          │                     ├───────────────┐ 1:N
          │ 1:N                 │ 1:N           ▼
          ▼                     ▼     ┌──────────────────────┐
┌─────────────────────────┐   ┌───────┴──────┐  │ DocumentationRequest │
│  DocRequestLokasiAssign │   │  DocRequest  │  │        Materi        │
│   (Perintah Kerja)      │   │    Materi    │  └──────────────────────┘
└─────────┬───────────────┘   └──────────────┘
          │ M:N
          ▼
┌───────────────────┐
│   Dokumentator    │
└───────────────────┘
```

### 4.1 Master Data Referensi
1. **`BrandMateri`**: Daftar merek pengiklan (contoh: Samsung, Shopee, BCA).
2. **`Lokasi`**: Titik lokasi fisik videotron/billboard (contoh: WTC Serpong, Kuningan City, Beos).
3. **`LEDType`**: Jenis produk / display (contoh: Mobile LED, LED Statis, Videotron, Billboard).
4. **`cameratype`**: Standar perangkat dokumentasi (iPhone, Android, Kamera DSLR).
5. **`Requirement`**: Kriteria hasil pemotretan (HIGHRESS, SIANG, MALAM, TIMESTAMP).
6. **`ViewPhoto`**: Sudut pandang kamera (PORTRAIT, LANDSCAPE, JARAK DEKAT, JARAK JAUH).
7. **`Dokumentator`**: Nama teknisi / fotografer pelaksana tugas.
8. **`InventoryItem`**: Katalog perangkat keras per grup (`MING`, `MOBILE_LED`, `MST`, `LUMINOVA`).

### 4.2 Documentation Request & Multi-Lokasi
* **`DocumentationRequest`**:
  * Menampung permintaan dokumentasi dari requester.
  * Fields: `submitted_by`, `brand`, `lokasi` (M2M), `jenis_led`, `tanggal`, `requirements` (M2M), `view_photo` (M2M), `jenis_kamera` (M2M), `note`, `pic_pemohon`, `foto_bukti_kerja`, `status` (`TODO`, `IN_PROGRESS`, `DONE`).
* **`DocumentationRequestMateri`**:
  * Mendukung penugasan multi-materi iklan dalam satu request.
  * Fields: `nama_materi`, `foto_bukti_kerja`, `sort_order`.
* **`DocumentationRequestLokasiAssignment`**:
  * Otomatis tersinkronisasi via Django Signal `m2m_changed` pada field `lokasi`.
  * Setiap lokasi yang dipilih memiliki penugasan mandiri:
    * `lokasi`: FK ke `Lokasi`.
    * `pelaksana`: M2M ke `Dokumentator` (dapat ditugaskan dokumentator berbeda per lokasi).
    * `perintah_kerja`: Catatan instruksi khusus spesifik untuk lokasi tersebut.

### 4.3 Maintenance & Troubleshoot Request
* **`MaintenanceRequest`**:
  * Tiket kerusakan hardware / display LED.
  * Fields: `nama_pemohon`, `departement`, `tanggal_permintaan`, `tanggal_deadline`, `brand`, `lokasi` (M2M), `jenis_led` (M2M), `inventory_items` (M2M), `deskripsi_pekerjaan`, `foto_kerusakan`, `foto_bukti_kerja`, `pelaksana` (M2M), `status` (`TODO`, `IN_PROGRESS`, `DONE`).
* **`MaintenanceRequestMateri`**:
  * Rincian komponen/materi yang dikerjakan beserta bukti hasil kerja per item.

### 4.4 Jadwal Tayang (Media Airing & Takeout)
* **`JadwalTayang`**:
  * Entitas jadwal penayangan iklan di layar digital.
  * Fields: `brand`, `lokasi` (M2M), `jenis_led`, `tanggal_tayang` (datetime), `tanggal_takeout` (datetime), `note_requester`, `foto_referensi_requester`, `link_foto_drive_requester`, `note_executor`, `pic_pemohon`, `pelaksana` (M2M), `status` (`BELUM_TAYANG`, `SEDANG_TAYANG`, `SUDAH_TAKEOUT`).
* **`JadwalTayangMateri`**:
  * Sub-item materi tayang dengan status independen (`BELUM_TAYANG`, `SEDANG_TAYANG`, `SUDAH_TAKEOUT`).
* **Bukti Pendukung Tayang & Takeout**:
  * `JadwalTayangFotoTayang`: Multi-foto tayang aktual di layar LED lapangan.
  * `JadwalTayangBuktiPlaylist`: Bukti screenshot playlist CMS per sesi (`foto_pagi`, `foto_siang`, `foto_malam`).
  * `JadwalTayangFotoTakeout`: Multi-foto bukti materi telah diturunkan (*takeout*).

### 4.5 Audit Trail: `EditHistory`
* Menyimpan rekaman riwayat perubahan data secara terperinci untuk mencegah manipulasi data penayangan:
  * `user`: Pengguna yang melakukan modifikasi.
  * `request_type`: `DOC_REQUEST` atau `JADWAL_TAYANG`.
  * `action`: `CREATE`, `UPDATE`, `DELETE`.
  * `field_name`: Nama atribut yang diubah (misal: "Tanggal Takeout", "Status Materi", "Foto Bukti").
  * `old_value` & `new_value`: Nilai sebelum dan sesudah perubahan.
  * `timestamp`: Waktu pencatatan.

---

## 5. Alur Bisnis & State Machine (Business Workflows)

### 5.1 Siklus Status Documentation & Maintenance Request
```
  [Requester Submit]
          │
          ▼
     ┌─────────┐
     │  TODO   │  (Belum ada bukti foto / materi belum dikerjakan)
     └────┬────┘
          │ Upload bukti pertama / parsial
          ▼
 ┌─────────────────┐
 │   IN_PROGRESS   │  (Sebagian materi telah terupload buktinya)
 └────────┬────────┘
          │ Seluruh materi memiliki bukti foto valid
          ▼
     ┌─────────┐
     │  DONE   │  (Selesai / archived)
     └─────────┘
```
* **Status Roll-up Otomatis**: Fungsi `_sync_parent_status_from_materi_proofs()` secara otomatis mengevaluasi seluruh child `materi_items`. Jika 100% item memiliki bukti foto, status induk berganti menjadi `DONE`.

### 5.2 Siklus Status Jadwal Tayang
Status Jadwal Tayang dihitung secara hierarkis dari bawah ke atas (*Bottom-Up*):
1. **Status Materi Individual (`calculate_status`)**:
   * Jika ada `foto_takeout_set` $\rightarrow$ `SUDAH_TAKEOUT`.
   * Jika ada `foto_tayang_set` ATAU `bukti_playlist` (pagi/siang/malam) $\rightarrow$ `SEDANG_TAYANG`.
   * Jika belum ada keduanya $\rightarrow$ `BELUM_TAYANG`.
2. **Status Jadwal Induk (`auto_update_status`)**:
   * Status induk mengikuti status materi yang **paling tertinggal**:
     * Jika ada satu saja materi `BELUM_TAYANG` $\rightarrow$ Induk `BELUM_TAYANG`.
     * Jika tidak ada yang belum tayang, tapi ada yang `SEDANG_TAYANG` $\rightarrow$ Induk `SEDANG_TAYANG`.
     * Hanya jika seluruh materi berstatus `SUDAH_TAKEOUT` $\rightarrow$ Induk `SUDAH_TAKEOUT`.

---

## 6. Mesin Peringatan & Notifikasi (Takeout Alert Engine)

Untuk mencegah materi iklan tetap tayang melewati durasi kontrak (resiko komplain lisensi / denda), sistem dilengkapi mesin peringatan dinamis:

### 6.1 Model Aturan: `TakeoutAlertRule`
* Aturan dapat dikonfigurasi melalui antarmuka Admin (`/notifications/rules/`):
  * **Trigger Direction**: `BEFORE` (sebelum waktu takeout) atau `AFTER` (sesudah waktu takeout).
  * **Offset Unit**: `DAY` (Hari) atau `HOUR` (Jam).
  * **Offset Value**: Angka integer (misal: 1 hari, 6 jam, 0 jam).
  * **Urgency**: `WARNING` (peringatan standar kuning) atau `URGENT` (peringatan kritis merah).
  * **Lead Minutes**: Nilai menit terkonversi otomatis untuk komputasi cepat query basis data.

### 6.2 Polling & Alerting Frontend
* **Summary Poller**: Polling otomatis background setiap **10 detik** ke `/api/notifications/summary/` via fetch AJAX.
* **Badge Counter**: Menampilkan jumlah jadwal aktif yang membutuhkan perhatian di navbar header.
* **Urgent Toasts**: Jadwal yang berada pada rentang waktu `URGENT` memunculkan *Bootstrap Toast* mengambang di pojok kanan atas setiap **12 detik**.

---

## 7. Master Data Engine & Modul Excel

Sistem menggunakan arsitektur **Registry-Led Generic Master Data Controller** (`MASTER_DATA_REGISTRY`):
* Menghindari duplikasi kode CRUD untuk entitas sederhana dengan mendaftarkan konfigurasi slug:
  * `brand-materi` $\rightarrow$ `BrandMateri`
  * `lokasi` $\rightarrow$ `Lokasi`
  * `dokumentator` $\rightarrow$ `Dokumentator`
  * `led-type` $\rightarrow$ `LEDType`
  * `requirement` $\rightarrow$ `Requirement`
  * `view-photo` $\rightarrow$ `ViewPhoto`
  * `camera-type` $\rightarrow$ `cameratype`

### 7.1 Fitur Excel Import / Export
1. **Export (`/master/<slug>/export/`)**:
   * Menghasilkan file Excel `.xlsx` dengan styling profesional (header biru gelap, teks tebal, auto-width kolom).
2. **Import Preview (`/master/<slug>/import/preview/`)**:
   * Membaca file `.xlsx`, memeriksa keberadaan kolom `name`, dan mendeteksi data baru vs duplikat yang sudah ada di database tanpa langsung melakukan insert.
3. **Import Confirm (`/master/<slug>/import/confirm/`)**:
   * Menjalankan `bulk_create` hanya untuk entri baru dalam satu transaksi database yang aman.

---

## 8. Spesifikasi Routing & Endpoint URL

### 8.1 Dokumentasi & Maintenance
| Method | Endpoint URL | Nama Route | Hak Akses | Deskripsi |
|---|---|---|---|---|
| `GET` | `/requests/` | `doc_request_list` | Login Required | Daftar Documentation Requests (terfilter per role). |
| `GET, POST` | `/requests/create/` | `doc_request_create` | Requester, Admin | Form pembuatan permintaan dokumentasi baru. |
| `GET, POST` | `/requests/<id>/edit/` | `doc_request_edit` | Requester, Staff, Admin | Edit detail permintaan dokumentasi. |
| `GET` | `/requests/<id>/` | `doc_request_detail` | Login Required | Detail request, daftar penugasan lokasi, bukti foto. |
| `POST` | `/requests/<id>/delete/` | `doc_request_delete` | Requester, Staff, Admin | Hapus tiket dokumentasi. |
| `POST` | `/requests/<id>/status/` | `doc_request_update_status` | Staff, Admin | Perubahan status manual. |
| `POST` | `/requests/assignment/<id>/pelaksana/` | `doc_request_update_lokasi_pelaksana` | Staff, Admin | Update penugasan dokumentator per lokasi. |
| `GET` | `/requests/export/perintah-kerja/` | `doc_request_export_perintah_kerja` | Login Required | Preview cetak lembar Surat Perintah Kerja (SPK). |
| `GET` | `/maintenance/` | `maint_request_list` | Login Required | Daftar Maintenance & Troubleshoot LED requests. |
| `GET, POST` | `/maintenance/create/` | `maint_request_create` | Requester, Admin | Buat tiket perbaikan/troubleshoot baru. |
| `GET, POST` | `/maintenance/<id>/edit/` | `maint_request_edit` | Requester, Staff, Admin | Edit tiket maintenance. |
| `GET` | `/maintenance/<id>/` | `maint_request_detail` | Login Required | Detail kerusakan, inventory terkait, bukti perbaikan. |

### 8.2 Jadwal Tayang & Notifikasi
| Method | Endpoint URL | Nama Route | Hak Akses | Deskripsi |
|---|---|---|---|---|
| `GET` | `/jadwal-tayang/` | `jadwal_tayang_list` | Login Required | Daftar jadwal tayang dan status pemutaran. |
| `GET` | `/jadwal-tayang/report/` | `jadwal_tayang_report` | Login Required | Rekapitulasi laporan tayang dan takeout. |
| `GET, POST` | `/jadwal-tayang/create/` | `jadwal_tayang_create` | Requester, Admin | Input jadwal tayang baru. |
| `GET, POST` | `/jadwal-tayang/<id>/edit/` | `jadwal_tayang_edit` | Requester, Staff, Admin | Edit jadwal tayang. |
| `GET` | `/jadwal-tayang/<id>/` | `jadwal_tayang_detail` | Login Required | Detail materi, verifikasi playlist, dan foto takeout. |
| `POST` | `/jadwal-tayang/<id>/upload-photos/` | `jadwal_tayang_upload_photos` | Executor, Staff, Admin | Upload bukti foto tayang, playlist, atau takeout. |
| `GET` | `/notifications/` | `notification_list` | Login Required | Halaman daftar seluruh alert aktif. |
| `GET` | `/api/notifications/summary/` | `notification_summary` | Login Required (AJAX) | Endpoint JSON polling notifikasi navbar & toast. |
| `GET, POST` | `/notifications/rules/` | `takeout_alert_rule_list` | Admin Only | Konfigurasi aturan alert takeout. |

### 8.3 Manajemen Master Data & Pengguna
| Method | Endpoint URL | Nama Route | Hak Akses | Deskripsi |
|---|---|---|---|---|
| `GET` | `/master/<slug>/` | `master_data_list` | Admin Only | Tampilan tabel data referensi per slug. |
| `POST` | `/master/<slug>/create/` | `master_data_create` | Admin Only | Tambah data master (mendukung modal AJAX). |
| `POST` | `/master/<slug>/<id>/edit/` | `master_data_edit` | Admin Only | Edit nama data master. |
| `POST` | `/master/<slug>/<id>/delete/`| `master_data_delete`| Admin Only | Hapus data master. |
| `GET` | `/master/<slug>/export/` | `master_data_export` | Admin Only | Download dataset dalam format Excel `.xlsx`. |
| `POST` | `/master/<slug>/import/preview/` | `master_data_import_preview` | Admin Only | Validasi dan preview data Excel yang diunggah. |
| `POST` | `/master/<slug>/import/confirm/` | `master_data_import_confirm` | Admin Only | Eksekusi commit import data ke database. |
| `GET` | `/users/` | `user_list` | Admin Only | Manajemen seluruh user dan role assignment. |
| `GET` | `/users/never-login/` | `user_never_login_list` | Admin Only | Audit user aktif yang belum pernah melakukan login. |
| `POST` | `/users/<id>/login-requirement/` | `user_update_login_requirement` | Admin Only | Toggle status kewajiban login user. |

---

## 9. Petunjuk Operasional, Deployment & Troubleshooting (Runbook)

### 9.1 Menjalankan di Lingkungan Pengembangan Lokal (Windows)
Gunakan helper PowerShell [dev.ps1](file:///d:/code/django_its/djangtest/dev.ps1):
```powershell
# 1. Jalankan migrasi database
.\dev.ps1 migrate

# 2. Lakukan seeding awal (opsional jika fresh database)
.\dev.ps1 seed

# 3. Jalankan development server (port 8000)
.\dev.ps1 runserver
```

### 9.2 Migrasi dari SQLite Lokal ke PostgreSQL Server
Jika sistem ingin dipindahkan ke basis data PostgreSQL:
1. Pastikan PostgreSQL 12 atau 14 telah terpasang dan database kosong dibuat:
   ```sql
   CREATE DATABASE djangtest;
   ```
2. Konfigurasi kredensial pada file `.env`:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/djangtest
   ```
3. Generate skema tabel baru di PostgreSQL:
   ```powershell
   .venv\Scripts\python manage.py migrate
   ```
4. Transfer seluruh data yang ada di `db.sqlite3` ke PostgreSQL:
   ```powershell
   .venv\Scripts\python migrate_data.py
   ```

### 9.3 Prosedur Deployment di Server Produksi (Linux / Gunicorn)
Sesuai panduan pada [notes.txt](file:///d:/code/django_its/djangtest/notes.txt):
```bash
# 1. Masuk ke direktori web
cd /var/www/djangtest

# 2. Aktifkan virtualenv server
source venv/bin/activate

# 3. Update dependensi & migrasi skema
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# 4. Restart proses Gunicorn
pkill -f gunicorn
/var/www/djangtest/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8002 mysite.wsgi:application
```

---

## 10. Pengujian Otomatis (Test Suite)

Project ini memiliki cakupan pengujian unit dan integrasi yang ekstensif pada [products/tests.py](file:///d:/code/django_its/djangtest/products/tests.py):
* `DocumentationRequestMultiLokasiTests`: Validasi split lokasi dan sinkronisasi penugasan pelaksana.
* `RequestCreationPermissionTests`: Verifikasi ketat pembatasan hak akses create/read/update/delete antar role.
* `JadwalTayangHistoryTests`: Pengujian pencatatan otomatis `EditHistory` pada setiap aksi manipulasi jadwal.
* `JadwalTayangVisibilityTests` & `JadwalTayangListPhotoStatusTests`: Verifikasi alur propagasi status dari foto materi ke status jadwal utama.
* `TakeoutNotificationTests`: Verifikasi kalkulasi sisa waktu (lead minutes), evaluasi status tayang, dan pengurutan prioritas alert.

Jalankan test suite menggunakan:
```powershell
.venv\Scripts\python manage.py test products
```
