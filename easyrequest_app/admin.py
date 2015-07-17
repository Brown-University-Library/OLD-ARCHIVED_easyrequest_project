# # -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib import admin
from easyrequest_app.models import ItemRequest


class ItemRequestAdmin( admin.ModelAdmin ):
    date_hierarchy = 'create_datetime'
    ordering = [ '-id' ]
    list_display = [
        'id', 'create_datetime', 'status',
        'item_title', 'item_barcode', 'item_id', 'item_bib', 'item_callnumber',
        'patron_name', 'patron_barcode', 'patron_email',
        'admin_notes', 'source_url' ]
    # list_filter = [ 'patron_barcode' ]
    search_fields = [
        'id', 'create_datetime', 'status',
        'item_title', 'item_barcode', 'item_id', 'item_bib', 'item_callnumber',
        'patron_name', 'patron_barcode', 'patron_email',
        'admin_notes', 'source_url' ]
    readonly_fields = [
        'id', 'create_datetime', 'status',
        'item_title', 'item_barcode', 'item_id', 'item_bib', 'item_callnumber',
        'patron_name', 'patron_barcode', 'patron_email',
        'admin_notes', 'source_url' ]


admin.site.register( ItemRequest, ItemRequestAdmin )
