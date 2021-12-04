from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from yatube.settings import COUNT_POSTS_PAGE

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def my_paginator(request, post_list):
    paginator = Paginator(post_list, COUNT_POSTS_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = my_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts_group.all()
    page_obj = my_paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    posts_count = post_list.count()
    page_obj = my_paginator(request, post_list)
    follows = user.following.all()
    following = request.user in [follow.user for follow in follows]
    context = {
        'page_obj': page_obj,
        'posts_count': posts_count,
        'author': user,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    post_count = post.author.posts.count()
    comments = post.comments.all()
    form = CommentForm(
        request.POST or None
    )
    context = {
        'post': post,
        'post_count': post_count,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    context = {'form': form}
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
        'pk': post_id,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    user = request.user
    followers = user.follower.all()
    post_list = Post.objects.filter(
        author__in=[follow.author for follow in followers]
    )
    page_obj = my_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    author = get_object_or_404(User, username=username)
    if not Follow.objects.filter(user=request.user, author=author).exists():
        if request.user != author:
            Follow.objects.create(
                user=request.user,
                author=author,
            )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Дизлайк, отписка"""
    author = get_object_or_404(User, username=username)
    follow_del = get_object_or_404(Follow, user=request.user, author=author)
    follow_del.delete()
    return redirect('posts:profile', username)
