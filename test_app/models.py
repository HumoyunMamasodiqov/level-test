from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Level(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('elementary', 'Elementary'),
        ('pre_intermediate', 'Pre-Intermediate'),
        ('intermediate', 'Intermediate'),
        ('upper_intermediate', 'Upper-Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    order = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    time_limit = models.IntegerField(default=15, help_text="Daqiqa bilan")  # ✅ Yangi: vaqt limiti
    question_count = models.IntegerField(default=20)  # ✅ Yangi: savollar soni
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} ({self.time_limit} daqiqa)"

class TestSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    first_name = models.CharField(max_length=100)  # ✅ Yangi: ism
    last_name = models.CharField(max_length=100)  # ✅ Yangi: familya
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # ✅ Yangi: telefon
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.session_id}"

class Question(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    image = models.ImageField(upload_to='questions/', blank=True, null=True)  # ✅ Yangi: rasm
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.level.name}: {self.question_text[:50]}..."

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.answer_text

class TestResult(models.Model):
    session = models.OneToOneField(TestSession, on_delete=models.CASCADE, related_name='result')
    correct_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    time_taken = models.IntegerField(default=0, help_text="Soniyalar bilan")
    telegram_sent = models.BooleanField(default=False)
    admin_notified = models.BooleanField(default=False)  # ✅ Yangi: adminga xabar berildi
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.session.first_name} {self.session.last_name}: {self.score}%"
    
    def get_time_taken_display(self):
        minutes = self.time_taken // 60
        seconds = self.time_taken % 60
        return f"{minutes}:{seconds:02d}"