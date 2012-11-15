# -*- coding: utf-8 -*-
from django.db.models import get_model
from django.http import Http404
    
class FlagsBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True

    def authenticate(self, username=None, password=None):
        return None
    
    
    def _check_anonymous(self, user, perm, obj, model_perm_query, object_flag):
        model_exists = get_model('flags', 'AuthContentFlag').objects.filter(is_anonymous__exact=True, content_flag__in=model_perm_query).exists()
        if object_flag:
            obj_exists = get_model('flags', 'AuthContentFlag').objects.filter(is_anonymous__exact=True, content_flag__exact=object_flag).exists()
        else:
            obj_exists = False
          
        if model_exists or obj_exists:
            return model_exists ^ obj_exists
        
        return None
   
    def _check_auth(self, user, perm, obj, model_perm_query, object_flag):
        model_exists = get_model('flags', 'AuthContentFlag').objects.filter(is_authenticated__exact=True, content_flag__in=model_perm_query).exists()
        if object_flag:
            obj_exists = get_model('flags', 'AuthContentFlag').objects.filter(is_authenticated__exact=True, content_flag__exact=object_flag).exists()
        else:
            obj_exists = False
          
        if model_exists or obj_exists:
            return model_exists ^ obj_exists
        
        return None
        
    
    def _check_custom(self,user, perm, obj, model_perm_query, object_flag):
        model_queryset = get_model('flags', 'CustomContentFlag').objects.filter(content_flag__in=model_perm_query)
        if object_flag:
            obj_queryset = get_model('flags', 'CustomContentFlag').objects.filter(content_flag__exact=object_flag)
            obj_exists = obj_queryset.exists()
        else:
            obj_exists = False
                
        state = False
        if model_queryset.exists():
            state = model_queryset.get().content_object.check(user, perm, obj)  #jest unque na object_id i contet wiec NULL jest tylko jeden
        elif obj_exists:
            state = obj_queryset.get().check(user, perm, obj)
            
        model_exists = model_queryset.exists()
        #zakladam, ze ten jest ostatni w kolejce, a wiec zawsze zwroci True lub False
        return  state and (model_exists ^ obj_exists)
    
    def _check_user(self, user, perm, obj, model_perm_query, object_flag):
        model_exists = get_model('flags', 'UserContentFlag').objects.filter(user__exact=user, content_flag__in=model_perm_query).exists()
        if object_flag:
            obj_exists = get_model('flags', 'UserContentFlag').objects.filter(user__exact=user, content_flag__exact=object_flag).exists()
        else:
            obj_exists = False

        if model_exists or obj_exists:
            return model_exists ^ obj_exists
        return None

    def _check_user_context(self, user, perm, obj, model_perm_query, object_flag):
        # model_perm_query to jest zawsze content_flag, ale idzie jako lista??
        model_exists = self._has_context(model_perm_query[0], obj, user)

        if object_flag:
            obj_exists = self._has_context(object_flag, obj, user)
        else:
            obj_exists = False

        if model_exists or obj_exists:
            return model_exists ^ obj_exists
        return None

    def _has_context(self, content_flag, obj, user):
        entries_present = False
        for context in get_model('flags', 'UserContextContentFlag').objects.filter(content_flag=content_flag):
            user_content = context.user_content_type.model_class().objects.filter(**{context.user_field: user})
            if obj:
                modes = {'f': 'filter', 'e': 'exclude'}
                for mode, action in modes.iteritems():
                    obj_query = dict((query.lookup, getattr(obj, query.value_field)) for query in context.object_query_setups.filter(mode=mode))
                    user_content = getattr(user_content, action)(**obj_query)
            entries_present = user_content.exists()
        return entries_present
        
    def _check_groups(self,user, perm, obj, model_perm_query, object_flag):
        #jedna negujaca - nie ma uprawnienia, jedna pozytywne i brak negujacych - pozytywne
        positive = False
        for group in get_model('flags', 'Group').objects.filter(members__exact=user):
            model_exists = get_model('flags', 'GroupContentFlag').objects.filter(group__exact=group, content_flag__in=model_perm_query).exists()
            if object_flag:
                obj_exists = get_model('flags', 'GroupContentFlag').objects.filter(group__exact=group, content_flag__exact=object_flag).exists()
            else:
                obj_exists = False
            
            if model_exists or obj_exists:
                result = model_exists ^ obj_exists
                #jesli zabronione to koniec
                if not result:
                    return result
                else:
                    positive = True
     
        if positive:
            return positive
        
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
            result = self._check_anonymous(user, perm, obj, model_perm_query, object_flag)
            if not result is None:
                return result
            
            return self._check_custom(user,perm,obj, model_perm_query, object_flag)
                
        #sprawdz usera
        PRIORTY=['user', 'groups', 'auth', 'user_context', 'custom']
        
        for i in PRIORTY:
            try:
                result = getattr(self, "_check_%s"%i)(user, perm, obj, model_perm_query, object_flag)
                if not result is None:
                    return result
            except AttributeError:
                return False
                    
        #zabezpieczenie jakby zakonczylo sie Nonem !
        return False
