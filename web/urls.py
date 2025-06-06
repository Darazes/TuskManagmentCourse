from django.urls import path
from . import views

urlpatterns = [
    path('', views.boards_list, name='boards_list'),
    path('create_board/', views.create_board, name='create_board'),
    path('board/<int:board_id>/', views.board_detail, name='board_detail'),
    path('boards/<int:board_id>/update_title/', views.update_board_title, name='update_board_title'),
    path('board/delete/', views.delete_board, name='delete_board'),
    path('update-task-position/', views.update_task_position, name='update_task_position'),
    path('add-task/', views.add_task, name='add_task'),
    path('add-task-list/', views.add_task_list, name='add_task_list'),
    path('update-title', views.update_title, name='update_title'),
    path('delete-list/', views.delete_list, name='delete_list'),
    path('login/', views.loginPage, name='login'),
    path('register/', views.registerPage, name='register'),
    path('me/', views.me, name='me'),
    path('logout/', views.doLogout, name='logout')
]