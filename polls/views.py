# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django import forms
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout, hashers
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.core import serializers
from datetime import timedelta
import re
import time

from .models import *


def index(req):
    if req.session.get('user') is None:
        return render(req, 'index.html', {'user_none': '登录'}, RequestContext(req))

    total = Question.objects.count()

    if req.session.get('register'):  # 用户注册成功后的跳转给出注册成功提示
        data = {'username': req.session['user'], 'user_id': User.objects.get(username=req.session['user']).id,
                'question_total': total, 'register_info': req.session['register']}
        del req.session['register']
        return render(req, 'index.html', data)

    data = {'username': req.session['user'], 'user_id': User.objects.get(username=req.session['user']).id,
            'question_total': total}
    return render(req, 'index.html', data)


def jump_to_index(req):
    return HttpResponseRedirect('http://localhost:8000/')


@login_required()
def jump_question(req):
    return HttpResponseRedirect('page1/')


@login_required()
def question(req, page):
    if req.is_ajax() and req.method == 'GET':  # 删除问题ajax
        question_id_list = req.GET.getlist('id')
        for question_id in question_id_list:
            Question.objects.get(id=question_id).delete()

        return JsonResponse({'result': 'success'})

    question_total = Question.objects.count()
    if question_total > 0:
        pages_total = (question_total - 1) // 10 + 1  # 每页显示10个题目
        if page > pages_total or page < 1:
            return HttpResponseRedirect('../page1/')

        question_list = Question.objects.all().order_by('-id')[(page - 1) * 10:page * 10]
        check_list = []
        for question in question_list:
            try:
                Answer.objects.get(question_id=question.id, user_id=User.objects.get(username=req.session['user']).id)
                check_list.append(1)
            except ObjectDoesNotExist:
                try:
                    AnswerDraft.objects.get(question_id=question.id,
                                            user_id=User.objects.get(username=req.session['user']).id)
                    check_list.append(-1)
                except ObjectDoesNotExist:
                    check_list.append(0)

        if req.session['user'] == 'admin':
            context = {'question_list': question_list, 'username': req.session['user'],
                       'user_id': User.objects.get(username=req.session['user']).id,
                       'local_page': page, 'total': question_total, 'pages': pages_total}
            return render(req, 'polls/question_admin.html', context)

        context = {'question_list': question_list, 'check_list': check_list, 'username': req.session['user'],
                   'user_id': User.objects.get(username=req.session['user']).id,
                   'local_page': page, 'total': question_total, 'pages': pages_total}
        return render(req, 'polls/question.html', context)
    else:
        return HttpResponseRedirect('../../index/')


@login_required()
def question_new(req):
    if req.session['user'] == 'admin':
        if req.is_ajax() and req.method == 'POST':
            question_name = req.POST.get('name')
            question_content = re.sub('\r\n', '<br>', req.POST.get('content'))
            try:
                Question.objects.get(question_name=question_name, question_content=question_content)
                return JsonResponse({'result': '问题重复！'})
            except ObjectDoesNotExist:
                Question.objects.create(question_name=question_name, question_content=question_content,
                                        date=timezone.now())
                try:
                    Question.objects.get(question_name=question_name, question_content=question_content)
                    return JsonResponse({'result': 'success'})
                except ObjectDoesNotExist:
                    return JsonResponse({'result': '无法添加问题！'})
        else:
            context = {'username': req.session['user'],
                       'user_id': User.objects.get(username=req.session['user']).id, }
            return render(req, 'polls/detail_new.html', context)

    else:
        return HttpResponseRedirect('../page1/')


@login_required()
def question_detail(req, question_id, page):
    user_id = User.objects.get(username=req.session['user']).id

    if req.session['user'] == 'admin':

        if req.is_ajax() and req.method == 'POST':
            question_name = req.POST.get('name')
            question_content = re.sub('\r\n', '<br>', req.POST.get('content'))
            question = Question.objects.get(id=question_id)
            question.question_name = question_name
            question.question_content = question_content
            question.save()
            answer_list = Answer.objects.filter(question_id=question_id)
            for answer in answer_list:
                AnswerDraft.objects.create(question_id=question_id, user_id=answer.user_id,
                                           answer_text=answer.answer_text)
            answer_list.delete()
            question_content = re.sub('<br>', ' ', question_content)
            if len(question_content) > 20:
                question_content = question_content[0:20] + '...'
            ActionLog(user_id=1, action='revise', object_id=question_id, object_content=question_content,
                      time=int(time.time())).save()
            return JsonResponse({'result': 'success'})
        elif req.is_ajax() and req.method == 'GET':
            question = Question.objects.get(id=question_id)
            return JsonResponse({'result': 'success', 'question_name': question.question_name,
                                 'question_content': question.question_content})

        question = get_object_or_404(Question, pk=question_id)
        try:
            answer_list = Answer.objects.filter(question_id=question_id).order_by("comment", "date")
            answer_list_final = []

            for obj in answer_list:
                obj.username = User.objects.get(id=obj.user_id).username
                try:
                    obj.name = UserInfo.objects.get(user_id=obj.user_id).name
                except ObjectDoesNotExist:
                    pass
                try:
                    obj.number = UserInfo.objects.get(user_id=obj.user_id).number
                except ObjectDoesNotExist:
                    pass
                answer_list_final.append(obj)
            context = {'question': question, 'username': req.session['user'],
                       'user_id': user_id,
                       'answer_list': answer_list_final}
            return render(req, 'polls/detail_admin.html', context)

        except ObjectDoesNotExist:

            context = {'question': question, 'username': req.session['user'],
                       'user_id': user_id,
                       }
            return render(req, 'polls/detail_admin.html', context)

    else:  # 用户页面
        try:  # 如果用户已经回答该问题
            obj_answer = Answer.objects.get(question_id=question_id,
                                            user_id=user_id)
            question = get_object_or_404(Question, pk=question_id)
            context = {'question': question, 'username': req.session['user'],
                       'user_id': user_id,
                       'answer': obj_answer.answer_text, 'comment': obj_answer.comment, 'check': '已提交'}
            return render(req, 'polls/detail.html', context)

        except ObjectDoesNotExist:

            if req.method == "POST":
                flag = req.POST.get('flag', '')
                answer = re.sub('\r\n', '<br>', req.POST.get('answer', ''))  # 将提交的内容中的换行替换保存
                if flag == 'save':
                    obj_draft, created = AnswerDraft.objects.update_or_create(question_id=question_id,
                                                                              user_id=User.objects.get(
                                                                                  username=req.session['user']).id,
                                                                              defaults={'answer_text': answer})
                    question = get_object_or_404(Question, pk=question_id)
                    context = {'question': question, 'username': req.session['user'],
                               'user_id': user_id,
                               'draft': obj_draft.answer_text, 'info_save': '草稿保存成功！'}
                    return render(req, 'polls/detail.html', context)
                else:
                    try:
                        Answer.objects.get(question_id=question_id,
                                           user_id=user_id)
                        return HttpResponseRedirect('../' + question_id + '/')
                    except ObjectDoesNotExist:
                        Answer.objects.create(question_id=question_id,
                                              user_id=user_id,
                                              date=timezone.now(), answer_text=answer)
                    try:  # 删除数据库中草稿
                        AnswerDraft.objects.get(question_id=question_id,
                                                user_id=user_id).delete()
                    except ObjectDoesNotExist:
                        pass
                    question = get_object_or_404(Question, pk=question_id)
                    context = {'question': question, 'username': req.session['user'],
                               'user_id': user_id, 'answer': answer,
                               'check': '已提交', 'info_submit': '提交成功！'}
                    question_content = Question.objects.get(id=question_id).question_content
                    if len(question_content) > 20:
                        question_content = question_content[0:20] + '...'
                    ActionLog(user_id=user_id, action='submit', object_id=question_id,
                              object_content=question_content, time=int(time.time())).save()
                    return render(req, 'polls/detail.html', context)

            try:
                obj_draft = AnswerDraft.objects.get(question_id=question_id,
                                                    user_id=user_id)
            except ObjectDoesNotExist:
                question = get_object_or_404(Question, pk=question_id)
                context = {'question': question, 'username': req.session['user'],
                           'user_id': user_id, }
                return render(req, 'polls/detail.html', context)

            question = get_object_or_404(Question, pk=question_id)
            context = {'question': question, 'username': req.session['user'],
                       'user_id': user_id, 'draft': obj_draft.answer_text}
            return render(req, 'polls/detail.html', context)


class UserForm(forms.Form):
    username = forms.CharField(label='用户名', max_length=50)
    password = forms.CharField(label='密码', widget=forms.PasswordInput())


def regist(req):  # 实现用户注册
    if req.is_ajax():
        if req.method == 'GET':
            username = req.GET.get('username')
            try:
                User.objects.get(username=username)
                return JsonResponse({'username': username})
            except ObjectDoesNotExist:
                return JsonResponse({'username': ''})

    if req.method == 'POST':
        userform = UserForm(req.POST)
        if userform.is_valid():
            username = userform.cleaned_data['username']
            password = userform.cleaned_data['password']

            if username == '' or password == '':
                return render(req, 'polls/signup.html', {'error_blank': '请填写用户名或密码！'})

            result = User.objects.filter(username=username)
            if result:
                return render(req, 'polls/signup.html', {'error_exist': '用户名已存在！'})

            User.objects.create_user(username=username, password=password)
            if User.objects.filter(username=username):  # 注册成功后对其登录并创建对应信息数据记录
                UserInfo.objects.create(user_id=User.objects.get(username=username).id)
                user = authenticate(username=username, password=password)
                login(req, user)
                Log(action_flag=True, user=user, time=timezone.now(), action='login', message='登陆成功').save()
                req.session['user'] = username  # 跳转后利用session给出一个提示
                req.session['register'] = '注册成功!'
                return HttpResponseRedirect('../../')

        else:
            return render(req, 'polls/signup.html', {'error_submit': '请检查输入！'})

    else:
        userform = UserForm()
    return render(req, 'polls/signup.html', {'userform': userform}, RequestContext(req))


def login_view(req):
    if req.user.is_authenticated:
        return HttpResponseRedirect('../../')

    if req.method == 'POST':
        username = req.POST.get('username', '')
        password = req.POST.get('password', '')
        login_remember = req.POST.get('chkRemember', '')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(req, user)
            Log(action_flag=True, user=user, time=timezone.now(), action='login', message='登陆成功').save()
            req.session['user'] = username
            if login_remember:
                req.session.set_expiry(60 * 60 * 24 * 15)  # session 有效期15天
            else:
                req.session.set_expiry(60 * 60 * 2)

            if req.session.get('jump'):
                jump_page = req.session.get('jump')
                del req.session['jump']
                return HttpResponseRedirect(jump_page)
            return HttpResponseRedirect('../../index/')
        else:
            Log(action_flag=False, user='None', time=timezone.now(), action='login',
                message='登陆失败,登陆名{}'.format(username)).save()

            return render(req, 'polls/signin.html', {'error': "用户名或密码错误"})

    if req.GET.get('next', ''):  # ?next=跳转
        req.session['jump'] = req.GET.get('next', '')
    return render(req, 'polls/signin.html', {}, RequestContext(req))


@login_required()
def log_out(req):
    try:
        del req.session['user']
    except KeyError:
        pass

    logout(req)
    return HttpResponseRedirect('../../index/')


@login_required()
def profile(req, user_id):
    username = req.session['user']
    following_total = Friend.objects.filter(user_id=user_id).count()
    followed_total = Friend.objects.filter(user_follow_id=user_id).count()
    following_pages_total = (following_total - 1) // 9 + 1
    following_list = []
    following_list_id = Friend.objects.filter(user_id=user_id)[0:9]
    for obj in following_list_id:
        try:
            user_obj = UserInfo.objects.get(user_id=obj.user_follow_id)
            try:
                Friend.objects.get(user_id=User.objects.get(username=username).id, user_follow_id=obj.user_follow_id)
                user_obj.relation = 'follow'
            except ObjectDoesNotExist:
                pass
            user_obj.username = User.objects.get(id=obj.user_follow_id).username
            following_list.append(user_obj)
        except ObjectDoesNotExist:
            userinfo_model = UserInfo.objects.all()[:1]
            userinfo_model.user_id = obj.user_follow_id
            try:
                Friend.objects.get(user_id=User.objects.get(username=username).id, user_follow_id=obj.user_follow_id)
                userinfo_model.relation = 'follow'
            except ObjectDoesNotExist:
                pass
            userinfo_model.username = User.objects.get(id=obj.user_follow_id).username
            following_list.append(userinfo_model)

    followed_pages_total = (followed_total - 1) // 9 + 1
    followed_list = []
    followed_list_id = Friend.objects.filter(user_follow_id=user_id)[0:9]
    for obj in followed_list_id:
        try:
            user_obj = UserInfo.objects.get(user_id=obj.user_id)
            try:
                Friend.objects.get(user_id=User.objects.get(username=username).id, user_follow_id=obj.user_id)
                user_obj.relation = 'follow'
            except ObjectDoesNotExist:
                pass
            user_obj.username = User.objects.get(id=obj.user_id).username
            followed_list.append(user_obj)
        except ObjectDoesNotExist:
            try:
                Friend.objects.get(user_id=User.objects.get(username=username).id, user_follow_id=obj.user_id)
                obj.relation = 'follow'
            except ObjectDoesNotExist:
                pass
            obj.username = User.objects.get(id=obj.user_id).username
            followed_list.append(obj)

    if user_id == User.objects.get(username=username).id:  # 个人信息页面

        if req.is_ajax() and req.method == 'POST':
            name = req.POST.get('name', '')
            number = req.POST.get('number', '')
            gender = req.POST.get('profileGender', '')
            address = req.POST.get('address', '')
            phone = req.POST.get('phone', '')
            major = req.POST.get('major', '')
            email = req.POST.get('email', '')
            about_me = re.sub('\r\n', '<br>', req.POST.get('about_me', ''))
            qq = req.POST.get('qq', '')
            github = req.POST.get('github', '')
            infolist = {'name': name, 'number': number, 'gender': gender, 'address': address, 'phone': phone,
                        'major': major, 'email': email, 'about_me': about_me, 'qq': qq, 'github': github}
            UserInfo.objects.update_or_create(user_id=user_id, defaults=infolist)
            infolist['username'] = username
            infolist['user_id'] = User.objects.get(username=req.session['user']).id
            infolist['page_user_id'] = user_id
            return JsonResponse(infolist)

        else:
            obj_profile = UserInfo.objects.get(user_id=user_id)
            question_collect_list = list(eval(obj_profile.collect))
            question_list = []
            for question_id in question_collect_list:
                try:
                    question_list.append(Question.objects.get(id=question_id))
                except ObjectDoesNotExist:
                    pass
            action_list = ActionLog.objects.filter(user_id=user_id).order_by("-id")[0:6]
            infolist = {'name': obj_profile.name, 'number': obj_profile.number, 'gender': obj_profile.gender,
                        'address': obj_profile.address, 'visit': obj_profile.visit,
                        'phone': obj_profile.phone, 'major': obj_profile.major, 'email': obj_profile.email,
                        'about_me': obj_profile.about_me, 'qq': obj_profile.qq, 'github': obj_profile.github,
                        'username': username, 'user_id': User.objects.get(username=req.session['user']).id,
                        'question_list': question_list, 'question_count': len(question_collect_list),
                        'following_total': following_total, 'following_pages_total': following_pages_total,
                        'following_list': following_list, 'followed_pages_total': followed_pages_total,
                        'followed_total': followed_total, 'followed_list': followed_list, 'page_user_id': user_id,
                        'answer_total': Answer.objects.filter(user_id=user_id).count(), 'action_list': action_list}
            return render(req, 'polls/userinfo.html', infolist)

    else:  # 访问非自己页面
        try:
            Friend.objects.get(user_id=User.objects.get(username=username).id, user_follow_id=user_id)
            relation_flag = 1
        except ObjectDoesNotExist:
            relation_flag = 0

        obj_profile = UserInfo.objects.get(user_id=user_id)
        obj_profile.visit += 1
        obj_profile.save()
        action_list = ActionLog.objects.filter(user_id=user_id).order_by("-id")[0:6]
        infolist = {'name': obj_profile.name, 'number': obj_profile.number, 'gender': obj_profile.gender,
                    'address': obj_profile.address, 'phone': obj_profile.phone, 'major': obj_profile.major,
                    'email': obj_profile.email, 'qq': obj_profile.qq, 'github': obj_profile.github,
                    'about_me': obj_profile.about_me, 'visit': obj_profile.visit, 'username': username,
                    'user_id': User.objects.get(username=req.session['user']).id,
                    'page_user_name': User.objects.get(id=user_id).username,
                    'following_total': following_total, 'following_pages_total': following_pages_total,
                    'following_list': following_list,
                    'followed_pages_total': followed_pages_total, 'followed_total': followed_total,
                    'followed_list': followed_list, 'answer_total': Answer.objects.filter(user_id=user_id).count(),
                    'page_user_id': user_id, 'relation': relation_flag, 'action_list': action_list
                    }
        return render(req, 'polls/userinfo_other.html', infolist)


@csrf_exempt
def img_ajax(req):
    if req.is_ajax():
        if req.method == 'POST':
            return JsonResponse({'result': "success"})


def follow_ajax(req):
    if req.is_ajax() and req.method == 'GET':
        flag = req.GET.get('flag')
        if flag == 'cancel':
            try:
                obj = Friend.objects.get(user_id=req.GET.get('user_id'), user_follow_id=req.GET.get('follow_id'))
                obj.delete()
            except ObjectDoesNotExist:
                pass
            return JsonResponse({'result': 'success'})

        else:
            try:
                Friend.objects.get(user_id=req.GET.get('user_id'), user_follow_id=req.GET.get('follow_id'))
            except ObjectDoesNotExist:
                obj = Friend(user_id=req.GET.get('user_id'), user_follow_id=req.GET.get('follow_id'))
                obj.save()
                if UserInfo.objects.get(user_id=req.GET.get('follow_id')).name:
                    ActionLog(user_id=req.GET.get('user_id'), action='follow', object_id=req.GET.get('follow_id'),
                              object_content=UserInfo.objects.get(user_id=req.GET.get('follow_id')).name,
                              time=int(time.time())).save()
                else:
                    ActionLog(user_id=req.GET.get('user_id'), action='follow', object_id=req.GET.get('follow_id'),
                              object_content=User.objects.get(id=req.GET.get('follow_id')).username,
                              time=int(time.time())).save()
            return JsonResponse({'result': 'success'})


def get_friend(req):
    if req.is_ajax() and req.method == 'GET':
        flag = req.GET.get('flag')
        page = int(req.GET.get('page'))
        username = req.GET.get('user_name')
        if flag == 'followed':
            followed_list = []
            flag_list = []
            i = 0
            followed_list_id = Friend.objects.filter(user_follow_id=req.GET.get('user_id'))[(page - 1) * 9:page * 9]
            for obj in followed_list_id:
                try:
                    user_obj = UserInfo.objects.get(user_id=obj.user_id)
                    if User.objects.get(username=username).id == obj.user_id:
                        flag_list.append({'relation': 'self'})
                    else:
                        try:
                            Friend.objects.get(user_id=User.objects.get(username=username).id,
                                               user_follow_id=obj.user_id)
                            flag_list.append({'relation': 'follow'})
                        except ObjectDoesNotExist:
                            flag_list.append({})
                    flag_list[i]['username'] = User.objects.get(id=obj.user_id).username

                    followed_list.append(model_to_dict(user_obj))
                    i = i + 1
                except ObjectDoesNotExist:
                    if User.objects.get(username=username).id == obj.user_id:
                        flag_list.append({'relation': 'self'})
                    else:
                        try:
                            Friend.objects.get(user_id=User.objects.get(username=username).id,
                                               user_follow_id=obj.user_id)
                            flag_list.append({'relation': 'follow'})
                        except ObjectDoesNotExist:
                            flag_list.append({})
                    flag_list[i]['username'] = User.objects.get(id=obj.user_id).username

                    followed_list.append(model_to_dict(obj))
                    i = i + 1
            return JsonResponse({'result': 'success', 'followed_list': followed_list, 'flag_list': flag_list})

        elif flag == 'following':
            following_list = []
            flag_list = []
            i = 0
            following_list_id = Friend.objects.filter(user_id=req.GET.get('user_id'))[(page - 1) * 9:page * 9]
            for obj in following_list_id:
                try:
                    user_obj = UserInfo.objects.get(user_id=obj.user_follow_id)
                    if User.objects.get(username=username).id == obj.user_follow_id:
                        flag_list.append({'relation': 'self'})
                    else:
                        try:
                            Friend.objects.get(user_id=User.objects.get(username=username).id,
                                               user_follow_id=obj.user_follow_id)
                            flag_list.append({'relation': 'follow'})
                        except ObjectDoesNotExist:
                            flag_list.append({})
                    flag_list[i]['username'] = User.objects.get(id=obj.user_follow_id).username

                    following_list.append(model_to_dict(user_obj))
                    i = i + 1
                except ObjectDoesNotExist:
                    if User.objects.get(username=username).id == obj.user_id:
                        flag_list.append({'relation': 'self'})
                    else:
                        try:
                            Friend.objects.get(user_id=User.objects.get(username=username).id,
                                               user_follow_id=obj.user_follow_id)
                            flag_list.append({'relation': 'follow'})
                        except ObjectDoesNotExist:
                            flag_list.append({})
                    flag_list[i]['username'] = User.objects.get(id=obj.user_follow_id).username

                    following_list.append(model_to_dict(obj))
                    i = i + 1
            return JsonResponse({'result': 'success', 'following_list': following_list, 'flag_list': flag_list})


@csrf_exempt
def comment(req):
    if req.is_ajax() and req.method == "POST":
        text = req.POST.get('text')
        question_id = req.POST.get('id')
        answer_model = Answer.objects.get(id=question_id)
        answer_model.comment = text
        answer_model.save()
        question_content = Question.objects.get(id=question_id).question_content
        if len(question_content) > 20:
            question_content = question_content[0:20] + '...'

        ActionLog(user_id=1, action='comment', object_id=question_id, object_content=question_content,
                  time=int(time.time())).save()
        return JsonResponse({'result': 'success'})


@login_required()
def search(req, text):
    username = req.session['user']
    question_list = Question.objects.filter(question_content__icontains=text)
    user_list = User.objects.filter(username__icontains=text)
    user_list_final = []
    name_list = UserInfo.objects.filter(name__icontains=text)
    name_list_final = []

    for obj in user_list:
        try:
            info = UserInfo.objects.get(user_id=obj.id)
            obj.name = info.name
            obj.major = info.major
            user_list_final.append(obj)
        except ObjectDoesNotExist:
            user_list_final.append(obj)

    for obj in name_list:
        obj.username = User.objects.get(id=obj.user_id).username
        name_list_final.append(obj)

    context = {'username': username, 'user_id': User.objects.get(username=username).id, 'question_list': question_list,
               'user_list': user_list_final, 'name_list': name_list_final, 'search_text': text}

    return render(req, 'polls/search.html', context)


@csrf_exempt
def change_password(req):
    if req.is_ajax() and req.method == 'POST':
        user_id = req.POST.get('user_id')
        pw_old = req.POST.get('pw_old')
        pw_new = req.POST.get('pw_new')
        user = User.objects.get(id=user_id)

        if hashers.check_password(pw_old, user.password):
            user.set_password(pw_new)
            user.save()
            user_new = authenticate(username=user.username, password=pw_new)  # 修改密码后重新登录用户
            login(req, user_new)
            Log(action_flag=True, user=user_new, time=timezone.now(), action='change_password', message='修改成功').save()
            req.session['user'] = user.username

            return JsonResponse({'result': 'success'})
        else:
            return JsonResponse({'result': '原密码错误！'})


def question_collect(req):
    if req.is_ajax() and req.method == 'GET':
        if req.GET.get('flag') == 'collect':
            collect_list = req.GET.getlist('id')
            user_id = req.GET.get('user_id')
            user = UserInfo.objects.get(user_id=user_id)
            past_list = list(eval(user.collect))
            past_len = len(past_list)
            past_list.extend(collect_list)
            past_list = list(set(past_list))
            past_list.sort()
            if past_len - len(past_list) == 0:
                return JsonResponse({'result': 'success'})
            else:
                user.collect = str(past_list)
                user.save()
                ActionLog(user_id=user_id, action='collect', object_id=len(past_list) - past_len, object_content='',
                          time=int(time.time())).save()
                return JsonResponse({'result': 'success'})
        elif req.GET.get('flag') == 'delete':
            collect_list = req.GET.getlist('id')
            user_id = req.GET.get('user_id')
            user = UserInfo.objects.get(user_id=user_id)
            past_list = list(eval(user.collect))
            for question_id in collect_list:
                try:
                    past_list.remove(question_id)
                except ValueError:
                    pass
            list_len = len(past_list)
            question_list = []
            for question_id in past_list:
                try:
                    obj = Question.objects.get(id=question_id)
                    obj.date = obj.date + timedelta(hours=8)
                    question_list.append(obj)
                except ObjectDoesNotExist:
                    pass
            question_list = serializers.serialize("json", question_list)
            user.collect = str(past_list)
            user.save()

            return JsonResponse({'result': 'success', 'question_list': question_list, 'len': list_len})
