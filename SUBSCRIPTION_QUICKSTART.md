# 🚀 Quick Start: Subscription Implementation

## ✅ Implementasi Selesai

Fitur subscription untuk students telah berhasil diimplementasikan dengan komponen berikut:

### 📁 File Baru yang Ditambahkan:
1. `subscriptions/decorators.py` - Decorator & Mixin untuk protect views
2. `subscriptions/context_processors.py` - Context processor untuk template
3. `subscriptions/management/commands/expire_subscriptions.py` - Command untuk expire subscription

### 🔧 File yang Dimodifikasi:
1. `ta3lem/settings/base.py` - Tambah context processor
2. `vite/templates/base.html` - Tambah link subscription & badge Premium/Free
3. `users/templates/users/course/list.html` - Tambah banner promo & warning
4. `users/views.py` - Tambah StudentDashboardView

## 🎯 Features Tersedia

### 1. Navigation & UI
- ✅ Link "Subscription" di desktop & mobile menu
- ✅ Badge Premium/Free di user dropdown
- ✅ Banner promo untuk non-premium users
- ✅ Warning banner untuk subscription akan expire (≤7 hari)
- ✅ Button "Upgrade Premium" di course list

### 2. Access Control
- ✅ `@subscription_required` decorator
- ✅ `SubscriptionRequiredMixin` untuk class-based views
- ✅ Auto redirect ke plans page jika tidak subscribe

### 3. Template Variables
- ✅ `user_has_subscription` - Boolean check
- ✅ `user_subscription` - Object subscription aktif

### 4. Management
- ✅ Command: `python manage.py expire_subscriptions`
- ✅ Otomatis expire subscription yang lewat tanggal

## 📖 Cara Pakai

### Protect View dengan Subscription:

```python
# Function-based view
from subscriptions.decorators import subscription_required

@subscription_required
def premium_content(request):
    return render(request, 'premium.html')

# Class-based view
from subscriptions.decorators import SubscriptionRequiredMixin

class PremiumView(SubscriptionRequiredMixin, DetailView):
    model = Course
```

### Check Subscription di Template:

```html
{% if user_has_subscription %}
    <p>Anda Premium Member! 🎉</p>
{% else %}
    <a href="{% url 'subscriptions:plans' %}">Upgrade Premium</a>
{% endif %}
```

### Check Subscription di Python:

```python
from subscriptions.services import SubscriptionService

# Check status
has_sub = SubscriptionService.user_has_active_subscription(user)

# Get subscription object
subscription = SubscriptionService.get_user_subscription(user)

# Get stats
stats = SubscriptionService.get_subscription_stats(user)
```

## 🔗 URL Routes

| URL | Deskripsi |
|-----|-----------|
| `/subscriptions/plans/` | Lihat semua subscription plans |
| `/subscriptions/subscribe/<slug>/` | Subscribe ke plan |
| `/subscriptions/trial/<slug>/` | Mulai free trial |
| `/subscriptions/manage/` | Kelola subscription |
| `/subscriptions/cancel/` | Cancel subscription |

## 🧪 Testing

```bash
# 1. Check konfigurasi
source .venv/bin/activate
python manage.py check

# 2. Create sample plan (di admin atau shell)
python manage.py shell
>>> from subscriptions.models import SubscriptionPlan
>>> plan = SubscriptionPlan.objects.create(
...     name="Premium Monthly",
...     slug="premium-monthly",
...     price=99000,
...     currency="IDR",
...     billing_cycle="monthly",
...     trial_days=7,
...     features=["Akses semua kursus", "Sertifikat", "Support prioritas"],
...     is_active=True
... )
>>> exit()

# 3. Test expire command
python manage.py expire_subscriptions

# 4. Run server
python manage.py runserver
```

## 🎨 UI Flow untuk Student

1. **Student login** → Lihat banner promo (jika belum subscribe)
2. **Klik "Lihat Plans"** → Tampil list plans dengan harga
3. **Klik "Pilih Plan"** → Redirect ke payment checkout
4. **Setelah payment success** → Subscription aktif
5. **Dashboard menampilkan** → Badge "Premium" + no banner promo
6. **7 hari sebelum expire** → Warning banner muncul
7. **Klik "Subscription" menu** → Kelola/cancel subscription

## ⚙️ Automation (Optional)

### Cron Job untuk Auto-Expire:
```bash
# Edit crontab
crontab -e

# Tambahkan (jalankan setiap hari jam 00:00):
0 0 * * * cd /path/to/ta3lem-lms && source .venv/bin/activate && python manage.py expire_subscriptions >> /var/log/subscription_expire.log 2>&1
```

## 📝 Notes

- Models `SubscriptionPlan` dan `UserSubscription` sudah ada sebelumnya
- Views dan templates untuk subscription management sudah ada
- Implementasi ini fokus pada **integrasi UI dan access control** untuk students
- Payment integration sudah ada di `payments` app (akan auto-create subscription)

## ✨ Ready to Use!

Semua komponen sudah terimplementasi dan terintegrasi. Tinggal:
1. Create subscription plans via Django admin
2. Test flow dari student perspective
3. Configure payment gateway jika belum
4. Setup cron job untuk auto-expire (optional)

**Status: ✅ COMPLETED**
