from django.urls import path 
from YOYO_APP.views import *

urlpatterns = [
   path('',login_yoyo,name='login'),
   path('register/',register_yoyo,name='register'),
   path('home/',home_yoyo,name='home'),
   path('Brainstormer/',brain_yoyo,name='brain_yoyo'),
   path('Career_guide/',Career_guide_yoyo,name='Career_guide_yoyo'),
   path('Chess_champ/',Chess_champ_yoyo,name='Chess_champ_yoyo'),
   path('Coding_partner/',Coding_partner_yoyo,name='Coding_partner_yoyo'),
   path('ForgotPassword/',ForgotPassword_yoyo,name='ForgotPassword_yoyo'),
   path('Learning_coach/',Learning_coach_yoyo,name='Learning_coach_yoyo'),
   path('NewGem/',NewGem_yoyo,name='NewGem_yoyo'),
   path('Public_Links/',Public_Links_yoyo,name='Public_Links_yoyo'),
   path('SavedInfo/',SavedInfo_yoyo,name='SavedInfo_yoyo'),
   path('Search/',Search_yoyo,name='Search_yoyo'),
   path('Upgrad/',Upgrad_yoyo,name='Upgrad_yoyo'),
   path('Writing_editor/',Writing_editor_yoyo,name='Writing_editor_yoyo'),
   path('Explore_Gem/',Explore_Gem_yoyo,name='Explore_Gem_yoyo'),
   path('logout/',logout_yoyo,name='logout_yoyo'), 
   path("chat/new/", new_chat, name="new_chat"),
   path("chat/", chat_detail, name="chat_detail"),   
   path("chat/<int:chat_id>/", chat_detail, name="chat_detail"),
   path("chat/<int:chat_id>/send/", send_message, name="send_message"),
   path("chat/0/send/", send_message, name="send_message_new"),
]
