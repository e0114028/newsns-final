import email
from xml.etree.ElementTree import Comment
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from requests import request
from core.formes import RegisterForm
from .models import Profile, Post, LikePost, FollowersCount, Comment
from itertools import chain
import random
from PIL import Image
import PIL.ExifTags as ExifTags
import json
from django.core import serializers
from django.views.generic import CreateView,ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView,DetailView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
# Create your views here.

def get_gps(fname):
    # 画像ファイルを開く --- (*1)
    im = Image.open(fname)
    # EXIF情報を辞書型で得る
    exif = {
        ExifTags.TAGS[k]: v
        for k, v in im._getexif().items()
        if k in ExifTags.TAGS
    }

    # GPS情報を得る --- (*2)
    gps_tags = exif["GPSInfo"]
    gps = {
        ExifTags.GPSTAGS.get(t, t): gps_tags[t]
        for t in gps_tags
    }
    # 緯度経度情報を得る --- (*3)
    def conv_deg(v):
        d = float(v[0])
        m = float(v[1])
        s = float(v[2])
        return d + (m / 60.0) + (s / 3600.0)
    lat = conv_deg(gps["GPSLatitude"])
    lat_ref = gps["GPSLatitudeRef"]
    if lat_ref != "N": lat = 0 - lat
    lon = conv_deg(gps["GPSLongitude"])
    lon_ref = gps["GPSLongitudeRef"]
    if lon_ref != "E": lon = 0 - lon
    return lat, lon

def home(request):
    return('home')

###### 無限スクロール反映前のindex function
@login_required(login_url = 'signin')
def index(request):

    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    user_following_list = []
    feed = []

    user_following = FollowersCount.objects.filter(follower=request.user.username)

    for users in user_following:
        user_following_list.append(users.user)

    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    post_query_set = Post.objects.filter(lat__isnull=False)
    post_json = serializers.serialize("json", post_query_set)
    json.loads(post_json)

    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)
    
    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if ( x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []

    for users in final_suggestions_list:
        username_profile.append(users.id)

    for ids in username_profile:
        profile_lists = Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)

    suggestions_username_profile_list = list(chain(*username_profile_list))
    return render(request, 'index.html', {'user_profile': user_profile, 'posts':feed, 'suggestions_username_profile_list': suggestions_username_profile_list[:4], 'json_posts_for_map': post_json})

class PostView(LoginRequiredMixin, ListView):
# class PostView(ListView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'posts'
    login_url: 'signin'
    paginate_by = 4

    def get_queryset(self):
        user_following_list = []
        user_following = FollowersCount.objects.filter(follower=self.request.user.username)
        for users in user_following:
            user_following_list.append(users.user)
        print(self.request.user.username)
        query_set = Post.objects.filter(Q(user__in=user_following_list)|Q(user=self.request.user.username)).order_by('-created_at')
        return query_set

    def get_context_data(self, **kwargs):
        user_object = User.objects.get(username=self.request.user.username)
        # user_profile = Profile.objects.get(user=user_object)

        user_following_list = []
        feed = []

        user_following = FollowersCount.objects.filter(follower=self.request.user.username)

        for users in user_following:
            user_following_list.append(users.user)

        for usernames in user_following_list:
            feed_lists = Post.objects.filter(user=usernames)
            feed.append(feed_lists)

        feed_list = list(chain(*feed))

        post_query_set = Post.objects.filter(lat__isnull=False)
        post_json = serializers.serialize("json", post_query_set)
        json.loads(post_json)

        # user suggestion starts
        all_users = User.objects.all()
        user_following_all = []

        for user in user_following:
            user_list = User.objects.get(username=user.user)
            user_following_all.append(user_list)
        
        new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
        current_user = User.objects.filter(username=self.request.user.username)
        final_suggestions_list = [x for x in list(new_suggestions_list) if ( x not in list(current_user))]
        random.shuffle(final_suggestions_list)

        username_profile = []
        username_profile_list = []

        for users in final_suggestions_list:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)

        suggestions_username_profile_list = list(chain(*username_profile_list))
        context = super().get_context_data(**kwargs)
        context['suggestions_username_profile_list'] = suggestions_username_profile_list[:4]
        context['json_posts_for_map'] = post_json
        return context

@login_required(login_url='signin')
def upload(request):

    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        lat, lng = get_gps(image)

        new_post = Post.objects.create(user=user, image=image, lat=lat, lng=lng, caption=caption)
        new_post.save()

    return redirect('/')

@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)
        
        username_profile_list = list(chain(*username_profile_list))
    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list},)

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes+1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes-1
        post.save()
        return redirect('/')

    

@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)

    follower = request.user.username
    user = pk


    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'フォロー解除'
    else:
        button_text = 'フォロー'

    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }
    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user)
    else:
        return redirect('/')

@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        
        if request.FILES.get('image') == None:
            image = user_profile.profileimg
        else:
            image = request.FILES.get('image')

        if request.FILES.get('header_image') == None:
            headerimage = user_profile.headerimg
        else:
            headerimage = request.FILES.get('header_image')

 
        bio = request.POST['bio']
        location = request.POST['location']

        user_profile.profileimg = image
        user_profile.headerimg = headerimage
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()
        # if request.FILES.get('image') == None:
        #     image = user_profile.profileimg
        #     bio = request.POST['bio']
        #     location = request.POST['location']

        #     user_profile.profileimg = image
        #     user_profile.bio = bio
        #     user_profile.location = location
        #     user_profile.save()

        # if request.FILES.get('image') != None:
        #     image = request.FILES.get('image')
        #     bio = request.POST['bio']
        #     location = request.POST['location']

        #     user_profile.profileimg = image
        #     user_profile.bio = bio
        #     user_profile.location = location
        #     user_profile.save()
        return redirect('social_book:settings')
    return render(request, 'setting.html', {'user_profile': user_profile})

def signup(request):

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('social_book:signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('social_book:signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                #log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                #create a Profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('social_book:signin')
        else:
            messages.info(request, 'パスワードが違います')
            return redirect('social_book:signup')
        
    else:
        return render(request, 'signup.html')

def signin(request):
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, '存在しません')
            return redirect('social_book:signin')

    else:
        return render(request, 'signin.html')

@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('social_book:signin')


# User = get_user_model()

# def register_page_(request):
#     form = RegisterForm(request.POST())
#     context = {"forms":form}
#     if form.is_valid(self):
#         print(form.cleaned_date)
#         username = form.cleaned_data.get("username")
#         email = form.cleaned_data.get("email")
#         password = form.cleaned_get("password")
#         new_user = User.objects.create_user(username,email,password)

#     render(request,"signup.html",context)

class DetailPost(LoginRequiredMixin, DetailView):
    """投稿詳細ページ"""
    model = Post
    template_name = 'detail.html'



def delete_profileimg(request):
    if request.method == "POST":
        if "delete_profileimg" in request.POST:
        # 以下にstart_buttonがクリックされた時の処理を書いていく
        # UploadImageのインスタンスを取得
            profile_profileimg = get_object_or_404(Profile, id="profileimg_id")
    
    # 画像ファイルの削除
            profile_profileimg.profileimg.delete()
            # profile_profileimg.profileimg.save()
    
    # レコードの削除
            profile_profileimg.delete()

            
    if request.method == "POST":       
        if "delete_headerimg" in request.POST:
            # 以下にfinish_buttonがクリックされた時の処理を書いてく
            # UploadImageのインスタンスを取得
            profile_headerimg= get_object_or_404(Profile, id="headerimg_id")
    
    # 画像ファイルの削除
            profile_headerimg.image.delete()
            # profile_headerimg.image.save()
    
    # レコードの削除
            profile_headerimg.delete()
