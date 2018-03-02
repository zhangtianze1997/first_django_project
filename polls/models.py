# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib import auth

# Create your models here.


class Question(models.Model):
    question_name = models.CharField(max_length=50)
    question_content = models.CharField(max_length=500)
    date = models.DateTimeField('date published')

    def __str__(self):
        return ':'.join([self.question_name, self.question_content])


# class User(models.Model):
#    username = models.CharField(max_length=50)
#    password = models.CharField(max_length=50)

#    def __str__(self):
#        return self.username


class UserInfo(models.Model):
    user = models.ForeignKey(auth.models.User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    number = models.CharField(max_length=10)
    email = models.EmailField()
    major = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    about_me = models.CharField(max_length=200)


class Answer(models.Model):
    user = models.ForeignKey(auth.models.User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=200)
    comment = models.CharField(max_length=200)
    date = models.DateTimeField('date answered')


class AnswerDraft(models.Model):   # 草稿
    user = models.ForeignKey(auth.models.User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=200)


class Log(models.Model):
    action_flag = models.NullBooleanField()
    user = models.CharField(max_length=50)
    time = models.DateTimeField('date logged in')
    action = models.CharField(max_length=50)
    message = models.CharField(max_length=100)


class Friend(models.Model):
    user = models.ForeignKey(auth.models.User, on_delete=models.CASCADE, related_name='user')
    user_follow = models.ForeignKey(auth.models.User, on_delete=models.CASCADE, related_name='user_follow')

