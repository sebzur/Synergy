# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from optparse import OptionParser, make_option
from django.db.models import get_model
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option("-o", "--output", dest="output"), make_option("-n", "--name", dest="name"))
    def handle(self, *args, **options):
        name = options.get('name')
        output = options.get('output')
        copy_record(options.get('name'), options.get('output'))

def copy_record(name, output_name):
    rec_setup_model = get_model('records','RecordSetup')
    rec_field_model = get_model('records','RecordField')
    rec_argument_model = get_model('records','RecordArgument')
    rec_lookup_model = get_model('records', 'ObjectLookupSetup')
    
    
    #nowy record setup:
    record = rec_setup_model.objects.get(name=name)

#    new_success_url = "detail 'applicant-applications' object.get_application.id"
#    new_cancel_url = "detail 'applicant-applications' application_id"
#    new_generic_url = "detail 'applicant-applications' object.get_application.id"


    new_record = rec_setup_model.objects.create(name=output_name, model=record.model, only_registered_fields=record.only_registered_fields, use_model_m2m_fields=record.use_model_m2m_fields, success_url=record.success_url, reverse_success_url=record.reverse_success_url, cancel_url=record.cancel_url, reverse_cancel_url=record.reverse_cancel_url, generic_url=record.generic_url, reverse_generic_url=record.reverse_generic_url)

    #nowe argumenty
    for field in record.fields.all():
        rec_field_model.objects.create(setup=new_record, field=field.field, default_value=field.default_value, is_hidden=field.is_hidden)


    #nowe argumenty
    for argument in record.arguments.all():
        rec_argument_model.objects.create(setup=new_record, name=argument.name, regex=argument.regex, weight=argument.weight)

    #no i lookupy
    for field in record.fields.all():
        for lookup in field.lookups.all():
            l_field = new_record.fields.get(field__exact=lookup.field.field)
            l_arg = new_record.arguments.get(name__exact=lookup.value.name)
            rec_lookup_model.objects.create(value=l_arg, field=l_field, lookup=lookup.lookup)


