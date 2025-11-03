from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
import markdown
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from io import BytesIO
import os
import re

from .forms import LessonForm, StudentForm, BioForm, LoginForm, ProfileForm, PasswordChangeForm
from .models import Lesson, Student, Teacher


def get_current_teacher(request):
    """Получить текущего учителя из сессии"""
    teacher_id = request.session.get('teacher_id')
    if teacher_id:
        try:
            return Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return None
    return None


def get_theme(request):
    """Получить текущую тему из сессии"""
    return request.session.get('theme', 'neon')


def set_theme(request, theme):
    """Установить тему в сессию"""
    request.session['theme'] = theme


def teacher_login(request):
    """Вход учителя"""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            try:
                teacher = Teacher.objects.get(username=username)
                if teacher.check_password(password):
                    request.session['teacher_id'] = teacher.id
                    return redirect('students_list')
                else:
                    form.add_error('password', 'Неверный пароль')
            except Teacher.DoesNotExist:
                form.add_error('username', 'Учитель не найден')
    else:
        form = LoginForm()
    
    theme = get_theme(request)
    return render(request, "lessons/login.html", {"form": form, "theme": theme})


def teacher_logout(request):
    """Выход"""
    request.session.pop('teacher_id', None)
    return redirect('teacher_login')


def students_list(request):
    """Список учеников (главная страница)"""
    teacher = get_current_teacher(request)
    if not teacher:
        return redirect('teacher_login')
    
    students = Student.objects.filter(teacher=teacher)
    
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.teacher = teacher
            student.save()
            return redirect('students_list')
    else:
        form = StudentForm()
    
    theme = get_theme(request)
    return render(request, "lessons/students_list.html", {
        "form": form,
        "students": students,
        "teacher": teacher,
        "theme": theme,
    })


def student_detail(request, student_id):
    """Детальная страница ученика с занятиями и био"""
    teacher = get_current_teacher(request)
    if not teacher:
        return redirect('teacher_login')
    
    student = get_object_or_404(Student, id=student_id, teacher=teacher)
    
    # Обработка формы занятий
    if request.method == "POST" and 'add_lesson' in request.POST:
        lesson_form = LessonForm(request.POST)
        if lesson_form.is_valid():
            lesson = lesson_form.save(commit=False)
            lesson.student = student
            lesson.teacher = teacher
            dt = lesson.start_time
            if timezone.is_naive(dt):
                lesson.start_time = timezone.make_aware(dt, timezone.get_default_timezone())
            lesson.notified_one_hour = False
            lesson.notified_five_minutes = False
            lesson.save()
            return redirect('student_detail', student_id=student_id)
    else:
        lesson_form = LessonForm()
        lesson_form.fields['student'].queryset = Student.objects.filter(id=student_id, teacher=teacher)
        lesson_form.fields['student'].initial = student
    
    # Обработка формы био
    if request.method == "POST" and 'save_bio' in request.POST:
        bio_form = BioForm(request.POST, instance=student)
        if bio_form.is_valid():
            bio_form.save()
            return redirect('student_detail', student_id=student_id)
    else:
        bio_form = BioForm(instance=student)
    
    lessons = Lesson.objects.filter(student=student).order_by('start_time')
    
    # Конвертируем MD в HTML для отображения
    bio_html = markdown.markdown(student.bio) if student.bio else ""
    
    theme = get_theme(request)
    return render(request, "lessons/student_detail.html", {
        "student": student,
        "lessons": lessons,
        "lesson_form": lesson_form,
        "bio_form": bio_form,
        "bio_html": bio_html,
        "teacher": teacher,
        "theme": theme,
    })


def student_bio_pdf(request, student_id):
    """Экспорт био ученика в PDF"""
    teacher = get_current_teacher(request)
    if not teacher:
        return redirect('teacher_login')
    
    student = get_object_or_404(Student, id=student_id, teacher=teacher)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    # Регистрируем шрифт с поддержкой кириллицы
    # Используем встроенный шрифт, который поддерживает кириллицу
    # В Windows обычно есть Arial Unicode MS или используем стандартный
    try:
        # Пробуем использовать системный шрифт с кириллицей
        font_paths = [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        ]
        font_registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
                    pdfmetrics.registerFont(TTFont('CyrillicFontBold', font_path.replace('.ttf', 'bd.ttf').replace('-Regular.ttf', '-Bold.ttf')))
                    font_registered = True
                    break
                except:
                    continue
    except:
        pass
    
    # Если шрифт не найден, используем стандартный подход с HTML-тегами
    if not font_registered:
        # Используем встроенные шрифты ReportLab
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'
    else:
        font_name = 'CyrillicFont'
        font_name_bold = 'CyrillicFontBold'
    
    # Создаем стили с поддержкой кириллицы
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        fontName=font_name_bold,
        fontSize=22,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        leading=26
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        fontName=font_name,
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=TA_CENTER,
        leading=14
    )
    
    content_style = ParagraphStyle(
        'CustomContent',
        fontName=font_name,
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        leading=16,
        leftIndent=0,
        rightIndent=0
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        fontName=font_name_bold,
        fontSize=14,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        spaceBefore=16,
        alignment=TA_LEFT,
        leading=18
    )
    
    story = []
    
    # Заголовок
    title_text = student.name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Информация об учителе
    teacher_text = f"Учитель: {teacher.username}".replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    story.append(Paragraph(teacher_text, subtitle_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Контент био
    if student.bio:
        # Конвертируем MD в HTML
        html_content = markdown.markdown(student.bio, extensions=['nl2br', 'fenced_code'])
        
        # Обрабатываем HTML для ReportLab Paragraph
        # Разбиваем на параграфы
        paragraphs = re.split(r'<p>|</p>|<br\s*/?>', html_content)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Обрабатываем заголовки
            if para.startswith('<h1>'):
                text = re.sub(r'<h1>(.*?)</h1>', r'\1', para)
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(text, heading_style))
            elif para.startswith('<h2>'):
                text = re.sub(r'<h2>(.*?)</h2>', r'\1', para)
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(text, heading_style))
            elif para.startswith('<h3>'):
                text = re.sub(r'<h3>(.*?)</h3>', r'\1', para)
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(text, heading_style))
            elif para.startswith('<ul>') or para.startswith('<ol>'):
                # Обрабатываем списки
                items = re.findall(r'<li>(.*?)</li>', para)
                for item in items:
                    text = item.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(f"• {text}", content_style))
            elif para.startswith('<code>') or para.startswith('<pre>'):
                # Код пропускаем или обрабатываем отдельно
                text = re.sub(r'<code>(.*?)</code>', r'\1', para)
                text = re.sub(r'<pre>(.*?)</pre>', r'\1', text, flags=re.DOTALL)
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(text, content_style))
            else:
                # Обычный текст
                # Убираем HTML теги, но сохраняем сущности
                text = re.sub(r'<[^>]+>', '', para)
                text = text.replace('&nbsp;', ' ')
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if text.strip():
                    story.append(Paragraph(text, content_style))
    else:
        empty_text = "Биография не заполнена".replace('&', '&amp;')
        story.append(Paragraph(empty_text, content_style))
    
    doc.build(story)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    # Кодируем имя файла правильно
    filename = f"{student.name}_bio.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def settings_page(request):
    """Страница настроек"""
    teacher = get_current_teacher(request)
    if not teacher:
        return redirect('teacher_login')
    
    tab = request.GET.get('tab', 'account')
    
    # Обработка смены темы
    if request.method == "POST" and 'change_theme' in request.POST:
        theme = request.POST.get('theme', 'neon')
        set_theme(request, theme)
        return HttpResponseRedirect(reverse('settings_page') + '?tab=themes')
    
    # Обработка формы аккаунта (username и telegram_chat_id)
    profile_form = None
    password_form = None
    
    if request.method == "POST" and tab == 'account':
        if 'update_profile' in request.POST:
            profile_form = ProfileForm(request.POST, instance=teacher)
            if profile_form.is_valid():
                profile_form.save()
                return HttpResponseRedirect(reverse('settings_page') + '?tab=account')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.POST)
            if password_form.is_valid():
                teacher.set_password(password_form.cleaned_data['new_password'])
                teacher.save()
                return HttpResponseRedirect(reverse('settings_page') + '?tab=account')
    else:
        profile_form = ProfileForm(instance=teacher)
        password_form = PasswordChangeForm()
    
    theme = get_theme(request)
    
    # Загружаем и конвертируем MD файл о проекте
    about_content = ""
    if tab == 'about':
        try:
            from pathlib import Path
            about_file = Path(__file__).parent.parent / 'templates' / 'lessons' / 'about_project.md'
            if about_file.exists():
                about_content = markdown.markdown(about_file.read_text(encoding='utf-8'))
        except Exception:
            about_content = "<p>Информация о проекте загружается...</p>"
    
    return render(request, "lessons/settings.html", {
        "teacher": teacher,
        "profile_form": profile_form,
        "password_form": password_form,
        "active_tab": tab,
        "theme": theme,
        "about_content": about_content,
    })
