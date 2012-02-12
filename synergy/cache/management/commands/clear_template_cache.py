# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from optparse import OptionParser, make_option
from django.core.cache import cache
from django.utils.hashcompat import sha_constructor, md5_constructor

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option("-a", "--args", dest="args"), make_option("-n", "--name", dest="name"))
    
    def handle(self, *args, **options):
        # args are stored as "arg1:arg2:arg3"
        args = md5_constructor(options.get('args'))
        print options.get('args')
        c_key = "template.cache.%s.%s" % (options.get('name'), args.hexdigest())
        print('Cleaning key: %s' % c_key)
        data = cache.get(c_key)
        if data is None:
            print("No data!")
        else:
            cache.delete(c_key)

