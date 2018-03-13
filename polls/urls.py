# -*- coding: utf-8 -*-
from django.urls import path

from .views import *

urlpatterns = [

    path('', index, name='index'),

    path('index/', jump_to_index, name='jump_index'),  # /index/ 跳转到 /
    path('question/', jump_question, name='jump_question'),

    path('question/page<int:page>/', question, name='question'),
    path('question/page<int:page>/<int:question_id>/', question_detail, name='questionDetail'),
    path('question/new/', question_new, name='question_new'),
    path('search/<str:text>/', search, name='search'),
    path('accounts/register/', regist, name='register'),
    path('accounts/login/', login_view, name='login'),
    path('accounts/logout/', log_out, name='logout'),
    path('accounts/<int:user_id>/', profile, name='profile'),
    path('accounts//', jump_to_index),
    path('accounts/pw_change/', change_password, name='change_password'),
    path('img_ajax/', img_ajax, name='user_img_ajax'),
    path('follow_ajax/', follow_ajax, name='follow_ajax'),
    path('get_friend/', get_friend, name='get_friend'),
    path('answer_comment/', comment, name='comment'),
    path('question_collect/', question_collect, name='question_collect')

]
