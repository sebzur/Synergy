# -*- coding: utf-8 -*-
from django.db.models import get_model
from django.http import Http404
    
class FlagsBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True

    def authenticate(self, username=None, password=None):
        return None
        
    def has_perm(self, user, perm, obj=None):
        app_name, model_name, perm_name = perm.split('.')
        
        if not obj is None:
            if app_name != obj._meta.app_label or model_name != obj._meta.object_name.lower():
                raise Http404
        
        
        #pobierz wszystkie contenty zwiazane z tym permem dla tego modelu
        permission_queryset =  get_model('flags', 'ContentFlag').objects.filter(content_type__app_label__exact=app_name,
                                                     content_type__model__exact=model_name,
                                                     flag__name__exact=perm_name)    
        
        
        model_perm_query = permission_queryset.filter(object_id__exact=None)
        
        if not obj is None and permission_queryset.filter(object_id__exact=obj.id).exists():
            object_flag = permission_queryset.get(object_id__exact=obj.id)
        else:
            object_flag = None
            
        #sprawdz anonimowego 
        if not user.is_authenticated():
            model = get_model('flags', 'UserStateFlag').objects.filter(is_anonymous__exact=True, flag__in=model_perm_query).exists()
            if object_flag:
                obj = get_model('flags', 'UserStateFlag').objects.filter(is_anonymous__exact=True, flag__exact=object_flag).exists()
            else:
                obj = False
            return model ^ obj
            
        #sprawdzanie zalogowanego
        #Jesli user ma dowolone lub user ma zabronione to zadne inne (grupa, authenticated) nie moga tego zmienic
        
        #sprawdz usera
        model = get_model('flags', 'UserFlag').objects.filter(user__exact=user, flag__in=model_perm_query).exists()
        if object_flag:
            obj = get_model('flags', 'UserFlag').objects.filter(user__exact=user, flag__exact=object_flag).exists()
        else:
            obj = False
        #czy jest wpis 
        if model or obj:
            return model ^ obj
       
        #teraz grupy 
        #jedna negujaca - nie ma uprawnienia, jedna pozytywne i brak negujacych - pozytywne
        positive = False
        for group in get_model('flags', 'Group').objects.filter(members__exact=user):
            model = get_model('flags', 'GroupFlag').objects.filter(group__exact=group, flag__in=model_perm_query).exists()
            if object_flag:
                obj = get_model('flags', 'GroupFlag').objects.filter(group__exact=group, flag__exact=object_flag).exists()
            else:
                obj = False
            #czy jest wpis
            if model or obj:
                result = model ^ obj
                #jesli zabronione to koniec
                if not result:
                    return result
                else:
                    positive = True
     
        if positive:
            return positive
     
        #Ostatni test - zalogowany user
        model = get_model('flags', 'UserStateFlag').objects.filter(is_authenticated__exact=True, flag__in=model_perm_query).exists()
        if object_flag:
            obj = get_model('flags', 'UserStateFlag').objects.filter(is_authenticated__exact=True, flag__exact=object_flag).exists()
        else:
            obj = False
        #jesli brak informacji to tak jakby ne bylo permissiona !!!!! 
        #to wazne gdyby dobudowywac kolejne zleznosci !!!!
        return model ^ obj
      