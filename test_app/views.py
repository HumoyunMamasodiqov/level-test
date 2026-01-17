from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
import json
import requests
from .models import Level, Question, Answer, TestSession, TestResult
import uuid
import logging
from django.db.models import Avg, Count

logger = logging.getLogger(__name__)

# Xatolik sahifalari uchun funksiyalar (avval e'lon qilamiz)
def custom_400(request, exception=None):
    """400 xatolik sahifasi"""
    return render(request, 'test_app/400.html', status=400)

def custom_403(request, exception=None):
    """403 xatolik sahifasi"""
    return render(request, 'test_app/403.html', status=403)

def custom_404(request, exception=None):
    """404 xatolik sahifasi"""
    return render(request, 'test_app/404.html', status=404)

def custom_500(request):
    """500 xatolik sahifasi"""
    return render(request, 'test_app/500.html', status=500)

# Asosiy view funksiyalar
def index(request):
    return render(request, 'test_app/index.html')

def about(request):
    return render(request, 'test_app/about.html')

def contact(request):
    return render(request, 'test_app/contact.html')

def instructions(request):
    return render(request, 'test_app/instructions.html')

def statistics(request):
    total_tests = TestSession.objects.count()
    completed_tests = TestSession.objects.filter(completed=True).count()
    avg_score = TestResult.objects.aggregate(Avg('score'))['score__avg'] or 0
    
    level_stats = []
    for level in Level.objects.all():
        level_results = TestResult.objects.filter(session__level=level)
        level_count = level_results.count()
        if level_count > 0:
            avg_level_score = level_results.aggregate(Avg('score'))['score__avg'] or 0
            level_stats.append({
                'level': level.name,
                'count': level_count,
                'avg_score': round(avg_level_score, 1)
            })
    
    context = {
        'total_tests': total_tests,
        'completed_tests': completed_tests,
        'avg_score': round(avg_score, 1),
        'level_stats': level_stats
    }
    
    return render(request, 'test_app/statistics.html', context)

def all_results(request):
    results = TestResult.objects.select_related('session', 'session__level').order_by('-created_at')[:100]
    return render(request, 'test_app/results.html', {'results': results})

def result_detail(request, session_id):
    session = get_object_or_404(TestSession, session_id=session_id)
    result = get_object_or_404(TestResult, session=session)
    return render(request, 'test_app/result_detail.html', {'result': result})

# API View funksiyalar
@csrf_exempt
def get_levels(request):
    if request.method == 'GET':
        levels = Level.objects.filter(is_active=True).order_by('order')
        levels_data = [{
            'id': level.id,
            'name': level.name,
            'code': level.code,
            'description': level.description,
            'time_limit': level.time_limit,
            'question_count': level.question_count
        } for level in levels]
        
        return JsonResponse({
            'success': True,
            'levels': levels_data
        })

@csrf_exempt
def start_test_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            level_id = data.get('level_id')
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            phone_number = data.get('phone_number', '').strip()
            
            if not level_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Level ID talab qilinadi'
                })
            
            if not first_name or not last_name:
                return JsonResponse({
                    'success': False,
                    'error': 'Ism va Familya talab qilinadi'
                })
            
            level = get_object_or_404(Level, id=level_id)
            session_id = f"IT_{timezone.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
            
            session = TestSession.objects.create(
                session_id=session_id,
                level=level,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number
            )
            
            # Adminga yangi test boshlanganligi haqida xabar
            message = (
                "🎯 *Yangi test boshlandi!*\n\n"
                f"👤 *Ism:* {first_name} {last_name}\n"
                f"📞 *Telefon:* {phone_number or 'Noma lum'}\n"
                f"📊 *Daraja:* {level.name}\n"
                f"🆔 *Session ID:* `{session_id}`\n"
                f"⏰ *Vaqt limiti:* {level.time_limit} daqiqa"
            )
            
            send_admin_notification(message)
            
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'time_limit': level.time_limit,
                'question_count': level.question_count
            })
            
        except Exception as e:
            logger.error(f"Session yaratishda xatolik: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@csrf_exempt
def get_questions(request, session_id):
    if request.method == 'GET':
        try:
            session = get_object_or_404(TestSession, session_id=session_id)
            level = session.level
            
            # Tasodifiy savollarni olish
            questions = Question.objects.filter(
                level=level, 
                is_active=True
            ).order_by('?')[:level.question_count]
            
            questions_data = []
            for question in questions:
                answers = question.answers.all().order_by('order')
                question_data = {
                    'id': question.id,
                    'question_text': question.question_text,
                    'answers': [
                        {
                            'id': answer.id,
                            'answer_text': answer.answer_text,
                            'is_correct': answer.is_correct
                        } for answer in answers
                    ]
                }
                
                # Agar rasm bo'lsa
                if question.image:
                    question_data['image_url'] = request.build_absolute_uri(question.image.url)
                
                questions_data.append(question_data)
            
            return JsonResponse({
                'success': True,
                'questions': questions_data,
                'level_name': level.name,
                'time_limit': level.time_limit
            })
        except Exception as e:
            logger.error(f"Savollarni olishda xatolik: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@csrf_exempt
def submit_test(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            answers = data.get('answers', [])
            time_taken = data.get('time_taken', 0)
            
            if not session_id:
                return JsonResponse({'success': False, 'error': 'Session ID talab qilinadi'})
            
            session = get_object_or_404(TestSession, session_id=session_id)
            
            # Testni tugatilgan deb belgilash
            session.completed = True
            session.end_time = timezone.now()
            session.save()
            
            # To'g'ri javoblarni hisoblash
            correct = 0
            for answer_data in answers:
                try:
                    selected_answer = Answer.objects.get(id=answer_data['answer_id'])
                    if selected_answer.is_correct:
                        correct += 1
                except Answer.DoesNotExist:
                    continue
            
            total = len(answers)
            score = (correct / total * 100) if total > 0 else 0
            
            # Natijani saqlash
            test_result = TestResult.objects.create(
                session=session,
                correct_answers=correct,
                total_questions=total,
                score=round(score, 1),
                time_taken=time_taken
            )
            
            # Foydalanuvchiga Telegram orqali natija yuborish
            telegram_sent = False
            if session.phone_number and session.phone_number.isdigit():
                telegram_sent = send_telegram_message(
                    chat_id=session.phone_number,
                    session=session,
                    result=test_result
                )
                if telegram_sent:
                    test_result.telegram_sent = True
            
            # Adminga to'liq natija yuborish
            admin_notified = send_admin_result(
                session=session,
                result=test_result
            )
            if admin_notified:
                test_result.admin_notified = True
            
            test_result.save()
            
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'correct': correct,
                'total': total,
                'score': round(score, 1),
                'time_taken': time_taken,
                'telegram_sent': telegram_sent,
                'admin_notified': admin_notified
            })
            
        except Exception as e:
            logger.error(f"Test yuborishda xatolik: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

def send_telegram_message(chat_id, session, result):
    try:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        
        if not bot_token:
            return False
        
        message = (
            "🎓 *IT House Test Natijasi*\n\n"
            f"👤 *Ishtirokchi:* {session.first_name} {session.last_name}\n"
            f"📊 *Daraja:* {session.level.name}\n"
            f"⏰ *Sarflangan vaqt:* {result.get_time_taken_display()}\n\n"
            f"📈 *Natija:*\n"
            f"✅ To'g'ri javoblar: {result.correct_answers}/{result.total_questions}\n"
            f"🏆 Foiz: {result.score}%\n\n"
            f"🆔 *ID:* `{session.session_id}`\n"
            f"📅 *Sana:* {result.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        )
        
        if result.score >= 80:
            message += "\n🎉 Ajoyib natija! Siz bu darajani mukammal egallagansiz!"
        elif result.score >= 60:
            message += "\n👍 Yaxshi natija! Biroz mashq qilsangiz yanada yaxshilashingiz mumkin."
        else:
            message += "\n💪 Qayta urinib ko'ring! Ko'proq mashq qilishingiz kerak."
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Telegramga yuborishda xatolik: {e}")
        return False

def send_admin_notification(message):
    try:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
        
        if not bot_token or not admin_chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': admin_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Adminga xabar yuborishda xatolik: {e}")
        return False

def send_admin_result(session, result):
    try:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
        
        if not bot_token or not admin_chat_id:
            return False
        
        message = (
            "📊 *TEST YAKUNLANDI*\n\n"
            f"👤 *Ishtirokchi:* {session.first_name} {session.last_name}\n"
            f"📞 *Telefon:* {session.phone_number or 'Noma lum'}\n"
            f"📚 *Daraja:* {session.level.name}\n"
            f"⏱️ *Vaqt:* {result.get_time_taken_display()}\n\n"
            f"📈 *NATIJALAR:*\n"
            f"🎯 To'g'ri javoblar: {result.correct_answers}/{result.total_questions}\n"
            f"🏆 Foiz: {result.score}%\n\n"
            f"🆔 *Session ID:* `{session.session_id}`\n"
            f"📅 *Yakunlangan vaqt:* {result.created_at.strftime('%d.%m.%Y %H:%M:%S')}"
        )
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': admin_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Adminga natija yuborishda xatolik: {e}")
        return False

@csrf_exempt
def get_test_result(request, session_id):
    try:
        session = get_object_or_404(TestSession, session_id=session_id)
        result = get_object_or_404(TestResult, session=session)
        
        return JsonResponse({
            'success': True,
            'result': {
                'session_id': session.session_id,
                'first_name': session.first_name,
                'last_name': session.last_name,
                'level': session.level.name if session.level else None,
                'correct_answers': result.correct_answers,
                'total_questions': result.total_questions,
                'score': result.score,
                'time_taken': result.time_taken,
                'time_taken_display': result.get_time_taken_display(),
                'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except TestResult.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Test natijasi topilmadi'
        }, status=404)