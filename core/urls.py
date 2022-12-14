from django.urls import path
from . import views
from .views import PostView,DetailPost
app_name = 'social_book'

urlpatterns = [
    # path('', views.index, name='index'),
    path('settings', views.settings, name='settings'),
    path('upload', views.upload, name='upload'),
    path('follow', views.follow, name='follow'),
    path('search', views.search, name='search'),
    path('profile/<str:pk>', views.profile, name='profile'),
    path('like-post', views.like_post, name='like-post'),
    path('signup', views.signup, name='signup'),
    path('', PostView.as_view(), name='list'),
    #path('register_page_',views.register_page_,name='register_page_'),
    path('signin', views.signin, name='signin'),
    path('logout', views.logout, name='logout'),
    path('home',views.home,name='home'),
    path('detail/<int:pk>', DetailPost.as_view(), name='detail'),
]

# fuckfuck