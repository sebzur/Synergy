# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import get_model
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib.auth.models import User
from django.db.models import Q

import models
import itertools


#filter queryste according to flags
def filter_queryset(queryset, user, flag_name):
    
    
    app_name = queryset.model._meta.app_label
    model_name = queryset.model._meta.object_name.lower()
                                                  
    filtr = {'flag__content_type__app_label__exact':app_name,
             'flag__content_type__model__exact': model_name,
             'flag__flag_type__slug__exact': flag_name,}                                                 
    
    if not user.is_authenticated():
        has_model_flag = get_model('cos','VisitorFlag').objects.filter(anonymous__exact=True, flag__object_id__exact=None, **filtr).exists()
        anonymous_objects = get_model('cos','VisitorFlag').objects.filter(anonymous__exact=True,**filtr).                                                                                               exclude(flag__object_id__exact=None).values_list('flag__object_id', flat=True)
      
        #XOR dla anonymos
        if has_model_flag:
            return queryset.exclude(id__in=anonymous_objects)
        return queryset.filter(id__in=anonymous_objects)
        
      
    #zalogowany 
    has_user_model_flag = get_model('cos','UserFlag').objects.filter(user__exact=user, flag__object_id__exact=None, **filtr).exists()
    user_objects= get_model('cos','UserFlag').objects.filter(user__exact=user, **filtr).exclude(flag__object_id__exact=None).values_list('flag__object_id', flat=True)

    #user ma pelne prawo do modelu i nie ma nic zabronionego - a wiec ma prawo ZAWSZE i nie ma co pytac dalej
    if has_user_model_flag and not user_objects.exists():
        return queryset
        
    user_allowed=[]
    user_forbiden=[]
    #user ma prawo do obiektów a nie ma do modelu - ma do nich prawo ZAWSZE:
    if not has_user_model_flag:
        user_allowed = user_objects
    
    #user nie ma prawa - nie ma go ZAWSZE
    if has_user_model_flag and user_objects.exists():
        user_forbiden = user_objects
    
    #uprawnienia grup
    # jezeli ktoras grupa ma prawo do modelu - to trzeba tylko wywalic zabronione z innych grup
    user_groups = get_model('cos','Group').objects.filter(member__exact=user)
    
    groups_allowed=[]
    groups_forbiden=[]
    gr_full_model = False
    for group in user_groups:
         has_group_model_flag = get_model('cos','GroupFlag').objects.filter(group__exact=group, flag__object_id__exact=None, **filtr).exists()
         group_objects = get_model('cos','GroupFlag').objects.filter(group__exact=group, **filtr).exclude(flag__object_id__exact=None).values_list('flag__object_id', flat=True)
         
         if has_group_model_flag and not group_objects.exists():
             gr_full_model=True    #do modelu czyli pojdzie tylko wykluczanie !!!
             continue
        
         if has_group_model_flag and group_objects.exists():
             groups_forbiden.append(group_objects)
             continue
         
         if not has_group_model_flag:
             groups_allowed.append(group_objects)
        
    #uprawnienia dla authenticated
    auth_full_model = False
    has_model_flag = get_model('cos','VisitorFlag').objects.filter(authenticated__exact=True, flag__object_id__exact=None, **filtr).exists()
    authenticated_objects = get_model('cos','VisitorFlag').objects.filter(authenticated__exact=True,**filtr).                                                                                               exclude(flag__object_id__exact=None).values_list('flag__object_id', flat=True)
      
    auth_forbiden=[]
    auth_allowed=[]
    
    if has_model_flag and not authenticated_objects.exists():
        auth_full_model = True
    
    if has_model_flag and authenticated_objects.exists():
        auth_forbiden = authenticated_objects
    
    if not has_model_flag and authenticated_objects.exists():
        auth_allowed = authenticated_objects
        
    
    #mozliowsci
    
    #1
    #ktoras grupa ma pelny dostep - wszytkie mozliwe za wyjatkiem forbiden z usera i grup lub forbiden z grup nie ma wplywu na dozwolone z usera
    
    if gr_full_model:
        forbiden = []
        #user nie ma forbiden
        if len(user_forbiden) == 0:
            for forb in groups_forbiden:
                forbiden.append(forb.exclude(flag__object_id__in=user_allowed))
            return queryset.exclude(id__in=itertools.chain(*forbiden))
        else: #user ma forbiden
            forbiden = []
            forbiden.append(user_forbiden)
            for forb in groups_forbiden:
                forbiden.append(forb)
            return queryset.exclude(id__in=itertools.chain(*forbiden))
        
    #2
    #grupy nie maja pelnego dostepu -  to trzeba dodatkowo rozpatrzyc authenticated 
    #ponizej wersja bez authenticated
    if len(user_forbiden) == 0:
        for forb in groups_forbiden:
            forbiden.append(forb.exclude(flag__object_id__in=user_allowed))
      
        allowed = []
        allowed.append(user_allowed)
        for allow in groups_allowed:
            allowed.append(allow)
                
        return queryset.filter(id__in=itertools.chain(*allowed)).exclude(id__in=itertools.chain(*forbiden))
            
    else: #user ma forbiden
        forbiden = []
        forbiden.append(user_forbiden)
        for forb in groups_forbiden:
            forbiden.append(forb)
        return queryset.filter(id__in=itertools.chain(*groups_allowed)).exclude(id__in=itertools.chain(*forbiden))
            
        

    
    
    
class CosBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True

    def authenticate(self, username=None, password=None):
        return None
  
    def _checkPerm(self, perm_query, user):
        #Anonymous
        if not user.is_authenticated():
            return get_model('cos','VisitorFlag').objects.filter(anonymous__exact=True, flag__in=perm_query).exists()
        else:
            #uprawnienia dla user'a
            if get_model('cos','UserFlag').objects.filter(user__exact=user, flag__in=perm_query).exists():
                return True
                    
            group_perm = get_model('cos','GroupFlag')
            #uprawnienia dla grup
            for group in get_model('cos','Group').objects.filter(member__exact=user):
                if group_perm.objects.filter(group__exact=group, flag__in=perm_query).exists():
                    return True
                    
            #uprawnienie dla authenticated
            if get_model('cos','VisitorFlag').objects.filter(authenticated__exact=True, flag__in=perm_query).exists():
                return True
                
        return False
       
    def has_perm(self, user, perm, obj=None):
        app_name,model_name,perm_name = perm.split('.')
        
        if not obj is None:
            if app_name != obj._meta.app_label or model_name != obj._meta.object_name.lower():
                raise Http404
        
            
        permission_queryset =  get_model('cos','Flag').objects.filter(content_type__app_label__exact=app_name,
                                                     content_type__model__exact=model_name,
                                                     flag_type__slug__exact=perm_name)    
        
        model_perm_query = permission_queryset.filter(object_id__exact=None)
        has_model_flag = self._checkPerm(model_perm_query, user)
        has_object_flag = self._checkPerm(permission_queryset.filter(object_id__exact=obj.id), user) if not obj is None else False
        #UWAGA - bug - to dziala prawidlowo tylko dla jednej grupy
        return has_model_flag ^ has_object_flag
       
            
        

       
      