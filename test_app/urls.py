# test_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifalar
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('instructions/', views.instructions, name='instructions'),
    path('statistics/', views.statistics, name='statistics'),
    path('results/', views.all_results, name='all_results'),
    path('results/<str:session_id>/', views.result_detail, name='result_detail'),
    
    # API endpointlar
    path('api/levels/', views.get_levels, name='get_levels'),
    path('api/start-session/', views.start_test_session, name='start_test_session'),
    path('api/questions/<str:session_id>/', views.get_questions, name='get_questions'),
    path('api/submit-test/', views.submit_test, name='submit_test'),
    path('api/test-results/<str:session_id>/', views.get_test_result, name='get_test_result'),
]

# BU QISMI O'CHIRING YO'Q QILING! Xatolik handlerlari faqat asosiy urls.py da bo'lishi kerak