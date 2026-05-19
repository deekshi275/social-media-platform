from itertools import chain
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import json
from .models import Followers, LikePost, Post, Profile, Story, Comment, Message
from django.db.models import Q

def signup(request):
 try:
    if request.method == 'POST':
        fnm=request.POST.get('fnm')
        emailid=request.POST.get('emailid')
        pwd=request.POST.get('pwd')
        print(fnm,emailid,pwd)
        my_user=User.objects.create_user(fnm,emailid,pwd)
        my_user.save()
        user_model = User.objects.get(username=fnm)
        new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
        new_profile.save()
        if my_user is not None:
            login(request,my_user)
            return redirect('/')
        return redirect('/loginn')
    
        
 except:
        invalid="User already exists"
        return render(request, 'signup.html',{'invalid':invalid})
  
    
 return render(request, 'signup.html')

def loginn(request):
 
  if request.method == 'POST':
        fnm=request.POST.get('fnm')
        pwd=request.POST.get('pwd')
        print(fnm,pwd)
        userr=authenticate(request,username=fnm,password=pwd)
        if userr is not None:
            login(request,userr)
            return redirect('/')
        
 
        invalid="Invalid Credentials"
        return render(request, 'loginn.html',{'invalid':invalid})
               
  return render(request, 'loginn.html')

@login_required(login_url='/loginn')
def logoutt(request):
    logout(request)
    return redirect('/loginn')



@login_required(login_url='/loginn')
def home(request):
    following_users = Followers.objects.filter(follower=request.user.username).values_list('user', flat=True)

    # Remove expired stories older than 12 hours
    expiry_time = timezone.now() - timedelta(hours=12)
    Story.objects.filter(created_at__lt=expiry_time).delete()

    post = Post.objects.filter(Q(user=request.user.username) | Q(user__in=following_users)).order_by('-created_at')
    stories = Story.objects.filter(Q(user=request.user.username) | Q(user__in=following_users)).order_by('-created_at')[:50]
    profile = Profile.objects.get(user=request.user)
    suggestions = Profile.objects.exclude(user=request.user).exclude(user__username__in=following_users).order_by('?')[:5]

    context = {
        'post': post,
        'profile': profile,
        'stories': stories,
        'suggestions': suggestions,
    }
    return render(request, 'main.html',context)
    


@login_required(login_url='/loginn')
def upload(request):

    if request.method == 'POST':
        user = request.user.username
        images = request.FILES.getlist('image_upload')
        caption = request.POST.get('caption', '').strip()

        for image in images:
            if image:
                Post.objects.create(user=user, image=image, caption=caption)

        return redirect('/')
    else:
        return redirect('/')

@login_required(login_url='/loginn')
def upload_story(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('story_image')
        
        if image:
            new_story = Story.objects.create(user=user, image=image)
            new_story.save()
        
        return redirect('/')
    else:
        return redirect('/')

@login_required(login_url='/loginn')
def likes(request, id):
    if request.method == 'GET':
        username = request.user.username
        post = get_object_or_404(Post, id=id)

        like_filter = LikePost.objects.filter(post_id=id, username=username).first()

        if like_filter is None:
            new_like = LikePost.objects.create(post_id=id, username=username)
            post.no_of_likes = post.no_of_likes + 1
        else:
            like_filter.delete()
            post.no_of_likes = post.no_of_likes - 1

        post.save()

        print(post.id)
        return redirect('/#'+id)
    
@login_required(login_url='/loginn')
def add_comment(request, id):
    if request.method == 'POST':
        text = request.POST.get('comment_text', '').strip()
        if text:
            post = get_object_or_404(Post, id=id)
            Comment.objects.create(post=post, user=request.user.username, text=text)
        return redirect('/#' + id)
    return redirect('/')


@login_required(login_url='/loginn')
def messages(request):
    profile = Profile.objects.get(user=request.user)
    # Get all users who have messaged with current user or are followers
    follower_usernames = list(Followers.objects.filter(user=request.user.username).values_list('follower', flat=True))
    
    # Get unique users from message conversations
    all_messages = Message.objects.filter(Q(sender=request.user.username) | Q(receiver=request.user.username))
    message_users = set()
    for msg in all_messages:
        if msg.sender == request.user.username:
            message_users.add(msg.receiver)
        else:
            message_users.add(msg.sender)
    
    all_users = set(follower_usernames) | message_users
    followers = Profile.objects.filter(user__username__in=all_users)
    
    selected_username = request.GET.get('to')
    if selected_username and selected_username not in all_users:
        # Allow messaging any user, not just followers
        try:
            User.objects.get(username=selected_username)
        except:
            selected_username = None
    
    if not selected_username and all_users:
        selected_username = list(all_users)[0]

    conversation = []
    if selected_username:
        conversation = Message.objects.filter(
            Q(sender=request.user.username, receiver=selected_username) |
            Q(sender=selected_username, receiver=request.user.username)
        ).order_by('created_at')

    context = {
        'profile': profile,
        'followers': followers,
        'selected_username': selected_username,
        'conversation': conversation,
    }
    return render(request, 'messages.html', context)


@login_required(login_url='/loginn')
def send_message(request):
    if request.method == 'POST':
        receiver = request.POST.get('receiver')
        body = request.POST.get('body', '').strip()
        if receiver and body:
            # Allow any user to message any other user
            try:
                User.objects.get(username=receiver)
                Message.objects.create(sender=request.user.username, receiver=receiver, body=body)
            except:
                pass
        return redirect('/messages/?to=' + receiver if receiver else '/messages/')
    return redirect('/messages/')


@login_required(login_url='/loginn')
def explore(request):
    post=Post.objects.all().order_by('-created_at')
    profile = Profile.objects.get(user=request.user)

    context={
        'post':post,
        'profile':profile
        
    }
    return render(request, 'explore.html',context)
    
@login_required(login_url='/loginn')
def profile(request,id_user):
    user_object = User.objects.get(username=id_user)
    print(user_object)
    profile = Profile.objects.get(user=request.user)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=id_user).order_by('-created_at')
    user_post_length = len(user_posts)

    follower = request.user.username
    user = id_user
    
    if Followers.objects.filter(follower=follower, user=user).first():
        follow_unfollow = 'Unfollow'
    else:
        follow_unfollow = 'Follow'

    user_followers = len(Followers.objects.filter(user=id_user))
    user_following = len(Followers.objects.filter(follower=id_user))

    latest_conversations = []
    if request.user.username == id_user:
        recent_messages = Message.objects.filter(Q(sender=id_user) | Q(receiver=id_user)).order_by('-created_at')
        conversation_map = {}
        for msg in recent_messages:
            partner = msg.receiver if msg.sender == id_user else msg.sender
            if partner not in conversation_map:
                conversation_map[partner] = msg
        latest_conversations = list(conversation_map.values())

    # Get like information for posts
    user_posts_with_likes = []
    for post in user_posts:
        likes = LikePost.objects.filter(post_id=post.id)
        is_liked = LikePost.objects.filter(post_id=post.id, username=request.user.username).exists()
        comments = Comment.objects.filter(post=post).order_by('-created_at')[:5]
        user_posts_with_likes.append({
            'post': post,
            'likes': likes,
            'is_liked': is_liked,
            'like_count': len(likes),
            'comments': comments,
            'comment_count': Comment.objects.filter(post=post).count()
        })
    
    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_posts_with_likes': user_posts_with_likes,
        'user_post_length': user_post_length,
        'profile': profile,
        'follow_unfollow':follow_unfollow,
        'user_followers': user_followers,
        'user_following': user_following,
        'latest_conversations': latest_conversations,
        'next_url': request.path,
    }
    
    
    if request.user.username == id_user:
        if request.method == 'POST':
            if request.FILES.get('image') == None:
             image = user_profile.profileimg
             bio = request.POST['bio']
             location = request.POST['location']

             user_profile.profileimg = image
             user_profile.bio = bio
             user_profile.location = location
             user_profile.save()
            if request.FILES.get('image') != None:
             image = request.FILES.get('image')
             bio = request.POST['bio']
             location = request.POST['location']

             user_profile.profileimg = image
             user_profile.bio = bio
             user_profile.location = location
             user_profile.save()
            

            return redirect('/profile/'+id_user)
        else:
            return render(request, 'profile.html', context)
    return render(request, 'profile.html', context)

@login_required(login_url='/loginn')
def delete(request, id):
    post = Post.objects.get(id=id)
    if post.user == request.user.username:
        post.delete()
    return redirect('/profile/'+ request.user.username)


@login_required(login_url='/loginn')
def delete_story(request, id):
    if request.method == 'POST':
        story = get_object_or_404(Story, id=id)
        if story.user == request.user.username:
            story.delete()
    return redirect('/')


@login_required(login_url='/loginn')
def delete_message(request, id):
    if request.method == 'POST':
        message = get_object_or_404(Message, id=id)
        redirect_to = '/messages/'
        if message.sender == request.user.username:
            receiver = message.receiver
            message.delete()
            if receiver:
                redirect_to = '/messages/?to=' + receiver
        return redirect(redirect_to)
    return redirect('/messages/')


@login_required(login_url='/loginn')
def search_results(request):
    query = request.GET.get('q')

    users = Profile.objects.filter(user__username__icontains=query)
    posts = Post.objects.filter(caption__icontains=query)

    context = {
        'query': query,
        'users': users,
        'posts': posts,
    }
    return render(request, 'search_user.html', context)

def home_post(request,id):
    post=Post.objects.get(id=id)
    profile = Profile.objects.get(user=request.user)
    context={
        'post':post,
        'profile':profile
    }
    return render(request, 'main.html',context)



def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if Followers.objects.filter(follower=follower, user=user).first():
            delete_follower = Followers.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower = Followers.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user)
    else:
        return redirect('/')