from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.boards_list, name='boards_list'),
    path('create_board/', views.create_board, name='create_board'),
    path('board/<int:board_id>/', views.board_detail, name='board_detail'),
    path('boards/<int:board_id>/update_title/', views.update_board_title, name='update_board_title'),
    path('boards/<int:board_id>/<int:id>/', views.task_detail_view, name='task_detail'),
    path('board/delete/', views.delete_board, name='delete_board'),
    path('update-task-position/', views.update_task_position, name='update_task_position'),
    path('add-task/', views.add_task, name='add_task'),
    path('add-task-list/', views.add_task_list, name='add_task_list'),
    path('update-title', views.update_title, name='update_title'),
    path('delete-list/', views.delete_list, name='delete_list'),
    path('login/', views.loginPage, name='login'),
    path('register/', views.registerPage, name='register'),
    path('me/', views.me, name='me'),
    path('logout/', views.doLogout, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='user/password_reset.html'),
         name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user/password_reset_confirm.html',
        success_url=reverse_lazy('login')
    ), name='password_reset_confirm'),
]