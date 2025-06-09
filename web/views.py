import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.decorators.http import require_POST, require_http_methods

from web.forms import LoginForm, RegisterForm, StatusForm, UploadFileForm, ContactForm
from web.models import *

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import JsonResponse
import json

def statuses_list(request):
    statuses = Status.objects.all().values('id', 'name')
    return JsonResponse(list(statuses), safe=False)

@require_http_methods(["GET", "POST"])
def task_detail_view(request, board_id, task_id):
    board = get_object_or_404(Board, id=board_id, user=request.user)
    task = get_object_or_404(Task, id=task_id, list__board=board)

    status_form = StatusForm(instance=task)
    file_form = UploadFileForm()

    if request.method == "POST":
        if 'status_submit' in request.POST:
            status_form = StatusForm(request.POST, instance=task)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, "Статус задачи обновлён.")
                return redirect('task_detail_view', board_id=board_id, task_id=task_id)
            else:
                messages.error(request, "Ошибка обновления статуса.")
        elif 'file_submit' in request.POST:
            file_form = UploadFileForm(request.POST, request.FILES)
            if file_form.is_valid():
                task_file = file_form.save(commit=False)
                task_file.task = task
                task_file.save()
                messages.success(request, "Файл успешно загружен.")
                return redirect('task_detail_view', board_id=board_id, task_id=task_id)
            else:
                messages.error(request, f"Ошибка загрузки файла: {file_form.errors.as_text()}")

    return render(request, 'tasks/task_detail.html', {
        'board': board,
        'task': task,
        'status_form': status_form,
        'file_form': file_form,
    })

@require_POST
@login_required
@csrf_protect
def delete_file(request):
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        if not file_id:
            return JsonResponse({'success': False, 'error': 'ID файла не передан'})

        # Получаем объект файла
        file_obj = TaskFile.objects.filter(id=file_id).first()
        if not file_obj:
            return JsonResponse({'success': False, 'error': 'Файл не найден'})

        # Проверка прав доступа - пример, что файл принадлежит пользователю или задаче пользователя
        # Замените логику проверки доступа согласно вашей модели данных
        if file_obj.task.list.board.user != request.user:
            return JsonResponse({'success': False, 'error': 'Нет прав на удаление этого файла'})

        # Удаляем файл из файловой системы
        file_path = file_obj.file.path
        if os.path.isfile(file_path):
            os.remove(file_path)

        # Удаляем запись из БД
        file_obj.delete()

        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class TaskSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        status_id = request.GET.get('status', '').strip()

        tasks = Task.objects.all()

        if query:
            tasks = tasks.filter(title__icontains=query)

        if status_id:
            tasks = tasks.filter(status_id=status_id)

        tasks = tasks.select_related('status', 'list__board')[:10]

        results = [{
            'id': task.id,
            'boardId': task.list.board.id,
            'title': task.title,
            'status_name': task.status.name if task.status else None,
        } for task in tasks]

        return JsonResponse(results, safe=False)

@login_required(login_url='login/')
def boards_list(request):
    boards = Board.objects.filter(user=request.user)
    return render(request, 'boards/board_list.html', {'boards': boards})

@login_required
def create_board(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            Board.objects.create(title=title, user=request.user)
        return redirect('/boards')
    else:
        return redirect('/boards')

@login_required
def delete_board(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            board_id = data.get('board_id')
            board = Board.objects.get(id=board_id, user=request.user)
            board.delete()
            return JsonResponse({'success': True})
        except Board.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Доска не найдена или доступ запрещён'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id, user=request.user)
    return render(request, 'boards/board_detail.html', {'board': board})


@csrf_exempt
def update_task_position(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_list_id = data.get('new_list_id')

        from .models import Task, List

        try:
            task = Task.objects.get(id=task_id)
            old_list = task.list  # запоминаем старый список
            new_list = List.objects.get(id=new_list_id)

            # Обновляем связь задачи с новым списком
            task.list = new_list

            # Устанавливаем позицию задачи в новом списке
            last_task = Task.objects.filter(list=new_list).order_by('-position').first()
            if last_task is None:
                task.position = 0
            else:
                task.position = last_task.position + 1

            task.save()

            # Считаем количество задач в старом списке
            tasks_left = Task.objects.filter(list=old_list).count()

            return JsonResponse({'status': 'ok', 'tasks_left': tasks_left})
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)
        except List.DoesNotExist:
            return JsonResponse({'error': 'List not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def add_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        list_id = data.get('list_id')
        if not title or not list_id:
            return JsonResponse({'error': 'Не переданы обязательные данные'}, status=400)
        try:
            task_list = List.objects.get(id=list_id)  # поменяйте на вашу модель списка
        except List.DoesNotExist:
            return JsonResponse({'error': 'Список не найден'}, status=404)
        task = Task.objects.create(title=title, description=description, list=task_list)
        return JsonResponse({'task_id': task.id})
    return JsonResponse({'error': 'Неверный метод'}, status=405)

@csrf_exempt
def add_task_list(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title')
        board_id = data.get('board_id')  # Получаем id доски из запроса

        if not title or not board_id:
            return JsonResponse({'error': 'Missing title or board_id'}, status=400)

        try:
            board = Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            return JsonResponse({'error': 'Board not found'}, status=404)

        task_list = List.objects.create(title=title, board=board)

        return JsonResponse({'id': task_list.id, 'title': task_list.title})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@require_POST
def delete_task(request):
    import json
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        if not task_id:
            return JsonResponse({'success': False, 'error': 'Не передан task_id'})

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Задача не найдена'})

        task.delete()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def delete_list(request):
    import json
    try:
        data = json.loads(request.body)
        list_id = data.get('list_id')
        if not list_id:
            return JsonResponse({'success': False, 'error': 'Не передан list_id'})

        try:
            task_list = List.objects.get(id=list_id)
        except List.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Список не найден'})

        task_list.delete()  # удалит список и связанные задачи, если установлено каскадное удаление
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt  # отключаем CSRF для простоты, но лучше настроить CSRF-токен в реальных проектах
def update_title(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            old_title = data.get('oldTitle')
            new_title = data.get('newTitle', 'Без названия').strip() or 'Без названия'

            task = List.objects.filter(title=old_title).first()
            if task:
                task.title = new_title
                task.save()
                return JsonResponse({'status': 'ok'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Заголовок не найден'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Неверный метод'}, status=405)


@require_POST
@csrf_exempt  # Только если вы не используете JS с CSRF токеном в headers!
def update_board_title(request, board_id):
    try:
        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        if not new_title:
            return JsonResponse({'error': 'Пустое название'}, status=400)

        board = get_object_or_404(Board, id=board_id)
        board.title = new_title
        board.save()
        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный JSON'}, status=400)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Получаем данные из формы
            name = form.cleaned_data['name']
            message = form.cleaned_data['message']
            sender = form.cleaned_data['email']
            recipient = [ 'gamebattle936@gmail.com' ]  # адрес для получения писем

            # Отправляем email
            send_mail(name, message, sender, recipient)
            messages.success(request, 'Спасибо за ваше сообщение! Мы учётём Ваши пожелания.')
            return redirect('/contact')
    else:
        form = ContactForm()
    return render(request, 'info/contact.html', {'form': form})

def loginPage(request):

    # инициализируем объект класса формы
    form = LoginForm()

    # обрабатываем случай отправки формы на этот адрес
    if request.method == 'POST':

        # заполянем объект данными, полученными из запроса
        form = LoginForm(request.POST)

        # проверяем валидность формы
        if form.is_valid():
            # пытаемся авторизовать пользователя
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                # если существует пользователь с таким именем и паролем,
                # то сохраняем авторизацию и делаем редирект
                login(request, user)
                return redirect('/')
            else:
                # иначе возвращаем ошибку
                form.add_error(None, 'Неверные данные!')

    return render(request, 'user/login.html', {'form': form})

def registerPage(request):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Отправка приветственного письма
            send_mail(
                subject='Добро пожаловать!',
                message='Спасибо за регистрацию на нашем сайте.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return redirect('login')

    return render(request, 'user/registration.html', {'form': form})


def me(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'user/me.html', {'user': request.user})

def doLogout(request):
    logout(request)
    return redirect('/')


def main(request):
    return render(request, 'info/main.html', )