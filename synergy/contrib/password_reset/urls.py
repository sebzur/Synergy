from django.conf.urls.defaults import *
from django.contrib.auth.views import password_reset, password_reset_done, password_reset_confirm, password_reset_complete
from django.conf import settings
from django.contrib.auth.forms import SetPasswordForm
from importlib import import_module

try:
    passwd_reset_form = getattr(import_module(settings.PASSWORD_RESET_FORM[0]),settings.PASSWORD_RESET_FORM[1])
except:
    passwd_reset_form = SetPasswordForm

urlpatterns = patterns('',
     url(r'^accounts/password/reset/$', password_reset, {  'template_name': 'password_reset/password_reset.html',
                                                        'email_template_name': 'password_reset/password_reset_email.html',
                                                        'post_reset_redirect': '/accounts/password/done/'}, name='password_reset'),
     url(r'^accounts/password/done/$', password_reset_done, {'template_name': 'password_reset/password_reset_done.html'}, name='password_reset_done'),
     url(r'^accounts/password/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm, {'template_name': 'password_reset/password_reset_confirm.html', 'post_reset_redirect': '/accounts/password/complete/', 'set_password_form': passwd_reset_form}, name='password_reset_confirm'),
     url(r'^accounts/password/complete/$', password_reset_complete, {'template_name': 'password_reset/password_reset_complete.html'}, name='password_reset_complete'),
)
