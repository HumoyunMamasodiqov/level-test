# test_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('test_app.urls')),  # test_app urls
]

# Xatolik sahifalari - faqat shu yerda bo'lishi kerak
handler400 = 'test_app.views.custom_400'
handler403 = 'test_app.views.custom_403'
handler404 = 'test_app.views.custom_404'
handler500 = 'test_app.views.custom_500'

# Debug rejimida static va media fayllar uchun
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)