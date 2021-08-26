from collections import defaultdict

from django.contrib import admin
from django.forms.widgets import Textarea
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.text import normalize_newlines
from simple_history.admin import SimpleHistoryAdmin

from capapi.models import CapUser
from capapi.resources import CachedCountDefaultQuerySet
from .models import VolumeXML, CaseXML, PageXML, TrackingToolLog, VolumeMetadata, Reporter, \
    SlowQuery, Jurisdiction, CaseMetadata, CaseExport, Citation, EditLog, EditLogTransaction, FastcaseImport


### helpers and setup ###

def new_class(name, *args, **kwargs):
    return type(name, args, kwargs)

# change Django defaults, because 'extra' isn't helpful anymore now you can add more with javascript
admin.TabularInline.extra = 0
admin.StackedInline.extra = 0

# ensure that CRLF data from Textareas is normalized to LF
real_textarea_value_from_datadict = Textarea.value_from_datadict
Textarea.value_from_datadict = lambda *a, **k: normalize_newlines(real_textarea_value_from_datadict(*a, **k))


class ReadonlyInlineMixin(object):
    """ Mixin for inlines to not allow editing. """
    can_delete = False

    def has_add_permission(self, *args, **kwargs):
        return False

    def get_readonly_fields(self, *args, **kwargs):
        result = list(set(
                [field.name for field in self.opts.local_fields] +
                [field.name for field in self.opts.local_many_to_many]
            ))
        result.remove('id')
        return result


class CachedCountMixin(object):
    """
        Mixin for ModelAdmin to use cached .count() queries.
        Admin will report 1000000 entries if the real number is not available.
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs.__class__ = CachedCountDefaultQuerySet
        return qs


### admin models ###

@admin.register(VolumeXML)
class VolumeXMLAdmin(SimpleHistoryAdmin):
    raw_id_fields = ['metadata']


@admin.register(CaseMetadata)
class CaseMetadataAdmin(CachedCountMixin, admin.ModelAdmin):
    list_display = ['name_abbreviation', 'decision_date', 'jurisdiction', 'court', 'reporter']
    list_select_related = ('jurisdiction', 'court', 'reporter')
    inlines = (
        new_class('CitationInline', ReadonlyInlineMixin, admin.TabularInline, model=Citation),
        new_class('CaseXMLInline', admin.StackedInline, model=CaseXML, raw_id_fields=['volume']),
        new_class('FastcaseImportInline', admin.StackedInline, model=FastcaseImport, fk_name='case', raw_id_fields=['duplicate_of']),
    )
    fieldsets = (
        ('Flags', {
            'fields': ('duplicate', 'duplicate_of', 'no_index', 'no_index_notes',
                       'no_index_elided', 'no_index_redacted',
                       'robots_txt_until', 'withdrawn', 'replaced_by', 'in_scope', 'custom_footer_message'),
        }),
        ('Metadata', {
            'fields': ('docket_number', 'decision_date', 'decision_date_original', 'name_abbreviation', 'name',),
        }),
        ('Automatically generated fields', {
            'fields': ('frontend_url', 'attorneys', 'opinions', 'parties', 'judges',),
        }),
        ('Ingest metadata', {
            'fields': ('date_added', 'case_id', 'last_page', 'first_page', 'duplicative'),
        }),
        ('Relationship', {
            'description': "These cannot currently be changed via the admin.",
            'fields': ('reporter', 'volume', 'court', 'jurisdiction',),
        }),
    )
    raw_id_fields = ['duplicate_of', 'replaced_by', 'reporter', 'volume', 'court', 'jurisdiction']
    # mark all fields as readonly
    readonly_fields = sum((f[1]['fields'] for f in fieldsets[2:]), ())

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # handle changes to obj.withdrawn
        if 'withdrawn' in form.changed_data or 'replaced_by' in form.changed_data:
            obj.withdraw(obj.withdrawn, obj.replaced_by)
        obj.reindex()  # manual reindex for instant results


class CasePageInline(admin.TabularInline):
    model = PageXML.cases.through
    show_change_link = True
    raw_id_fields = ['casexml', 'pagexml']


@admin.register(PageXML)
class PageXMLAdmin(CachedCountMixin, SimpleHistoryAdmin):
    inlines = [CasePageInline]
    exclude = ('cases',)
    raw_id_fields = ['volume']


@admin.register(CaseXML)
class CaseXMLAdmin(CachedCountMixin, SimpleHistoryAdmin):
    inlines = [CasePageInline]
    raw_id_fields = ['volume', 'metadata']


@admin.register(TrackingToolLog)
class TrackingToolLogAdmin(admin.ModelAdmin):
    raw_id_fields = ['volume']


@admin.register(Reporter)
class ReporterAdmin(admin.ModelAdmin):
    fields = ['full_name', 'short_name', 'is_nominative', 'nominative_for', 'jurisdictions', 'start_year', 'end_year', 'notes', 'hollis']
    list_display = ['short_name', 'full_name', 'is_nominative', 'jurisdiction', 'start_year', 'end_year']
    search_fields = ['short_name', 'full_name']
    list_filter = ['jurisdictions', 'is_nominative']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('jurisdictions')

    def jurisdiction(self, obj):
        return ", ".join(j.name for j in obj.jurisdictions.all())

    # to inline volumes:
    # inlines = [new_class('VolumeInline', admin.TabularInline, model=VolumeMetadata)]


@admin.register(SlowQuery)
class SlowQueryAdmin(admin.ModelAdmin):
    list_display = ['last_seen', 'label', 'query']
    list_editable = ['label']


@admin.register(Jurisdiction)
class JurisdictionAdmin(admin.ModelAdmin):
    list_display = ['id', 'slug', 'name', 'name_long', 'whitelisted']


@admin.register(CaseExport)
class CaseExportAdmin(admin.ModelAdmin):
    list_display = ['id', 'export_date', 'filter_type', 'filter_id', 'file_name', 'file', 'public']


@admin.register(EditLog)
class EditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'timestamp', 'description']
    inlines = [new_class('EditLogTransactionInline', ReadonlyInlineMixin, admin.TabularInline, model=EditLogTransaction)]

    def user(self, obj):
        if not obj.user_id:
            return "-"
        return CapUser.objects.get(id=obj.user_id)


@admin.register(VolumeMetadata)
class VolumeMetadataAdmin(admin.ModelAdmin):
    raw_id_fields = ['duplicate_of', 'reporter', 'nominative_reporter', 'request', 'second_part_of']
    list_display = ['pk', 'volume_number', 'reporter', 'out_of_scope', 'duplicate']
    list_select_related = ['reporter']
    ordering = ['reporter__full_name', 'volume_number']
    search_fields = ['reporter__short_name', 'reporter__full_name', 'pk']
    list_filter = ['reporter__jurisdictions', 'reporter']
    fieldsets = (
        ('', {
            'fields': (
                'barcode', 'out_of_scope', 'title', 'reporter', 'volume_number', 'nominative_reporter', 'nominative_volume_number',
                'duplicate', 'duplicate_of',
                'second_part_of',
                'pdf_file',
                'task_statuses', 'xml_metadata',
                'ingest_status', 'ingest_errors',
                'notes', 'description',
            ),
        }),
    )
    readonly_fields = ['barcode', 'task_statuses', 'xml_metadata', 'ingest_status', 'ingest_errors']

    def get_urls(self):
        return [
            path('task_statuses/', self.admin_site.admin_view(self.task_statuses))
        ] + super().get_urls()

    def task_statuses(self, request):
        """
            View to summarize .task_statuses field for all volumes.
        """
        statuses = defaultdict(lambda: {'success': 0, 'error': 0, 'last_success': '', 'last_error': ''})

        for volume_statuses in VolumeMetadata.objects.filter(out_of_scope=False).values_list('task_statuses', flat=True):
            for task_name, outcome in volume_statuses.items():
                task = statuses[task_name]
                outcome_key = 'success' if 'success' in outcome else 'error'
                task[outcome_key] += 1
                ts_key = 'last_' + outcome_key
                ts = outcome['timestamp']
                if ts > task[ts_key]:
                    task[ts_key] = ts
                    if outcome_key == 'error':
                        task['error_message'] = outcome['error']

        return TemplateResponse(request, "admin/capdb/volumemetadata/task_statuses.html", {
            **self.admin_site.each_context(request),
            'title': 'Volume task results',
            'statuses': sorted(statuses.items()),
        })
