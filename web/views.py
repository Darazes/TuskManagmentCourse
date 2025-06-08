from django.conf import settings
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from web.forms import LoginForm, RegisterForm, StatusForm
from web.models import *

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


def task_detail_view(request, board_id, id):

    board = get_object_or_404(Board, id=board_id, user=request.user)
    task = get_object_or_404(Task, id=id, list__board=board)

    if request.method == 'POST':
        form = StatusForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
    else:
        form = StatusForm(instance=task)

    return render(request, 'tasks/task_detail.html', {'form': form,'board': board, 'task': task})

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
        return redirect('/')
    else:
        return redirect('/')

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
                return redirect('me')
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
    return redirect('login')

