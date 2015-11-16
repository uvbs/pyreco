__FILENAME__ = manage
#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parliament.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.accounts.models import *

class UserAdmin(admin.ModelAdmin):

    list_display = ['email', 'created', 'last_login', 'email_bouncing']
    search_fields = ['email']
    list_filter = ['last_login', 'created', 'email_bouncing']

admin.site.register(User, UserAdmin)
########NEW FILE########
__FILENAME__ = middleware
from django.conf import settings
from django.http import HttpRequest

EMAIL_COOKIE_NAME = 'email'


class AuthenticatedEmailDescriptor(object):
    """Make request.authenticated_email an alias of request.session['_ae']"""

    def __get__(self, request, objtype=None):
        return request.session.get('_ae')

    def __set__(self, request, email):
        request.session['_ae'] = email
        request.session.modified = True


class AuthenticatedEmailUserDescriptor(object):

    def __get__(self, request, objtype=None):
        from parliament.accounts.models import User
        if not request.authenticated_email:
            return None
        try:
            user = User.objects.get(
                email=request.authenticated_email)
        except User.DoesNotExist:
            user = None
        request.authenticated_email_user = user
        return user

HttpRequest.authenticated_email = AuthenticatedEmailDescriptor()
HttpRequest.authenticated_email_user = AuthenticatedEmailUserDescriptor()


class AuthenticatedEmailMiddleware(object):
    """Keep a JS-readable cookie with the user's email, and ensure it's
    synchronized with the session."""

    def process_request(self, request):
        assert not hasattr(request, 'session'), "AuthenticatedEmailMiddleware must be before SessionMiddleware"

    def process_response(self, request, response):
        if settings.SESSION_COOKIE_NAME in response.cookies:
            # We're setting the session cookie, so update the email cookie
            if request.authenticated_email:
                response.cookies[EMAIL_COOKIE_NAME] = request.authenticated_email
                response.cookies[EMAIL_COOKIE_NAME].update(
                    response.cookies[settings.SESSION_COOKIE_NAME].copy())
                response.cookies[EMAIL_COOKIE_NAME]['httponly'] = ''
            else:
                response.delete_cookie(EMAIL_COOKIE_NAME)
        return response

########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'User'
        db.create_table('accounts_user', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75, db_index=True)),
            ('email_bouncing', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('json_data', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal('accounts', ['User'])


    def backwards(self, orm):
        
        # Deleting model 'User'
        db.delete_table('accounts_user')


    models = {
        'accounts.user': {
            'Meta': {'object_name': 'User'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'email_bouncing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['accounts']

########NEW FILE########
__FILENAME__ = models
import datetime

from django.db import models


class User(models.Model):

    email = models.EmailField(unique=True, db_index=True)
    email_bouncing = models.BooleanField(default=False)

    created = models.DateTimeField(default=datetime.datetime.now)
    last_login = models.DateTimeField(blank=True, null=True)

    json_data = models.TextField(default='{}')

    def __unicode__(self):
        return self.email

    def log_in(self, request):
        request.authenticated_email = self.email
        self.__class__.objects.filter(id=self.id).update(last_login=datetime.datetime.now())

########NEW FILE########
__FILENAME__ = persona
import browserid

from django.conf import settings

from parliament.accounts.models import User
from parliament.utils.views import JSONView

def get_user_from_persona_assertion(assertion, audience=settings.SITE_URL.replace('http://', '').replace('https://', '')):
    data = browserid.verify(assertion, audience)
    assert data['email']
    user, created = User.objects.get_or_create(email=data['email'].lower().strip())
    return user

class PersonaLoginEndpointView(JSONView):

    def post(self, request):
        user = get_user_from_persona_assertion(request.POST.get('assertion'))
        user.log_in(request)
        return {'email': user.email}

class PersonaLogoutEndpointView(JSONView):

    def post(self, request):
        request.authenticated_email = None
        return True

########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import patterns, include, url

from parliament.accounts.persona import *

urlpatterns = patterns('parliament.accounts.views',
    url(r'^login/$', PersonaLoginEndpointView.as_view()),
    url(r'^logout/$', PersonaLogoutEndpointView.as_view()),
    url(r'^current/$', 'current_account'),
)

########NEW FILE########
__FILENAME__ = views
from django.views.decorators.cache import never_cache

from parliament.utils.views import JSONView


class CurrentAccountView(JSONView):

    def get(self, request):
        return {'email': request.authenticated_email}

current_account = never_cache(CurrentAccountView.as_view())
########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.activity.models import *


class ActivityOptions(admin.ModelAdmin):
    list_display = ('politician', 'variety', 'date', 'guid')
    list_filter = ('variety', 'date')
    search_fields = ('politician__name', 'variety')
admin.site.register(Activity, ActivityOptions)
########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Activity'
        db.create_table('activity_activity', (
            ('politician', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'])),
            ('variety', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('guid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('payload', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('activity', ['Activity'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Activity'
        db.delete_table('activity_activity')
    
    
    models = {
        'activity.activity': {
            'Meta': {'object_name': 'Activity'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'variety': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        }
    }
    
    complete_apps = ['activity']

########NEW FILE########
__FILENAME__ = 0002_public
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Activity.active'
        db.add_column('activity_activity', 'active', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting field 'Activity.active'
        db.delete_column('activity_activity', 'active')
    
    
    models = {
        'activity.activity': {
            'Meta': {'object_name': 'Activity'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'variety': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        }
    }
    
    complete_apps = ['activity']

########NEW FILE########
__FILENAME__ = 0003_remove_p_from_payload
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        for activity in orm.Activity.objects.all():
            activity.payload = activity.payload.replace('<p class="activity_item">', '').replace('</p>', '')
            activity.save()


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'activity.activity': {
            'Meta': {'ordering': "('-date', '-id')", 'object_name': 'Activity'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'variety': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        }
    }

    complete_apps = ['activity']

########NEW FILE########
__FILENAME__ = models
from django.db import models

from parliament.core.models import Politician
from parliament.core.utils import ActiveManager

class Activity(models.Model):
    
    date = models.DateField(db_index=True)
    variety = models.CharField(max_length=15)
    politician = models.ForeignKey(Politician)
    payload = models.TextField()
    guid = models.CharField(max_length=50, db_index=True, unique=True)
    active = models.BooleanField(default=True, db_index=True)
    
    objects = models.Manager()
    public = ActiveManager()
    
    class Meta:
        ordering = ('-date','-id')
        verbose_name_plural = 'Activities'
        
    def payload_wrapped(self):
        return u'<p class="activity_item" data-id="%s">%s</p>' % (self.pk, self.payload)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Activity, self).save(*args, **kwargs)
        
        
########NEW FILE########
__FILENAME__ = utils
import datetime
from hashlib import sha1

from django.conf import settings
from django.template import Context, loader, RequestContext

from parliament.activity.models import Activity

def save_activity(obj, politician, date, guid=None, variety=None):
    if not getattr(settings, 'PARLIAMENT_SAVE_ACTIVITIES', True):
        return
    if not variety:
        variety = obj.__class__.__name__.lower()
    if not guid:
        guid = variety + str(obj.id)
    if len(guid) > 50:
        guid = sha1(guid).hexdigest()
    if Activity.objects.filter(guid=guid).exists():
        return False
    t = loader.get_template("activity/%s.html" % variety.lower())
    c = Context({'obj': obj, 'politician': politician})
    Activity(variety=variety,
        date=date,
        politician=politician,
        guid=guid,
        payload = t.render(c)).save()
    return True

ACTIVITY_MAX = {
    'twitter': 6,
    'gnews': 6,
    'membervote': 5,
    'statement': 8,
    'billsponsor': 7,
    'committee': 8,
} 
def iter_recent(queryset):
    activity_counts = ACTIVITY_MAX.copy()
    for activity in queryset:
        if activity_counts[activity.variety]:
            activity_counts[activity.variety] -= 1
            yield activity
            
def prune(queryset):
    today = datetime.date.today()
    activity_counts = ACTIVITY_MAX.copy()
    for activity in queryset:
        if activity_counts[activity.variety] >= 0:
            activity_counts[activity.variety] -= 1
        elif (today - activity.date).days >= 4: # only start pruning if it's a few days old
            activity.active = False
            activity.save()
        

########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.alerts.models import *

class PoliticianAlertAdmin(admin.ModelAdmin):
    
    list_display = ('email', 'politician', 'active', 'created')
    search_fields = ('email', 'politician__name')
    
admin.site.register(PoliticianAlert, PoliticianAlertAdmin)


class TopicAdmin(admin.ModelAdmin):

    list_display = ['query', 'created', 'last_found']
    search_fields = ['query']
    ordering = ['-created']


class SubscriptionAdmin(admin.ModelAdmin):

    list_display = ['user', 'topic', 'active', 'created', 'last_sent']
    search_fields = ['user__email']
    list_filter = ['active', 'created', 'last_sent']
    ordering = ['-created']

admin.site.register(Topic, TopicAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(SeenItem)
########NEW FILE########
__FILENAME__ = send_email_alerts
import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Searches for new items & sends applicable email alerts."

    def handle(self, **options):

        if getattr(settings, 'PARLIAMENT_SEARCH_CLOSED', False):
            return logger.error("Not sending alerts because of PARLIAMENT_SEARCH_CLOSED")

        from parliament.alerts.models import Subscription

        start_time = time.time()

        subscriptions = Subscription.objects.filter(active=True, user__email_bouncing=False
            ).prefetch_related('user', 'topic')

        by_topic = {}
        for sub in subscriptions:
            by_topic.setdefault(sub.topic, []).append(sub)

        topics_sent = messages_sent = 0

        for topic, subs in by_topic.items():
            documents = topic.get_new_items()
            logger.debug(u'%s documents for query %s' % (len(documents), topic))
            #time.sleep(0.3)
            if documents:
                topics_sent += 1
                for sub in subs:
                    messages_sent += 1
                    sub.send_email(documents)

        if topics_sent:
            print "%s topics, %s subscriptions sent in %s seconds" % (
                topics_sent, messages_sent, (time.time() - start_time))

########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'PoliticianAlert'
        db.create_table('alerts_politicianalert', (
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('politician', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal('alerts', ['PoliticianAlert'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'PoliticianAlert'
        db.delete_table('alerts_politicianalert')
    
    
    models = {
        'alerts.politicianalert': {
            'Meta': {'object_name': 'PoliticianAlert'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        }
    }
    
    complete_apps = ['alerts']

########NEW FILE########
__FILENAME__ = 0002_v2
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SeenItem'
        db.create_table('alerts_seenitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['alerts.Topic'])),
            ('item_id', self.gf('django.db.models.fields.CharField')(max_length=400, db_index=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('alerts', ['SeenItem'])

        # Adding unique constraint on 'SeenItem', fields ['topic', 'item_id']
        db.create_unique('alerts_seenitem', ['topic_id', 'item_id'])

        # Adding model 'Topic'
        db.create_table('alerts_topic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('query', self.gf('django.db.models.fields.CharField')(unique=True, max_length=800)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('last_checked', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_found', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('alerts', ['Topic'])

        # Adding model 'Subscription'
        db.create_table('alerts_subscription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['alerts.Topic'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_sent', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('alerts', ['Subscription'])

        # Adding unique constraint on 'Subscription', fields ['topic', 'user']
        db.create_unique('alerts_subscription', ['topic_id', 'user_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Subscription', fields ['topic', 'user']
        db.delete_unique('alerts_subscription', ['topic_id', 'user_id'])

        # Removing unique constraint on 'SeenItem', fields ['topic', 'item_id']
        db.delete_unique('alerts_seenitem', ['topic_id', 'item_id'])

        # Deleting model 'SeenItem'
        db.delete_table('alerts_seenitem')

        # Deleting model 'Topic'
        db.delete_table('alerts_topic')

        # Deleting model 'Subscription'
        db.delete_table('alerts_subscription')


    models = {
        'accounts.user': {
            'Meta': {'object_name': 'User'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'alerts.politicianalert': {
            'Meta': {'object_name': 'PoliticianAlert'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"})
        },
        'alerts.seenitem': {
            'Meta': {'unique_together': "[('topic', 'item_id')]", 'object_name': 'SeenItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.CharField', [], {'max_length': '400', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['alerts.Topic']"})
        },
        'alerts.subscription': {
            'Meta': {'unique_together': "[('topic', 'user')]", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['alerts.Topic']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.User']"})
        },
        'alerts.topic': {
            'Meta': {'object_name': 'Topic'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_found': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'query': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '800'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        }
    }

    complete_apps = ['alerts']

########NEW FILE########
__FILENAME__ = 0003_convert_old
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        for pa in orm.PoliticianAlert.objects.filter(active=True).select_related('politician'):
            query = u'MP: "%s" Type: "debate"' % pa.politician.slug
            topic, created = orm.Topic.objects.get_or_create(query=query)
            user, created = orm['accounts.User'].objects.get_or_create(email=pa.email.lower().strip())
            subscription, created = orm.Subscription.objects.get_or_create(
                topic=topic,
                user=user,
                defaults={
                    'created': pa.created,
                    'active': pa.active
                }
            )
        print "PoliticianAlert objects converted."
        print "You now need to call topic.initialize_if_necessary so that initial alerts"
        print "don't contain old items."
        print "Press Enter to continue"
        raw_input()


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'accounts.user': {
            'Meta': {'object_name': 'User'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'email_bouncing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'alerts.politicianalert': {
            'Meta': {'object_name': 'PoliticianAlert'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"})
        },
        'alerts.seenitem': {
            'Meta': {'unique_together': "[('topic', 'item_id')]", 'object_name': 'SeenItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.CharField', [], {'max_length': '400', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['alerts.Topic']"})
        },
        'alerts.subscription': {
            'Meta': {'unique_together': "[('topic', 'user')]", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['alerts.Topic']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.User']"})
        },
        'alerts.topic': {
            'Meta': {'object_name': 'Topic'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_found': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'query': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '800'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        }
    }

    complete_apps = ['alerts']

########NEW FILE########
__FILENAME__ = models
import base64
import datetime
import hashlib
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.signing import Signer
from django.core import urlresolvers
from django.db import models
from django.template import loader, Context

from parliament.core.models import Politician
from parliament.core.templatetags.ours import english_list
from parliament.core.utils import ActiveManager
from parliament.search.solr import SearchQuery

import logging
logger = logging.getLogger(__name__)


class TopicManager(models.Manager):

    def get_or_create_by_query(self, query):
        query_obj = SearchQuery(query)
        if 'Date' in query_obj.filters:
            del query_obj.filters['Date']  # Date filters make no sense in alerts
        normalized_query = query_obj.normalized_query
        if not normalized_query:
            raise ValueError("Invalid query")
        return self.get_or_create(query=normalized_query)


class Topic(models.Model):
    """A search that one or more people have saved."""
    query = models.CharField(max_length=800, unique=True)
    created = models.DateTimeField(default=datetime.datetime.now)
    last_checked = models.DateTimeField(blank=True, null=True)
    last_found = models.DateTimeField(blank=True, null=True)

    objects = TopicManager()

    def __unicode__(self):
        if self.politician_hansard_alert:
            return u'%s in House debates' % self.person_name
        return self.query

    def save(self, *args, **kwargs):
        super(Topic, self).save(*args, **kwargs)
        self.initialize_if_necessary()

    def get_search_query(self, limit=25):
        query_obj = SearchQuery(self.query, limit=limit,
            user_params={'sort': 'date desc'},
            full_text=self.politician_hansard_alert,
            solr_params={
                'mm': '100%' # match all query terms
            })

        # Only look for items newer than 60 days
        today = datetime.date.today()
        past = today - datetime.timedelta(days=60)
        query_obj.filters['Date'] = '%d-%02d to %d-12' % (
            past.year,
            past.month,
            today.year)

        return query_obj

    def initialize_if_necessary(self):
        if (not self.last_checked) or (
                (datetime.datetime.now() - self.last_checked) > datetime.timedelta(hours=24)):
            self.get_new_items(limit=40)

    def get_new_items(self, label_as_seen=True, limit=25):
        query_obj = self.get_search_query(limit=limit)
        result_ids = set((result['url'] for result in query_obj.documents))
        if result_ids:
            ids_seen = set(
                SeenItem.objects.filter(topic=self, item_id__in=list(result_ids))
                    .values_list('item_id', flat=True)
            )
            result_ids -= ids_seen

        self.last_checked = datetime.datetime.now()
        if result_ids:
            self.last_found = datetime.datetime.now()
        self.save()

        if label_as_seen and result_ids:
            SeenItem.objects.bulk_create([
                SeenItem(topic=self, item_id=result_id)
                for result_id in result_ids
            ])

        items = [r for r in reversed(query_obj.documents) if r['url'] in result_ids]

        if self.politician_hansard_alert:
            # Remove procedural stuff by the Speaker
            items = [r for r in items
                if 'Speaker' not in r['politician'] or len(r['full_text']) > 1200]

        return items

    @property
    def politician_hansard_alert(self):
        """Is this an alert for everything an MP says in the House chamber?"""
        return bool(re.search(r'^MP: \S+ Type: "debate"$', self.query))

    @property
    def person_name(self):
        match = re.search(r'Person: "([^"]+)"', self.query)
        if match:
            return match.group(1)
        match = re.search(r'MP: "([^\s"]+)"', self.query)
        if match:
            return Politician.objects.get_by_slug_or_id(match.group(1)).name


class SeenItem(models.Model):
    """A record that users have already seen a given item for a topic."""
    topic = models.ForeignKey(Topic)
    item_id = models.CharField(max_length=400, db_index=True)
    timestamp = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        unique_together = [
            ('topic', 'item_id')
        ]

    def __unicode__(self):
        return u'%s seen for %s' % (self.item_id, self.topic)


class SubscriptionManager(models.Manager):

    def get_or_create_by_query(self, query, user):
        topic, created = Topic.objects.get_or_create_by_query(query)
        return self.get_or_create(topic=topic, user=user)


class Subscription(models.Model):
    """A specific user's alert subscription for a specific search."""
    topic = models.ForeignKey(Topic)
    user = models.ForeignKey('accounts.User')

    created = models.DateTimeField(default=datetime.datetime.now)
    active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(blank=True, null=True)

    objects = SubscriptionManager()

    class Meta:
        unique_together = [
            ('topic', 'user')
        ]
        ordering = ['-created']

    def __unicode__(self):
        return u'%s: %s' % (self.user, self.topic)

    def save(self, *args, **kwargs):
        new = not self.id
        super(Subscription, self).save(*args, **kwargs)
        if new:
            self.topic.initialize_if_necessary()

    def get_unsubscribe_url(self, full=False):
        key = Signer(salt='alerts_unsubscribe').sign(unicode(self.id))
        return (settings.SITE_URL if full else '') + urlresolvers.reverse(
            'alerts_unsubscribe', kwargs={'key': key})

    def render_message(self, documents):
        ctx = {
            'documents': documents,
            'unsubscribe_url': self.get_unsubscribe_url(full=True)
        }

        if self.topic.politician_hansard_alert:
            ctx['person_name'] = documents[0]['politician']
            t = loader.get_template('alerts/mp_hansard_alert.txt')
            text = t.render(Context(ctx))
            return dict(text=text)

        ctx.update(
            topic=self.topic
        )
        t = loader.get_template('alerts/search_alert.txt')
        text = t.render(Context(ctx))
        return dict(text=text)

    def get_subject_line(self, documents):
        if self.topic.politician_hansard_alert:
            topics = set((d['topic'] for d in documents))
            subj = u'%(politician)s spoke about %(topics)s in the House' % {
                'politician': documents[0]['politician'],
                'topics': english_list(list(topics))
            }
        else:
            subj = u'New from openparliament.ca for %s' % self.topic.query
        return subj[:200]

    def send_email(self, documents):
        rendered = self.render_message(documents)
        msg = EmailMultiAlternatives(
            self.get_subject_line(documents),
            rendered['text'],
            'alerts@contact.openparliament.ca',
            [self.user.email]
        )
        if not self.topic.politician_hansard_alert:
            msg.bcc = ['michael@openparliament.ca']
        if rendered.get('html'):
            msg.attach_alternative(rendered['html'], 'text/html')
        if getattr(settings, 'PARLIAMENT_SEND_EMAIL', False):
            msg.send()
            self.last_sent = datetime.datetime.now()
            self.save()
        else:
            logger.warning("settings.PARLIAMENT_SEND_EMAIL must be True to send mail")
            print msg.subject
            print msg.body


class PoliticianAlert(models.Model):
    
    email = models.EmailField('Your e-mail')
    politician = models.ForeignKey(Politician)
    active = models.BooleanField(default=False)
    created = models.DateTimeField(default=datetime.datetime.now)
    
    objects = models.Manager()
    public = ActiveManager()
    
    def get_key(self):
        h = hashlib.sha1()
        h.update(str(self.id))
        h.update(self.email)
        h.update(settings.SECRET_KEY)
        return base64.urlsafe_b64encode(h.digest()).replace('=', '')
        
    @models.permalink
    def get_unsubscribe_url(self):
        return ('parliament.alerts.views.unsubscribe_old', [], {'alert_id': self.id, 'key': self.get_key()})
    
    def __unicode__(self):
        return u"%s for %s (%s)" % \
            (self.email, self.politician.name, 'active' if self.active else 'inactive')
########NEW FILE########
__FILENAME__ = alerts
import re

from django import template

register = template.Library()

@register.filter(name='text_highlight')
def text_highlight(s):
    s = re.sub(r'</?em>', '**', s.replace('&gt;', '>').replace('&lt;', '<').replace('&quot;', '"').replace('&amp;', '&'))
    s = re.sub(r'\n+', ' ', s)
    return re.sub('&#(\d+);', lambda m: chr(int(m.group(1))), s)


########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import patterns, include, url

urlpatterns = patterns('parliament.alerts.views',
    url(r'^pol_hansard_signup/$', 'politician_hansard_signup', name='alerts_pol_signup'),
    url(r'^unsubscribe/(?P<key>[^\s/]+)/$', 'unsubscribe', name='alerts_unsubscribe'),
    url(r'^$', 'alerts_list', name='alerts_list'),
    url(r'^create/$', 'create_alert'),
    url(r'^(?P<subscription_id>\d+)/$', 'modify_alert'),
    url(r'^pha/(?P<signed_key>[^\s/]+)$', 'politician_hansard_subscribe', name='alerts_pol_subscribe'),
)

########NEW FILE########
__FILENAME__ = utils
from collections import defaultdict

from django.template import Context, loader, RequestContext
from django.core.mail import send_mail

from parliament.alerts.models import PoliticianAlert
from parliament.core.templatetags.ours import english_list

import logging
logger = logging.getLogger(__name__)


def clear_former_mp_alerts(qs=None):
    from parliament.core.models import ElectedMember

    if qs is None:
        qs = PoliticianAlert.objects.filter(active=True)
    bad_alerts = [a for a in qs
        if not a.politician.current_member]
    for alert in bad_alerts:
        riding = alert.politician.latest_member.riding
        new_politician = ElectedMember.objects.get(riding=riding, end_date__isnull=True).politician
        t = loader.get_template("alerts/former_mp.txt")
        c = Context({
            'politician': alert.politician,
            'riding': riding,
            'new_politician': new_politician
        })
        msg = t.render(c)
        subj = u'Your alerts for %s from openparliament.ca' % alert.politician.name
        try:
            send_mail(subject=subj,
                message=msg,
                from_email='alerts@contact.openparliament.ca',
                recipient_list=[alert.email])
            alert.active = False
            alert.save()
        except Exception as e:
            logger.error("Couldn't send mail for alert %s; %r" % (alert.id, e))

########NEW FILE########
__FILENAME__ = views
import json
import re

from django.template import loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core import urlresolvers
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail, mail_admins
from django.core.signing import Signer, TimestampSigner, BadSignature
from django.views.decorators.cache import never_cache

from parliament.accounts.models import User
from parliament.alerts.models import Subscription
from parliament.core.models import Politician
from parliament.core.views import disable_on_readonly_db
from parliament.utils.views import JSONView

class PoliticianAlertForm(forms.Form):

    email = forms.EmailField(label='Your email')
    politician = forms.IntegerField(widget=forms.HiddenInput)

@disable_on_readonly_db
def politician_hansard_signup(request):
    try:
        politician_id = int(re.sub(r'\D', '', request.REQUEST.get('politician', '')))
    except ValueError:
        raise Http404
 
    pol = get_object_or_404(Politician, pk=politician_id)
    success = False
    if request.method == 'POST':
        # This is a hack to remove spaces from e-mails before sending them off to the validator
        # If anyone knows a cleaner way of doing this without writing a custom field, please let me know
        postdict = request.POST.copy()
        if 'email' in postdict:
            postdict['email'] = postdict['email'].strip().lower()

        form = PoliticianAlertForm(postdict)
        if form.is_valid():
            if form.cleaned_data['email'] == request.authenticated_email:
                Subscription.objects.get_or_create_by_query(
                    _generate_query_for_politician(pol),
                    request.authenticated_email_user
                )
                messages.success(request, u"You're signed up for alerts for %s." % pol.name)
                return HttpResponseRedirect(urlresolvers.reverse('alerts_list'))

            key = "%s,%s" % (politician_id, form.cleaned_data['email'])
            signed_key = TimestampSigner(salt='alerts_pol_subscribe').sign(key)
            activate_url = urlresolvers.reverse('alerts_pol_subscribe',
                kwargs={'signed_key': signed_key})
            activation_context = RequestContext(request, {
                'pol': pol,
                'activate_url': activate_url,
            })
            t = loader.get_template("alerts/activate.txt")
            send_mail(subject=u'Confirmation required: Email alerts about %s' % pol.name,
                message=t.render(activation_context),
                from_email='alerts@contact.openparliament.ca',
                recipient_list=[form.cleaned_data['email']])

            success = True
    else:
        initial = {
            'politician': politician_id
        }
        if request.authenticated_email:
            initial['email'] = request.authenticated_email
        form = PoliticianAlertForm(initial=initial)
        
    c = RequestContext(request, {
        'form': form,
        'success': success,
        'pol': pol,
        'title': 'Email alerts for %s' % pol.name,
    })
    t = loader.get_template("alerts/signup.html")
    return HttpResponse(t.render(c))


@never_cache
def alerts_list(request):
    if not request.authenticated_email:
        return render(request, 'alerts/list_unauthenticated.html',
            {'title': 'Email alerts'})

    user = User.objects.get(email=request.authenticated_email)

    if request.session.get('pending_alert'):
        Subscription.objects.get_or_create_by_query(request.session['pending_alert'], user)
        del request.session['pending_alert']

    subscriptions = Subscription.objects.filter(user=user).select_related('topic')

    t = loader.get_template('alerts/list.html')
    c = RequestContext(request, {
        'user': user,
        'subscriptions': subscriptions,
        'title': 'Your email alerts'
    })
    resp = HttpResponse(t.render(c))
    resp.set_cookie(
        key='enable-alerts',
        value='y',
        max_age=60*60*24*90,
        httponly=False
    )
    return resp


class CreateAlertView(JSONView):

    def post(self, request):
        query = request.POST.get('query')
        if not query:
            raise Http404
        user_email = request.authenticated_email
        if not user_email:
            request.session['pending_alert'] = query
            return self.redirect(urlresolvers.reverse('alerts_list'))
        user = User.objects.get(email=user_email)
        try:
            subscription = Subscription.objects.get_or_create_by_query(query, user)
            return True
        except ValueError:
            raise NotImplementedError
create_alert = CreateAlertView.as_view()


class ModifyAlertView(JSONView):

    def post(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, id=subscription_id)
        if subscription.user.email != request.authenticated_email:
            raise PermissionDenied

        action = request.POST.get('action')
        if action == 'enable':
            subscription.active = True
            subscription.save()
        elif action == 'disable':
            subscription.active = False
            subscription.save()
        elif action == 'delete':
            subscription.delete()

        return True
modify_alert = ModifyAlertView.as_view()

def _generate_query_for_politician(pol):
    return u'MP: "%s" Type: "debate"' % pol.identifier

@disable_on_readonly_db
def politician_hansard_subscribe(request, signed_key):
    ctx = {
        'key_error': False
    }
    try:
        key = TimestampSigner(salt='alerts_pol_subscribe').unsign(signed_key, max_age=60*60*24*14)
        politician_id, _, email = key.partition(',')
        pol = get_object_or_404(Politician, id=politician_id)
        if not pol.current_member:
            raise Http404

        user, created = User.objects.get_or_create(email=email)
        sub, created = Subscription.objects.get_or_create_by_query(
            _generate_query_for_politician(pol), user)
        if not sub.active:
            sub.active = True
            sub.save()
        ctx.update(
            pol=pol,
            title=u'Email alerts for %s' % pol.name
        )
    except BadSignature:
        ctx['key_error'] = True

    return render(request, 'alerts/activate.html', ctx)


@never_cache
def unsubscribe(request, key):
    ctx = {
        'title': 'Email alerts'
    }
    try:
        subscription_id = Signer(salt='alerts_unsubscribe').unsign(key)
        subscription = get_object_or_404(Subscription, id=subscription_id)
        subscription.active = False
        subscription.save()
        if settings.PARLIAMENT_DB_READONLY:
            mail_admins("Unsubscribe request", subscription_id)
        ctx['query'] = subscription.topic
    except BadSignature:
        ctx['key_error'] = True
    c = RequestContext(request, ctx)
    t = loader.get_template("alerts/unsubscribe.html")
    return HttpResponse(t.render(c))


def bounce_webhook(request):
    """Simple view to process bounce reports delivered via webhook.
    (uses the Mandrill API for the moment)"""
    if 'mandrill_events' not in request.POST:
        raise Http404

    for event in json.loads(request.POST['mandrill_events']):
        if 'bounce' in event['event']:
            User.objects.filter(email=event['msg']['email']).update(email_bouncing=True)
    return HttpResponse('OK')

########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import patterns, url
urlpatterns = patterns('parliament.api.views',
    url(r'^hansards/(?P<hansard_id>\d+)/$', 'hansard', name='legacy_api_hansard'),
    url(r'^hansards/$', 'hansard_list', name='legacy_api_hansard_list'),   
)
########NEW FILE########
__FILENAME__ = views
from django.shortcuts import get_object_or_404

from parliament.hansards.models import Document
from parliament.utils.views import JSONView

class LegacyAPIHansardListView(JSONView):

    wrap = False

    def get(self, request):
        return [{
            'note': "This API is deprecated. Please use the API documented on the openparliament.ca Developers page.",
            'date': unicode(h.date),
            'id': h.id,
            'number': h.number,
            'api_url': '/api/hansards/%s/' % h.id
        } for h in Document.debates.all()]

hansard_list = LegacyAPIHansardListView.as_view()

def _serialize_statement(s):
    v = {
        'url': s.get_absolute_url(),
        'heading': s.heading,
        'topic': s.topic,
        'time': unicode(s.time),
        'attribution': s.who,
        'text': s.text_plain()
    }
    if s.member:
        v['politician'] = {
            'id': s.member.politician.id,
            'member_id': s.member.id,
            'name': s.member.politician.name,
            'url': s.member.politician.get_absolute_url(),
            'party': s.member.party.short_name,
            'riding': unicode(s.member.riding),
        }
    return v

class LegacyAPIHansardView(JSONView):

    wrap = False

    def get(self, request, hansard_id):
        doc = get_object_or_404(Document, document_type='D', id=hansard_id)
        return {
            'date': unicode(doc.date),
            'url': doc.get_absolute_url(),
            'id': doc.id,
            'original_url': doc.url,
            'parliament': doc.session.parliamentnum,
            'session': doc.session.sessnum,
            'statements': [_serialize_statement(s)
                for s in doc.statement_set.all()
                    .order_by('sequence')
                    .select_related('member__politician', 'member__party', 'member__riding')]
        }

hansard = LegacyAPIHansardView.as_view()
########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.bills.models import *

class BillOptions(admin.ModelAdmin):
    search_fields = ['number']
    raw_id_fields = ('sponsor_member','sponsor_politician')
    list_display = ('number', 'name', 'session', 'privatemember', 'sponsor_politician', 'added', 'introduced')
    list_filter = ('institution', 'privatemember', 'added', 'sessions', 'introduced', 'status_date')
    ordering = ['-introduced']

class BillInSessionOptions(admin.ModelAdmin):
    list_display = ['bill', 'session']

class BillTextOptions(admin.ModelAdmin):
    list_display = ['bill', 'docid', 'created']
    search_fields = ['bill__number', 'bill__name_en', 'docid']
    
class VoteQuestionOptions(admin.ModelAdmin):
    list_display = ('number', 'date', 'bill', 'description', 'result')
    raw_id_fields = ('bill', 'context_statement')
    
class MemberVoteOptions(admin.ModelAdmin):
    list_display = ('politician', 'votequestion', 'vote')
    raw_id_fields = ('politician', 'member')
    
class PartyVoteAdmin(admin.ModelAdmin):
    list_display = ('party', 'votequestion', 'vote', 'disagreement')

class BillEventAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'status', 'date', 'institution')
    raw_id_fields = ('debate', 'committee_meetings', 'bis')
    list_filter = ('date', 'institution')
    

admin.site.register(Bill, BillOptions)
admin.site.register(BillInSession, BillInSessionOptions)
admin.site.register(BillText, BillTextOptions)
admin.site.register(VoteQuestion, VoteQuestionOptions)
admin.site.register(MemberVote, MemberVoteOptions)
admin.site.register(PartyVote, PartyVoteAdmin)
admin.site.register(BillEvent, BillEventAdmin)
########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Bill'
        db.create_table('bills_bill', (
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Session'])),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal('bills', ['Bill'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Bill'
        db.delete_table('bills_bill')
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0002_intnumber
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Bill.number_only'
        db.add_column('bills_bill', 'number_only', self.gf('django.db.models.fields.SmallIntegerField')(default=0), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting field 'Bill.number_only'
        db.delete_column('bills_bill', 'number_only')
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0003_legisinfo
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Bill.sponsor_member'
        db.add_column('bills_bill', 'sponsor_member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ElectedMember'], null=True, blank=True), keep_default=False)

        # Adding field 'Bill.privatemember'
        db.add_column('bills_bill', 'privatemember', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True), keep_default=False)

        # Adding field 'Bill.sponsor_politician'
        db.add_column('bills_bill', 'sponsor_politician', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'], null=True, blank=True), keep_default=False)

        # Adding field 'Bill.legisinfo_url'
        db.add_column('bills_bill', 'legisinfo_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting field 'Bill.sponsor_member'
        db.delete_column('bills_bill', 'sponsor_member_id')

        # Deleting field 'Bill.privatemember'
        db.delete_column('bills_bill', 'privatemember')

        # Deleting field 'Bill.sponsor_politician'
        db.delete_column('bills_bill', 'sponsor_politician_id')

        # Deleting field 'Bill.legisinfo_url'
        db.delete_column('bills_bill', 'legisinfo_url')
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0004_votes
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'MemberVote'
        db.create_table('bills_membervote', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ElectedMember'])),
            ('politician', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'])),
            ('votequestion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bills.VoteQuestion'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vote', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('bills', ['MemberVote'])

        # Adding model 'VoteQuestion'
        db.create_table('bills_votequestion', (
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('nay_total', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('bill', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bills.Bill'], null=True, blank=True)),
            ('paired_total', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('number', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Session'])),
            ('result', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('yea_total', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('bills', ['VoteQuestion'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'MemberVote'
        db.delete_table('bills_membervote')

        # Deleting model 'VoteQuestion'
        db.delete_table('bills_votequestion')
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0005_apr9
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting field 'Bill.session'
        db.delete_column('bills_bill', 'session_id')

        # Adding field 'Bill.status'
        db.add_column('bills_bill', 'status', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Bill.law'
        db.add_column('bills_bill', 'law', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True), keep_default=False)

        # Adding M2M table for field sessions on 'Bill'
        db.create_table('bills_bill_sessions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bill', models.ForeignKey(orm['bills.bill'], null=False)),
            ('session', models.ForeignKey(orm['core.session'], null=False))
        ))
        db.create_unique('bills_bill_sessions', ['bill_id', 'session_id'])

        # Adding index on 'VoteQuestion', fields ['date']
        db.create_index('bills_votequestion', ['date'])
    
    
    def backwards(self, orm):
        
        # Adding field 'Bill.session'
        db.add_column('bills_bill', 'session', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['core.Session']), keep_default=False)

        # Deleting field 'Bill.status'
        db.delete_column('bills_bill', 'status')

        # Deleting field 'Bill.law'
        db.delete_column('bills_bill', 'law')

        # Removing M2M table for field sessions on 'Bill'
        db.delete_table('bills_bill_sessions')

        # Removing index on 'VoteQuestion', fields ['date']
        db.delete_index('bills_votequestion', ['date'])
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0006_added_field
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Bill.added'
        db.add_column('bills_bill', 'added', self.gf('django.db.models.fields.DateField')(default=datetime.date.today, db_index=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting field 'Bill.added'
        db.delete_column('bills_bill', 'added')
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0007_partyvotes
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'PartyVote'
        db.create_table('bills_partyvote', (
            ('vote', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Party'])),
            ('votequestion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bills.VoteQuestion'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('bills', ['PartyVote'])

        # Adding field 'MemberVote.dissent'
        db.add_column('bills_membervote', 'dissent', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting model 'PartyVote'
        db.delete_table('bills_partyvote')

        # Deleting field 'MemberVote.dissent'
        db.delete_column('bills_membervote', 'dissent')
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'object_name': 'PartyVote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0008_partyvote_disagreement
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'PartyVote.disagreement'
        db.add_column('bills_partyvote', 'disagreement', self.gf('django.db.models.fields.FloatField')(null=True), keep_default=False)

        # Adding unique constraint on 'PartyVote', fields ['party', 'votequestion']
        db.create_unique('bills_partyvote', ['party_id', 'votequestion_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'PartyVote', fields ['party', 'votequestion']
        db.delete_unique('bills_partyvote', ['party_id', 'votequestion_id'])

        # Deleting field 'PartyVote.disagreement'
        db.delete_column('bills_partyvote', 'disagreement')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('number_only',)", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0009_add_institution
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Bill.institution'
        db.add_column('bills_bill', 'institution', self.gf('django.db.models.fields.CharField')(default='C', max_length=1, db_index=True), keep_default=False)

        # Changing field 'Bill.name'
        db.alter_column('bills_bill', 'name', self.gf('django.db.models.fields.TextField')())


    def backwards(self, orm):
        
        # Deleting field 'Bill.institution'
        db.delete_column('bills_bill', 'institution')

        # Changing field 'Bill.name'
        db.alter_column('bills_bill', 'name', self.gf('django.db.models.fields.CharField')(max_length=500))


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0010_new_legisinfo_fields
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Bill.legisinfo_url'
        db.delete_column('bills_bill', 'legisinfo_url')

        # Adding field 'Bill.name_fr'
        db.add_column('bills_bill', 'name_fr', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Bill.short_title_en'
        db.add_column('bills_bill', 'short_title_en', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Bill.short_title_fr'
        db.add_column('bills_bill', 'short_title_fr', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Bill.status_fr'
        db.add_column('bills_bill', 'status_fr', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Bill.status_date'
        db.add_column('bills_bill', 'status_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Bill.introduced'
        db.add_column('bills_bill', 'introduced', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Bill.text_docid'
        db.add_column('bills_bill', 'text_docid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'Bill.legisinfo_url'
        db.add_column('bills_bill', 'legisinfo_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True), keep_default=False)

        # Deleting field 'Bill.name_fr'
        db.delete_column('bills_bill', 'name_fr')

        # Deleting field 'Bill.short_title_en'
        db.delete_column('bills_bill', 'short_title_en')

        # Deleting field 'Bill.short_title_fr'
        db.delete_column('bills_bill', 'short_title_fr')

        # Deleting field 'Bill.status_fr'
        db.delete_column('bills_bill', 'status_fr')

        # Deleting field 'Bill.status_date'
        db.delete_column('bills_bill', 'status_date')

        # Deleting field 'Bill.introduced'
        db.delete_column('bills_bill', 'introduced')

        # Deleting field 'Bill.text_docid'
        db.delete_column('bills_bill', 'text_docid')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0011_rename_billsession_join_table
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        db.rename_table('bills_bill_sessions', 'bills_billinsession')


    def backwards(self, orm):

        db.rename_table('bills_billinsession', 'bills_bill_sessions')

    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0012_add_billinsession_fields
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'BillInSession.legisinfo_id'
        db.add_column('bills_billinsession', 'legisinfo_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True), keep_default=False)

        # Adding field 'BillInSession.introduced'
        db.add_column('bills_billinsession', 'introduced', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'BillInSession.sponsor_politician'
        db.add_column('bills_billinsession', 'sponsor_politician', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'], null=True, blank=True), keep_default=False)

        # Adding field 'BillInSession.sponsor_member'
        db.add_column('bills_billinsession', 'sponsor_member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ElectedMember'], null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'BillInSession.legisinfo_id'
        db.delete_column('bills_billinsession', 'legisinfo_id')

        # Deleting field 'BillInSession.introduced'
        db.delete_column('bills_billinsession', 'introduced')

        # Deleting field 'BillInSession.sponsor_politician'
        db.delete_column('bills_billinsession', 'sponsor_politician_id')

        # Deleting field 'BillInSession.sponsor_member'
        db.delete_column('bills_billinsession', 'sponsor_member_id')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0013_votequestion_context_statement
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'VoteQuestion.context_statement'
        db.add_column('bills_votequestion', 'context_statement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hansards.Statement'], null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'VoteQuestion.context_statement'
        db.delete_column('bills_votequestion', 'context_statement_id')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'context_statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Statement']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0014_add_billtext
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BillText'
        db.create_table('bills_billtext', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bill', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bills.Bill'])),
            ('docid', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('text_en', self.gf('django.db.models.fields.TextField')()),
            ('text_fr', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('bills', ['BillText'])


    def backwards(self, orm):
        
        # Deleting model 'BillText'
        db.delete_table('bills_billtext')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'bills.billtext': {
            'Meta': {'object_name': 'BillText'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'docid': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text_en': ('django.db.models.fields.TextField', [], {}),
            'text_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'context_statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Statement']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'urlcache': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0015_billtext_unique
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding unique constraint on 'BillText', fields ['docid']
        db.create_unique('bills_billtext', ['docid'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'BillText', fields ['docid']
        db.delete_unique('bills_billtext', ['docid'])


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'bills.billtext': {
            'Meta': {'object_name': 'BillText'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'docid': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text_en': ('django.db.models.fields.TextField', [], {}),
            'text_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'context_statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Statement']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'urlcache': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0016_enfr
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        db.rename_column('bills_votequestion', 'description', 'description_en')

        # Adding field 'VoteQuestion.description_fr'
        db.add_column('bills_votequestion', 'description_fr', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding index on 'BillInSession', fields ['introduced']
        db.create_index('bills_billinsession', ['introduced'])

        db.rename_column('bills_bill', 'name', 'name_en')

    def backwards(self, orm):
        
        # Removing index on 'BillInSession', fields ['introduced']
        db.delete_index('bills_billinsession', ['introduced'])

        # Deleting field 'VoteQuestion.description_fr'
        db.delete_column('bills_votequestion', 'description_fr')

        db.rename_column('bills_bill', 'name_en', 'name')

        db.rename_column('bills_votequestion', 'description_en', 'description')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'bills.billtext': {
            'Meta': {'object_name': 'BillText'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'docid': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text_en': ('django.db.models.fields.TextField', [], {}),
            'text_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'context_statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Statement']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {}),
            'description_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h1_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'h2_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'h3_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'urlcache': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who_context_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'who_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = 0017_billstatus
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BillEvent'
        db.create_table('bills_billevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bis', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bills.BillInSession'])),
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('source_id', self.gf('django.db.models.fields.PositiveIntegerField')(unique=True, db_index=True)),
            ('institution', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('status_en', self.gf('django.db.models.fields.TextField')()),
            ('status_fr', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('debate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hansards.Document'], null=True, blank=True)),
        ))
        db.send_create_signal('bills', ['BillEvent'])

        # Adding M2M table for field committee_meetings on 'BillEvent'
        db.create_table('bills_billevent_committee_meetings', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('billevent', models.ForeignKey(orm['bills.billevent'], null=False)),
            ('committeemeeting', models.ForeignKey(orm['committees.committeemeeting'], null=False))
        ))
        db.create_unique('bills_billevent_committee_meetings', ['billevent_id', 'committeemeeting_id'])

        # Deleting field 'Bill.status'
        db.delete_column('bills_bill', 'status')

        # Deleting field 'Bill.status_fr'
        db.delete_column('bills_bill', 'status_fr')

        # Adding field 'Bill.status_code'
        db.add_column('bills_bill', 'status_code', self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'BillEvent'
        db.delete_table('bills_billevent')

        # Removing M2M table for field committee_meetings on 'BillEvent'
        db.delete_table('bills_billevent_committee_meetings')

        # Adding field 'Bill.status'
        db.add_column('bills_bill', 'status', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Bill.status_fr'
        db.add_column('bills_bill', 'status_fr', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Deleting field 'Bill.status_code'
        db.delete_column('bills_bill', 'status_code')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billevent': {
            'Meta': {'object_name': 'BillEvent'},
            'bis': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.BillInSession']"}),
            'committee_meetings': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['committees.CommitteeMeeting']", 'symmetrical': 'False'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'debate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'source_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'status_en': ('django.db.models.fields.TextField', [], {}),
            'status_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'bills.billtext': {
            'Meta': {'object_name': 'BillText'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'docid': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text_en': ('django.db.models.fields.TextField', [], {}),
            'text_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'bills.membervote': {
            'Meta': {'object_name': 'MemberVote'},
            'dissent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.partyvote': {
            'Meta': {'unique_together': "(('votequestion', 'party'),)", 'object_name': 'PartyVote'},
            'disagreement': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'vote': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'votequestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.VoteQuestion']"})
        },
        'bills.votequestion': {
            'Meta': {'ordering': "('-date', '-number')", 'object_name': 'VoteQuestion'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']", 'null': 'True', 'blank': 'True'}),
            'context_statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Statement']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {}),
            'description_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nay_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'paired_total': ('django.db.models.fields.SmallIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'yea_total': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'committees.committee': {
            'Meta': {'ordering': "['name_en']", 'object_name': 'Committee'},
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.TextField', [], {}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcommittees'", 'null': 'True', 'to': "orm['committees.Committee']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['committees.CommitteeInSession']", 'symmetrical': 'False'}),
            'short_name_en': ('django.db.models.fields.TextField', [], {}),
            'short_name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'committees.committeeactivity': {
            'Meta': {'object_name': 'CommitteeActivity'},
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'study': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeeinsession': {
            'Meta': {'unique_together': "[('session', 'committee'), ('session', 'acronym')]", 'object_name': 'CommitteeInSession'},
            'acronym': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'committees.committeemeeting': {
            'Meta': {'unique_together': "[('session', 'committee', 'number')]", 'object_name': 'CommitteeMeeting'},
            'activities': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['committees.CommitteeActivity']", 'symmetrical': 'False'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hansards.Document']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_camera': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'minutes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notice': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'televised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'travel': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'webcast': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h1_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'h2_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'h3_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'urlcache': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who_context_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'who_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['bills']

########NEW FILE########
__FILENAME__ = models
import datetime
from collections import defaultdict
import re

from django.conf import settings
from django.core import urlresolvers
from django.db import models
from django.utils.safestring import mark_safe

from parliament.committees.models import CommitteeMeeting
from parliament.core.models import Session, ElectedMember, Politician, Party
from parliament.core.utils import language_property
from parliament.hansards.models import Document, Statement
from parliament.activity import utils as activity

import logging
logger = logging.getLogger(__name__)

CALLBACK_URL = 'http://www2.parl.gc.ca/HousePublications/GetWebOptionsCallBack.aspx?SourceSystem=PRISM&ResourceType=Document&ResourceID=%d&language=1&DisplayMode=2'
BILL_VOTES_URL = 'http://www2.parl.gc.ca/Housebills/BillVotes.aspx?Language=E&Parl=%s&Ses=%s&Bill=%s'

LEGISINFO_BILL_URL = 'http://www.parl.gc.ca/LegisInfo/BillDetails.aspx?Language=%(lang)s&Mode=1&Bill=%(bill)s&Parl=%(parliament)s&Ses=%(session)s'
LEGISINFO_BILL_ID_URL = 'http://www.parl.gc.ca/LEGISINFO/BillDetails.aspx?Language=%(lang)s&Mode=1&billId=%(id)s'
PARLIAMENT_DOCVIEWER_URL = 'http://parl.gc.ca/HousePublications/Publication.aspx?Language=%(lang)s&Mode=1&DocId=%(docid)s'

class BillManager(models.Manager):

    def get_by_legisinfo_id(self, legisinfo_id):
        """Given a House of Commons ID (e.g. from LEGISinfo, or a Hansard link),
        return a Bill, creating it if necessary."""
        legisinfo_id = int(legisinfo_id)
        try:
            return self.get(billinsession__legisinfo_id=legisinfo_id)
        except Bill.DoesNotExist:
            from parliament.imports import legisinfo
            return legisinfo.import_bill_by_id(legisinfo_id)

    def create_temporary_bill(self, number, session, legisinfo_id=None):
        """Creates a bare-bones Bill object, to be filled in later.

        Used because often it'll be a day or two between when a bill ID is
        first referenced in Hansard and when it shows up in LEGISinfo.
        """
        if legisinfo_id:
            legisinfo_id = int(legisinfo_id)
            if BillInSession.objects.filter(legisinfo_id=int(legisinfo_id)).exists():
                raise Bill.MultipleObjectsReturned(
                    "There's already a bill with LEGISinfo id %s" % legisinfo_id)
        try:
            bill = Bill.objects.get(number=number, sessions=session)
            logger.error("Potential duplicate LEGISinfo ID: %s in %s exists, but trying to create with ID %s" %
                (number, session, legisinfo_id))
            return bill
        except Bill.DoesNotExist:
            bill = self.create(number=number)
            BillInSession.objects.create(bill=bill, session=session,
                    legisinfo_id=legisinfo_id)
            return bill

    def recently_active(self, number=12):
        return Bill.objects.filter(status_date__isnull=False).exclude(models.Q(privatemember=True) 
            & models.Q(status_code='Introduced')).order_by('-status_date')[:number]


class Bill(models.Model): 
    CHAMBERS = (
        ('C', 'House'),
        ('S', 'Senate'),
    )
    STATUS_CODES = {
        u'BillNotActive': 'Not active',
        u'WillNotBeProceededWith': 'Dead',
        u'RoyalAssentAwaiting': 'Awaiting royal assent',
        u'BillDefeated': 'Defeated',
        u'HouseAtReportStage': 'Report stage (House)',
        u'RoyalAssentGiven': 'Law (royal assent given)',
        u'SenateAt1stReading': 'First reading (Senate)',
        u'HouseAt1stReading': 'First reading (House)',
        u'HouseAt2ndReading': 'Second reading (House)',
        u'SenateAt2ndReading': 'Second reading (Senate)',
        u'SenateAt3rdReading': 'Third reading (Senate)',
        u'HouseAt3rdReading': 'Third reading (House)',
        u'HouseInCommittee': 'In committee (House)',
        u'SenateInCommittee': 'In committee (Senate)',
        u'SenateConsiderationOfCommitteeReport': 'Considering committee report (Senate)',
        u'HouseConsiderationOfAmendments': 'Considering amendments (House)',
        u'Introduced': 'Introduced'
    }

    name_en = models.TextField(blank=True)
    name_fr = models.TextField(blank=True)
    short_title_en = models.TextField(blank=True)
    short_title_fr = models.TextField(blank=True)
    number = models.CharField(max_length=10)
    number_only = models.SmallIntegerField()
    institution = models.CharField(max_length=1, db_index=True, choices=CHAMBERS)
    sessions = models.ManyToManyField(Session, through='BillInSession')
    privatemember = models.NullBooleanField()
    sponsor_member = models.ForeignKey(ElectedMember, blank=True, null=True)
    sponsor_politician = models.ForeignKey(Politician, blank=True, null=True)
    law = models.NullBooleanField()

    status_date = models.DateField(blank=True, null=True, db_index=True)
    status_code = models.CharField(max_length=50, blank=True)

    added = models.DateField(default=datetime.date.today, db_index=True)
    introduced = models.DateField(blank=True, null=True)
    text_docid = models.IntegerField(blank=True, null=True,
        help_text="The parl.gc.ca document ID of the latest version of the bill's text")
    
    objects = BillManager()

    name = language_property('name')
    short_title = language_property('short_title')
   
    class Meta:
        ordering = ('privatemember', 'institution', 'number_only')
    
    def __unicode__(self):
        return "%s - %s" % (self.number, self.name)
        
    def get_absolute_url(self):
        return self.url_for_session(self.session)

    def url_for_session(self, session):
        return urlresolvers.reverse('parliament.bills.views.bill', kwargs={
            'session_id': session.id, 'bill_number': self.number})
        
    def get_legisinfo_url(self, lang='E'):
        return LEGISINFO_BILL_URL % {
            'lang': lang,
            'bill': self.number.replace('-', ''),
            'parliament': self.session.parliamentnum,
            'session': self.session.sessnum
        }
        
    legisinfo_url = property(get_legisinfo_url)
        
    def get_billtext_url(self, lang='E', single_page=False):
        if not self.text_docid:
            return None
        url = PARLIAMENT_DOCVIEWER_URL % {
            'lang': lang,
            'docid': self.text_docid
        }
        if single_page:
            url += '&File=4&Col=1'
        return url

    def get_text_object(self):
        if not self.text_docid:
            raise BillText.DoesNotExist
        return BillText.objects.get(bill=self, docid=self.text_docid)

    def get_text(self, language=settings.LANGUAGE_CODE):
        try:
            return getattr(self.get_text_object(), 'text_' + language)
        except BillText.DoesNotExist:
            return ''

    def get_summary(self):
        try:
            return self.get_text_object().summary_html
        except BillText.DoesNotExist:
            return ''

    def get_related_debates(self):
        return Document.objects.filter(billinsession__bill=self)

    def get_committee_meetings(self):
        return CommitteeMeeting.objects.filter(billevent__bis__bill=self)

    def get_major_speeches(self):
        doc_ids = list(self.get_related_debates().values_list('id', flat=True))
        if self.short_title_en:
            qs = Statement.objects.filter(h2_en__iexact=self.short_title_en, wordcount__gt=50)
        else:
            qs = self.statement_set.filter(wordcount__gt=100)
        return qs.filter(document__in=doc_ids, procedural=False)

    @property
    def latest_date(self):
        return self.status_date if self.status_date else self.introduced
        
    def save(self, *args, **kwargs):
        if not self.number_only:
            self.number_only = int(re.sub(r'\D', '', self.number))
        if getattr(self, 'privatemember', None) is None:
            self.privatemember = bool(self.number_only >= 200)
        if not self.institution:
            self.institution = self.number[0]
        if not self.law and self.status_code == 'RoyalAssentGiven':
            self.law = True
        super(Bill, self).save(*args, **kwargs)

    def save_sponsor_activity(self):
        if self.sponsor_politician:
            activity.save_activity(
                obj=self,
                politician=self.sponsor_politician,
                date=self.introduced if self.introduced else (self.added - datetime.timedelta(days=1)),
                variety='billsponsor',
            )
        
    def get_session(self):
        """Returns the most recent session this bill belongs to."""
        try:
            self.__dict__['session'] = s = self.sessions.all().order_by('-start')[0]
            return s
        except (IndexError, ValueError):
            return getattr(self, '_session', None)

    def set_temporary_session(self, session):
        """To deal with tricky save logic, saves a session to the object for cases
        when self.sessions.all() won't get exist in the DB."""
        self._session = session
        
    session = property(get_session)

    @property
    def status(self):
        return self.STATUS_CODES.get(self.status_code, 'Unknown')

    @property
    def dead(self):
        return self.status_code in ('BillNotActive', 'WillNotBeProceededWith', 'BillDefeated')

    @property
    def dormant(self):
        return (self.status_date and (datetime.date.today() - self.status_date).days > 150)

class BillInSessionManager(models.Manager):

    def get_by_legisinfo_id(self, legisinfo_id):
        legisinfo_id = int(legisinfo_id)
        try:
            return self.get(legisinfo_id=legisinfo_id)
        except BillInSession.DoesNotExist:
            from parliament.imports import legisinfo
            legisinfo.import_bill_by_id(legisinfo_id)
            return self.get(legisinfo_id=legisinfo_id)


class BillInSession(models.Model):
    """Represents a bill, as introduced in a single session.

    All bills are, technically, introduced only in a single session.
    But, in a decision which ended up being pretty complicated, we combine
    reintroduced bills into a single Bill object. But it's this model
    that maps one-to-one to most IDs used elsewhere.
    """
    bill = models.ForeignKey(Bill)
    session = models.ForeignKey(Session)

    legisinfo_id = models.PositiveIntegerField(db_index=True, blank=True, null=True)
    introduced = models.DateField(blank=True, null=True, db_index=True)
    sponsor_politician = models.ForeignKey(Politician, blank=True, null=True)
    sponsor_member = models.ForeignKey(ElectedMember, blank=True, null=True)

    debates = models.ManyToManyField('hansards.Document', through='BillEvent')

    objects = BillInSessionManager()

    def __unicode__(self):
        return u"%s in session %s" % (self.bill, self.session_id)

    def get_absolute_url(self):
        return self.bill.url_for_session(self.session)

    def get_legisinfo_url(self, lang='E'):
        return LEGISINFO_BILL_ID_URL % {
            'lang': lang,
            'id': self.legisinfo_id
        }

    def to_api_dict(self, representation):
        d = {
            'session': self.session_id,
            'legisinfo_id': self.legisinfo_id,
            'introduced': unicode(self.introduced) if self.introduced else None,
            'name': {
                'en': self.bill.name_en,
                'fr': self.bill.name_fr
            },
            'number': self.bill.number
        }
        if representation == 'detail':
            d.update(
                short_title={'en': self.bill.short_title_en, 'fr': self.bill.short_title_fr},
                home_chamber=self.bill.get_institution_display(),
                law=self.bill.law,
                sponsor_politician_url=self.sponsor_politician.get_absolute_url() if self.sponsor_politician else None,
                sponsor_politician_membership_url=urlresolvers.reverse('politician_membership',
                    kwargs={'member_id': self.sponsor_member_id}) if self.sponsor_member_id else None,
                text_url=self.bill.get_billtext_url(),
                other_session_urls=[self.bill.url_for_session(s)
                    for s in self.bill.sessions.all()
                    if s.id != self.session_id],
                vote_urls=[vq.get_absolute_url() for vq in VoteQuestion.objects.filter(bill=self.bill_id)],
                private_member_bill=self.bill.privatemember,
                legisinfo_url=self.get_legisinfo_url(),
                status_code=self.bill.status_code,
                status={'en': self.bill.status}
            )
        return d


class BillEvent(models.Model):
    bis = models.ForeignKey(BillInSession)

    date = models.DateField(db_index=True)

    source_id = models.PositiveIntegerField(unique=True, db_index=True)

    institution = models.CharField(max_length=1, choices=Bill.CHAMBERS)

    status_en = models.TextField()
    status_fr = models.TextField(blank=True)

    debate = models.ForeignKey('hansards.Document', blank=True, null=True, on_delete=models.SET_NULL)
    committee_meetings = models.ManyToManyField('committees.CommitteeMeeting', blank=True)

    status = language_property('status')

    def __unicode__(self):
        return u"%s: %s, %s" % (self.status, self.bis.bill.number, self.date)

    @property
    def bill_number(self):
        return self.bis.bill.number


class BillText(models.Model):

    bill = models.ForeignKey(Bill)
    docid = models.PositiveIntegerField(unique=True, db_index=True)

    created = models.DateTimeField(default=datetime.datetime.now)

    text_en = models.TextField()
    text_fr = models.TextField(blank=True)

    text = language_property('text')

    def __unicode__(self):
        return u"Document #%d for %s" % (self.docid, self.bill)

    @property
    def summary(self):
        match = re.search(r'SUMMARY\n([\s\S]+?)(Also a|A)vailable on', self.text_en)
        return match.group(1).strip() if match else None

    @property
    def summary_html(self):
        summary = self.summary
        if not summary:
            return ''
        return mark_safe('<p>' + summary.replace('\n', '</p><p>') + '</p>')

        
VOTE_RESULT_CHOICES = (
    ('Y', 'Passed'), # Agreed to
    ('N', 'Failed'), # Negatived
    ('T', 'Tie'),
)
class VoteQuestion(models.Model):
    
    bill = models.ForeignKey(Bill, blank=True, null=True)
    session = models.ForeignKey(Session)
    number = models.PositiveIntegerField()
    date = models.DateField(db_index=True)
    description_en = models.TextField()
    description_fr = models.TextField(blank=True)
    result = models.CharField(max_length=1, choices=VOTE_RESULT_CHOICES)
    yea_total = models.SmallIntegerField()
    nay_total = models.SmallIntegerField()
    paired_total = models.SmallIntegerField()
    context_statement = models.ForeignKey('hansards.Statement',
        blank=True, null=True, on_delete=models.SET_NULL)

    description = language_property('description')
    
    def __unicode__(self):
        return u"Vote #%s on %s" % (self.number, self.date)
        
    class Meta:
        ordering=('-date', '-number')

    def to_api_dict(self, representation):
        r = {
            'bill_url': self.bill.get_absolute_url() if self.bill else None,
            'session': self.session_id,
            'number': self.number,
            'date': unicode(self.date),
            'description': {'en': self.description_en, 'fr': self.description_fr},
            'result': self.get_result_display(),
            'yea_total': self.yea_total,
            'nay_total': self.nay_total,
            'paired_total': self.paired_total,
        }
        if representation == 'detail':
            r.update(
                context_statement=self.context_statement.get_absolute_url() if self.context_statement else None,
                party_votes=[{
                    'vote': pv.get_vote_display(),
                    'disagreement': pv.disagreement,
                    'party': {
                        'name': {'en': pv.party.name},
                        'short_name': {'en': pv.party.short_name}
                    },
                } for pv in self.partyvote_set.all()]
            )
        return r

    def label_absent_members(self):
        for member in ElectedMember.objects.on_date(self.date).exclude(membervote__votequestion=self):
            MemberVote(votequestion=self, member=member, politician_id=member.politician_id, vote='A').save()
            
    def label_party_votes(self):
        """Create PartyVote objects representing the party-line vote; label individual dissenting votes."""
        membervotes = self.membervote_set.select_related('member', 'member__party').all()
        parties = defaultdict(lambda: defaultdict(int))
        
        for mv in membervotes:
            if mv.member.party.name != 'Independent':
                parties[mv.member.party][mv.vote] += 1
        
        partyvotes = {}
        for party in parties:
            # Find the most common vote
            votes = sorted(parties[party].items(), key=lambda i: i[1])
            partyvotes[party] = votes[-1][0]
            
            # Find how many people voted with the majority
            yn = (parties[party]['Y'], parties[party]['N'])
            try:
                disagreement = float(min(yn))/sum(yn)
            except ZeroDivisionError:
                disagreement = 0.0
                
            # If more than 15% of the party voted against the party majority,
            # label this as a free vote.
            if disagreement >= 0.15:
                partyvotes[party] = 'F'
            
            PartyVote.objects.filter(party=party, votequestion=self).delete()
            PartyVote.objects.create(party=party, votequestion=self, vote=partyvotes[party], disagreement=disagreement)
        
        for mv in membervotes:
            if mv.member.party.name != 'Independent' \
              and mv.vote != partyvotes[mv.member.party] \
              and mv.vote in ('Y', 'N') \
              and partyvotes[mv.member.party] in ('Y', 'N'):
                mv.dissent = True
                mv.save()
            
    @models.permalink
    def get_absolute_url(self):
        return ('parliament.bills.views.vote', [],
            {'session_id': self.session_id, 'number': self.number})

VOTE_CHOICES = [
    ('Y', 'Yes'),
    ('N', 'No'),
    ('P', 'Paired'),
    ('A', "Didn't vote"),
]
class MemberVote(models.Model):
    
    votequestion = models.ForeignKey(VoteQuestion)
    member = models.ForeignKey(ElectedMember)
    politician = models.ForeignKey(Politician)
    vote = models.CharField(max_length=1, choices=VOTE_CHOICES)
    dissent = models.BooleanField(default=False, db_index=True)
    
    def __unicode__(self):
        return u'%s voted %s on %s' % (self.politician, self.get_vote_display(), self.votequestion)
            
    def save_activity(self):
        activity.save_activity(self, politician=self.politician, date=self.votequestion.date)

    def to_api_dict(self, representation):
        return {
            'vote_url': self.votequestion.get_absolute_url(),
            'politician_url': self.politician.get_absolute_url(),
            'politician_membership_url': urlresolvers.reverse('politician_membership',
                kwargs={'member_id': self.member_id}) if self.member_id else None,
            'ballot': self.get_vote_display(),
        }

VOTE_CHOICES_PARTY = VOTE_CHOICES + [('F', "Free vote")]            
class PartyVote(models.Model):
    
    votequestion = models.ForeignKey(VoteQuestion)
    party = models.ForeignKey(Party)
    vote = models.CharField(max_length=1, choices=VOTE_CHOICES_PARTY)
    disagreement = models.FloatField(null=True)
    
    class Meta:
        unique_together = ('votequestion', 'party')
    
    def __unicode__(self):
        return u'%s voted %s on %s' % (self.party, self.get_vote_display(), self.votequestion)
########NEW FILE########
__FILENAME__ = search_indexes
#coding: utf-8

from haystack import site
from haystack import indexes

from parliament.search.index import SearchIndex
from parliament.bills.models import Bill
from parliament.core.models import Session


class BillIndex(SearchIndex):
    text = indexes.CharField(document=True, model_attr='get_text')
    searchtext = indexes.CharField(use_template=True)
    boosted = indexes.CharField(stored=False, use_template=True)
    title = indexes.CharField(model_attr='name')
    number = indexes.CharField(model_attr='number', indexed=False)
    url = indexes.CharField(model_attr='get_absolute_url', indexed=False)
    date = indexes.DateField(model_attr='latest_date', null=True)
    session = indexes.CharField(model_attr='session', indexed=False, null=True)
    politician = indexes.CharField(model_attr='sponsor_politician__name', null=True)
    politician_id = indexes.CharField(model_attr='sponsor_politician__identifier', null=True)
    party = indexes.CharField(model_attr='sponsor_member__party__short_name', null=True)
    doctype = indexes.CharField(default='bill')

    def prepare_session(self, obj):
        if self.prepared_data.get('session'):
            return self.prepared_data['session']

        if obj.introduced:
            return Session.objects.get_by_date(obj.introduced)

        return Session.objects.current()

    def prepare_title(self, obj):
        if len(obj.name) < 150:
            return obj.name
        elif obj.short_title:
            return obj.short_title
        else:
            return obj.name[:140] + u'…'

    def get_queryset(self):
        return Bill.objects.all().prefetch_related(
            'sponsor_politician', 'sponsor_member', 'sponsor_member__party'
        )

site.register(Bill, BillIndex)

########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import patterns, include, url
from django.core import urlresolvers
from django.http import HttpResponsePermanentRedirect

from parliament.bills.views import BillFeed, BillListFeed

urlpatterns = patterns('parliament.bills.views',
    url(r'^(?P<session_id>\d+-\d)/(?P<bill_number>[CS]-[0-9A-Z]+)/$', 'bill', name='bill'),
    url(r'^(?P<bill_id>\d+)/rss/$', BillFeed(), name='bill_feed'),
    (r'^(?:session/)?(?P<session_id>\d+-\d)/$', 'bills_for_session'),
    url(r'^$', 'index', name='bills'),
    (r'^(?P<bill_id>\d+)/$', 'bill_pk_redirect'),
    url(r'^rss/$', BillListFeed(), name='bill_list_feed'),
    url(r'^votes/([0-9/-]*)$', lambda r,u: HttpResponsePermanentRedirect(
        urlresolvers.reverse('votes') + u)),
)

########NEW FILE########
__FILENAME__ = views
import datetime
from urllib import urlencode

from django.contrib.syndication.views import Feed
from django.core import urlresolvers
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.template import Context, loader, RequestContext
from django.template.defaultfilters import date as format_date
from django.utils.safestring import mark_safe
from django.views.decorators.vary import vary_on_headers

from parliament.bills.models import Bill, VoteQuestion, MemberVote, BillInSession
from parliament.core.api import ModelListView, ModelDetailView, APIFilters
from parliament.core.models import Session
from parliament.hansards.models import Statement, Document

def bill_pk_redirect(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    return HttpResponsePermanentRedirect(
        urlresolvers.reverse('parliament.bills.views.bill', kwargs={
        'session_id': bill.get_session().id, 'bill_number': bill.number}))


class BillDetailView(ModelDetailView):

    resource_name = 'Bill'

    def get_object(self, request, session_id, bill_number):
        return BillInSession.objects.select_related(
            'bill', 'sponsor_politician').get(session=session_id, bill__number=bill_number)

    def get_related_resources(self, request, qs, result):
        return {
            'bills_url': urlresolvers.reverse('bills')
        }

    def _render_page(self, request, qs, per_page=10):
        paginator = Paginator(qs, per_page)

        try:
            pagenum = int(request.GET.get('page', '1'))
        except ValueError:
            pagenum = 1
        try:
            return paginator.page(pagenum)
        except (EmptyPage, InvalidPage):
            return paginator.page(paginator.num_pages)

    def get_html(self, request, session_id, bill_number):
        bill = get_object_or_404(Bill, sessions=session_id, number=bill_number)

        mentions = bill.statement_set.all().order_by('-time', '-sequence').select_related('member', 'member__politician', 'member__riding', 'member__party')
        major_speeches = bill.get_major_speeches().order_by('-document__date', 'sequence').select_related(
            'member', 'member__politician', 'member__riding', 'member__party')
        meetings = bill.get_committee_meetings()

        tab = request.GET.get('tab', 'major-speeches')

        has_major_speeches = major_speeches.exists()
        has_mentions = has_major_speeches or mentions.exists()
        has_meetings = meetings.exists()

        if tab == 'major-speeches' and not has_major_speeches:
            tab = 'mentions'

        per_page = 500 if request.GET.get('singlepage') else 15

        if tab == 'mentions':
            page = self._render_page(request, mentions, per_page=per_page)
        elif tab == 'major-speeches':
            page = self._render_page(request, major_speeches, per_page=per_page)
        else:
            page = None

        c = RequestContext(request, {
            'bill': bill,
            'has_major_speeches': has_major_speeches,
            'has_mentions': has_mentions,
            'has_meetings': has_meetings,
            'committee_meetings': meetings,
            'votequestions': bill.votequestion_set.all().order_by('-date', '-number'),
            'page': page,
            'allow_single_page': True,
            'tab': tab,
            'title': ('Bill %s' % bill.number) + (' (Historical)' if bill.session.end else ''),
            'statements_full_date': True,
            'statements_context_link': True,
        })
        if request.is_ajax():
            if tab == 'meetings':
                t = loader.get_template("bills/related_meetings.inc")
            else:
                t = loader.get_template("hansards/statement_page.inc")
        else:
            t = loader.get_template("bills/bill_detail.html")
        return HttpResponse(t.render(c))
bill = vary_on_headers('X-Requested-With')(BillDetailView.as_view())
    
class BillListView(ModelListView):

    resource_name = 'Bills'

    filters = {
        'session': APIFilters.dbfield(help="e.g. 41-1"),
        'introduced': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="date bill was introduced, e.g. introduced__gt=2010-01-01"),
        'legisinfo_id': APIFilters.dbfield(help="integer ID assigned by parl.gc.ca's LEGISinfo"),
        'number': APIFilters.dbfield('bill__number',
            help="a string, not an integer: e.g. C-10"),
        'law': APIFilters.dbfield('bill__law',
            help="did it become law? True, False"),
        'private_member_bill': APIFilters.dbfield('bill__privatemember',
            help="is it a private member's bill? True, False"),
        'status_code': APIFilters.dbfield('bill__status_code'),
        'sponsor_politician': APIFilters.politician('sponsor_politician'),
        'sponsor_politician_membership': APIFilters.fkey(lambda u: {'sponsor_member': u[-1]}),
    }

    def get_qs(self, request):
        return BillInSession.objects.all().select_related('bill', 'sponsor_politician')

    def get_html(self, request):
        sessions = Session.objects.with_bills()
        len(sessions) # evaluate it
        bills = Bill.objects.filter(sessions=sessions[0])
        votes = VoteQuestion.objects.select_related('bill').filter(session=sessions[0])[:6]

        t = loader.get_template('bills/index.html')
        c = RequestContext(request, {
            'object_list': bills,
            'session_list': sessions,
            'votes': votes,
            'session': sessions[0],
            'title': 'Bills & Votes',
            'recently_active': Bill.objects.recently_active()
        })

        return HttpResponse(t.render(c))
index = BillListView.as_view()


class BillSessionListView(ModelListView):

    def get_json(self, request, session_id):
        return HttpResponseRedirect(urlresolvers.reverse('bills') + '?'
                                    + urlencode({'session': session_id}))

    def get_html(self, request, session_id):
        session = get_object_or_404(Session, pk=session_id)
        bills = Bill.objects.filter(sessions=session)
        votes = VoteQuestion.objects.select_related('bill').filter(session=session)[:6]

        t = loader.get_template('bills/bill_list.html')
        c = RequestContext(request, {
            'object_list': bills,
            'session': session,
            'votes': votes,
            'title': 'Bills for the %s' % session
        })
        return HttpResponse(t.render(c))
bills_for_session = BillSessionListView.as_view()


class VoteListView(ModelListView):

    resource_name = 'Votes'

    api_notes = mark_safe("""<p>What we call votes are <b>divisions</b> in official Parliamentary lingo.
        We refer to an individual person's vote as a <a href="/votes/ballots/">ballot</a>.</p>
    """)

    filters = {
        'session': APIFilters.dbfield(help="e.g. 41-1"),
        'yea_total': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="# votes for"),
        'nay_total': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="# votes against, e.g. nay_total__gt=10"),
        'paired_total': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="paired votes are an odd convention that seem to have stopped in 2011"),
        'date': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="date__gte=2011-01-01"),
        'number': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="every vote in a session has a sequential number"),
        'bill': APIFilters.fkey(lambda u: {
            'bill__sessions': u[-2],
            'bill__number': u[-1]
        }, help="e.g. /bills/41-1/C-10/"),
        'result': APIFilters.choices('result', VoteQuestion)
    }

    def get_json(self, request, session_id=None):
        if session_id:
            return HttpResponseRedirect(urlresolvers.reverse('votes') + '?'
                                        + urlencode({'session': session_id}))
        return super(VoteListView, self).get_json(request)

    def get_qs(self, request):
        return VoteQuestion.objects.select_related(depth=1).order_by('-date', '-number')

    def get_html(self, request, session_id=None):
        if session_id:
            session = get_object_or_404(Session, pk=session_id)
        else:
            session = Session.objects.current()

        t = loader.get_template('bills/votequestion_list.html')
        c = RequestContext(request, {
            'object_list': self.get_qs(request).filter(session=session),
            'session': session,
            'title': 'Votes for the %s' % session
        })
        return HttpResponse(t.render(c))
votes_for_session = VoteListView.as_view()
        
def vote_pk_redirect(request, vote_id):
    vote = get_object_or_404(VoteQuestion, pk=vote_id)
    return HttpResponsePermanentRedirect(
        urlresolvers.reverse('parliament.bills.views.vote', kwargs={
        'session_id': vote.session_id, 'number': vote.number}))


class VoteDetailView(ModelDetailView):

    resource_name = 'Vote'

    api_notes = VoteListView.api_notes

    def get_object(self, request, session_id, number):
        return get_object_or_404(VoteQuestion, session=session_id, number=number)

    def get_related_resources(self, request, obj, result):
        return {
            'ballots_url': urlresolvers.reverse('vote_ballots') + '?' +
                urlencode({'vote': result['url']}),
            'votes_url': urlresolvers.reverse('votes')
        }

    def get_html(self, request, session_id, number):
        vote = self.get_object(request, session_id, number)
        membervotes = MemberVote.objects.filter(votequestion=vote)\
            .order_by('member__party', 'member__politician__name_family')\
            .select_related('member', 'member__party', 'member__politician')
        partyvotes = vote.partyvote_set.select_related('party').all()

        c = RequestContext(request, {
            'vote': vote,
            'membervotes': membervotes,
            'parties_y': [pv.party for pv in partyvotes if pv.vote == 'Y'],
            'parties_n': [pv.party for pv in partyvotes if pv.vote == 'N']
        })
        t = loader.get_template("bills/votequestion_detail.html")
        return HttpResponse(t.render(c))
vote = VoteDetailView.as_view()


class BallotListView(ModelListView):

    resource_name = 'Ballots'

    filters = {
        'vote': APIFilters.fkey(lambda u: {'votequestion__session': u[-2],
                                           'votequestion__number': u[-1]},
                                help="e.g. /votes/41-1/472/"),
        'politician': APIFilters.politician(),
        'politician_membership': APIFilters.fkey(lambda u: {'member': u[-1]},
            help="e.g. /politicians/roles/326/"),
        'ballot': APIFilters.choices('vote', MemberVote),
        'dissent': APIFilters.dbfield('dissent',
            help="does this look like a vote against party line? not reliable for research. True, False")
    }

    def get_qs(self, request):
        return MemberVote.objects.all().select_related(
            'votequestion').order_by('-votequestion__date', '-votequestion__number')

    def object_to_dict(self, obj):
        return obj.to_api_dict(representation='list')
ballots = BallotListView.as_view()

class BillListFeed(Feed):
    title = 'Bills in the House of Commons'
    description = 'New bills introduced to the House, from openparliament.ca.'
    link = "/bills/"
    
    def items(self):
        return Bill.objects.filter(introduced__isnull=False).order_by('-introduced', 'number_only')[:25]
    
    def item_title(self, item):
        return "Bill %s (%s)" % (item.number,
            "Private member's" if item.privatemember else "Government")
    
    def item_description(self, item):
        return item.name
        
    def item_link(self, item):
        return item.get_absolute_url()
        
    
class BillFeed(Feed):

    def get_object(self, request, bill_id):
        return get_object_or_404(Bill, pk=bill_id)

    def title(self, bill):
        return "Bill %s" % bill.number

    def link(self, bill):
        return "http://openparliament.ca" + bill.get_absolute_url()

    def description(self, bill):
        return "From openparliament.ca, speeches about Bill %s, %s" % (bill.number, bill.name)

    def items(self, bill):
        statements = bill.statement_set.all().order_by('-time', '-sequence').select_related('member', 'member__politician', 'member__riding', 'member__party')[:10]
        votes = bill.votequestion_set.all().order_by('-date', '-number')[:3]
        merged = list(votes) + list(statements)
        merged.sort(key=lambda i: i.date, reverse=True)
        return merged

    def item_title(self, item):
        if isinstance(item, VoteQuestion):
            return "Vote #%s (%s)" % (item.number, item.get_result_display())
        else:
            return "%(name)s (%(party)s%(date)s)" % {
                'name': item.name_info['display_name'],
                'party': item.member.party.short_name + '; ' if item.member else '',
                'date': format_date(item.time, "F jS"),
            }

    def item_link(self, item):
        return item.get_absolute_url()

    def item_description(self, item):
        if isinstance(item, Statement):
            return item.text_html()
        else:
            return item.description

    def item_pubdate(self, item):
        return datetime.datetime(item.date.year, item.date.month, item.date.day)

########NEW FILE########
__FILENAME__ = vote_urls
from django.conf.urls import *

urlpatterns = patterns('parliament.bills.views',
    url(r'^$', 'votes_for_session', name='votes'),
    (r'^(?:session/)?(?P<session_id>\d+-\d)/$', 'votes_for_session'),
    url(r'^(?P<session_id>\d+-\d)/(?P<number>\d+)/$', 'vote', name='vote'),
    (r'^(?P<vote_id>\d+)/$', 'vote_pk_redirect'),
    url(r'^ballots/$', 'ballots', name='vote_ballots'),
)
########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.committees.models import *

class CommitteeAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'slug', 'latest_session', 'display')
    list_filter = ('sessions', 'display')

class CommitteeInSessionAdmin(admin.ModelAdmin):
    list_display = ('committee', 'acronym', 'session')

class MeetingAdmin(admin.ModelAdmin):
    list_display = ('committee', 'number', 'date', 'start_time', 'end_time', 'notice', 'minutes', 'evidence',
        'in_camera')
    list_filter = ('committee', 'date')
    
class ReportAdmin(admin.ModelAdmin):
    list_display = ('committee', 'number', 'session', 'name', 'government_response')
    list_filter = ('committee', 'session', 'government_response')
    
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'committee', 'study')
    list_filter = ('committee', 'study')

admin.site.register(Committee, CommitteeAdmin)
admin.site.register(CommitteeInSession, CommitteeInSessionAdmin)
admin.site.register(CommitteeMeeting, MeetingAdmin)
admin.site.register(CommitteeReport, ReportAdmin)
admin.site.register(CommitteeActivity, ActivityAdmin)
########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Committee'
        db.create_table('committees_committee', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('short_name', self.gf('django.db.models.fields.TextField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='subcommittees', null=True, to=orm['committees.Committee'])),
        ))
        db.send_create_signal('committees', ['Committee'])

        # Adding model 'CommitteeInSession'
        db.create_table('committees_committeeinsession', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Session'])),
            ('committee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['committees.Committee'])),
            ('acronym', self.gf('django.db.models.fields.CharField')(max_length=5, db_index=True)),
        ))
        db.send_create_signal('committees', ['CommitteeInSession'])

        # Adding model 'CommitteeActivity'
        db.create_table('committees_committeeactivity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('committee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['committees.Committee'])),
            ('source_id', self.gf('django.db.models.fields.IntegerField')()),
            ('name_en', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('name_fr', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('study', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('committees', ['CommitteeActivity'])

        # Adding model 'CommitteeMeeting'
        db.create_table('committees_committeemeeting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('start_time', self.gf('django.db.models.fields.TimeField')()),
            ('end_time', self.gf('django.db.models.fields.TimeField')(null=True, blank=True)),
            ('committee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['committees.Committee'])),
            ('number', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Session'])),
            ('minutes', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('notice', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('evidence', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hansards.Document'], unique=True, null=True, blank=True)),
            ('in_camera', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('travel', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('webcast', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('televised', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('committees', ['CommitteeMeeting'])

        # Adding M2M table for field activities on 'CommitteeMeeting'
        db.create_table('committees_committeemeeting_activities', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('committeemeeting', models.ForeignKey(orm['committees.committeemeeting'], null=False)),
            ('committeeactivity', models.ForeignKey(orm['committees.committeeactivity'], null=False))
        ))
        db.create_unique('committees_committeemeeting_activities', ['committeemeeting_id', 'committeeactivity_id'])

        # Adding model 'CommitteeReport'
        db.create_table('committees_committeereport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('committee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['committees.Committee'])),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Session'])),
            ('number', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('source_id', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('adopted_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('presented_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('government_response', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['committees.CommitteeReport'])),
        ))
        db.send_create_signal('committees', ['CommitteeReport'])


    def backwards(self, orm):
        
        # Deleting model 'Committee'
        db.delete_table('committees_committee')

        # Deleting model 'CommitteeInSession'
        db.delete_table('committees_committeeinsession')

        # Deleting model 'CommitteeActivity'
        db.delete_table('committees_committeeactivity')

        # Deleting model 'CommitteeMeeting'
        db.delete_table('committees_committeemeeting')

        # Removing M2M table for field activities on 'CommitteeMeeting'
        db.delete_table('committees_committeemeeting_activities')

        # Deleting model 'CommitteeReport'
        db.delete_table('committees_committeereport')


    models = {
        'committees.committee': {
            'Meta': {'ordering': "['name']", 'object_name': 'Committee'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcommittees'", 'null': 'True', 'to': "orm['committees.Committee']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['committees.CommitteeInSession']", 'symmetrical': 'False'}),
            'short_name': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'committees.committeeactivity': {
            'Meta': {'object_name': 'CommitteeActivity'},
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {}),
            'study': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeeinsession': {
            'Meta': {'object_name': 'CommitteeInSession'},
            'acronym': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'committees.committeemeeting': {
            'Meta': {'object_name': 'CommitteeMeeting'},
            'activities': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['committees.CommitteeActivity']", 'symmetrical': 'False'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hansards.Document']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_camera': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'minutes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notice': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'televised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'travel': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'webcast': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeereport': {
            'Meta': {'object_name': 'CommitteeReport'},
            'adopted_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'government_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['committees.CommitteeReport']"}),
            'presented_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['committees']

########NEW FILE########
__FILENAME__ = 0002_activities_and_constraints
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'CommitteeActivityInSession'
        db.create_table('committees_committeeactivityinsession', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('activity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['committees.CommitteeActivity'])),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Session'])),
            ('source_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
        ))
        db.send_create_signal('committees', ['CommitteeActivityInSession'])

        # Adding unique constraint on 'CommitteeActivityInSession', fields ['activity', 'session']
        db.create_unique('committees_committeeactivityinsession', ['activity_id', 'session_id'])

        # Adding index on 'CommitteeMeeting', fields ['date']
        db.create_index('committees_committeemeeting', ['date'])

        # Adding unique constraint on 'CommitteeMeeting', fields ['session', 'number', 'committee']
        db.create_unique('committees_committeemeeting', ['session_id', 'number', 'committee_id'])

        # Deleting field 'CommitteeActivity.source_id'
        db.delete_column('committees_committeeactivity', 'source_id')

        # Adding unique constraint on 'CommitteeInSession', fields ['session', 'committee']
        db.create_unique('committees_committeeinsession', ['session_id', 'committee_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'CommitteeInSession', fields ['session', 'committee']
        db.delete_unique('committees_committeeinsession', ['session_id', 'committee_id'])

        # Removing unique constraint on 'CommitteeMeeting', fields ['session', 'number', 'committee']
        db.delete_unique('committees_committeemeeting', ['session_id', 'number', 'committee_id'])

        # Removing index on 'CommitteeMeeting', fields ['date']
        db.delete_index('committees_committeemeeting', ['date'])

        # Removing unique constraint on 'CommitteeActivityInSession', fields ['activity', 'session']
        db.delete_unique('committees_committeeactivityinsession', ['activity_id', 'session_id'])

        # Deleting model 'CommitteeActivityInSession'
        db.delete_table('committees_committeeactivityinsession')

        # We cannot add back in field 'CommitteeActivity.source_id'
        raise RuntimeError(
            "Cannot reverse this migration. 'CommitteeActivity.source_id' and its values cannot be restored.")


    models = {
        'committees.committee': {
            'Meta': {'ordering': "['name']", 'object_name': 'Committee'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcommittees'", 'null': 'True', 'to': "orm['committees.Committee']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['committees.CommitteeInSession']", 'symmetrical': 'False'}),
            'short_name': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'committees.committeeactivity': {
            'Meta': {'object_name': 'CommitteeActivity'},
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'study': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeeactivityinsession': {
            'Meta': {'unique_together': "[('activity', 'session')]", 'object_name': 'CommitteeActivityInSession'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.CommitteeActivity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        'committees.committeeinsession': {
            'Meta': {'unique_together': "[('session', 'committee')]", 'object_name': 'CommitteeInSession'},
            'acronym': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'committees.committeemeeting': {
            'Meta': {'unique_together': "[('session', 'committee', 'number')]", 'object_name': 'CommitteeMeeting'},
            'activities': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['committees.CommitteeActivity']", 'symmetrical': 'False'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hansards.Document']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_camera': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'minutes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notice': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'televised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'travel': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'webcast': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeereport': {
            'Meta': {'object_name': 'CommitteeReport'},
            'adopted_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'government_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['committees.CommitteeReport']"}),
            'presented_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['committees']

########NEW FILE########
__FILENAME__ = 0003_acronym_constraint
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding unique constraint on 'CommitteeInSession', fields ['acronym', 'session']
        db.create_unique('committees_committeeinsession', ['acronym', 'session_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'CommitteeInSession', fields ['acronym', 'session']
        db.delete_unique('committees_committeeinsession', ['acronym', 'session_id'])


    models = {
        'committees.committee': {
            'Meta': {'ordering': "['name']", 'object_name': 'Committee'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcommittees'", 'null': 'True', 'to': "orm['committees.Committee']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['committees.CommitteeInSession']", 'symmetrical': 'False'}),
            'short_name': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'committees.committeeactivity': {
            'Meta': {'object_name': 'CommitteeActivity'},
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'study': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeeactivityinsession': {
            'Meta': {'unique_together': "[('activity', 'session')]", 'object_name': 'CommitteeActivityInSession'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.CommitteeActivity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        'committees.committeeinsession': {
            'Meta': {'unique_together': "[('session', 'committee'), ('session', 'acronym')]", 'object_name': 'CommitteeInSession'},
            'acronym': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'committees.committeemeeting': {
            'Meta': {'unique_together': "[('session', 'committee', 'number')]", 'object_name': 'CommitteeMeeting'},
            'activities': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['committees.CommitteeActivity']", 'symmetrical': 'False'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hansards.Document']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_camera': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'minutes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notice': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'televised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'travel': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'webcast': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeereport': {
            'Meta': {'object_name': 'CommitteeReport'},
            'adopted_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'government_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['committees.CommitteeReport']"}),
            'presented_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['committees']

########NEW FILE########
__FILENAME__ = 0004_add_display
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Committee.display'
        db.add_column('committees_committee', 'display', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Committee.display'
        db.delete_column('committees_committee', 'display')


    models = {
        'committees.committee': {
            'Meta': {'ordering': "['name']", 'object_name': 'Committee'},
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcommittees'", 'null': 'True', 'to': "orm['committees.Committee']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['committees.CommitteeInSession']", 'symmetrical': 'False'}),
            'short_name': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'committees.committeeactivity': {
            'Meta': {'object_name': 'CommitteeActivity'},
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'study': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeeactivityinsession': {
            'Meta': {'unique_together': "[('activity', 'session')]", 'object_name': 'CommitteeActivityInSession'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.CommitteeActivity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        'committees.committeeinsession': {
            'Meta': {'unique_together': "[('session', 'committee'), ('session', 'acronym')]", 'object_name': 'CommitteeInSession'},
            'acronym': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'committees.committeemeeting': {
            'Meta': {'unique_together': "[('session', 'committee', 'number')]", 'object_name': 'CommitteeMeeting'},
            'activities': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['committees.CommitteeActivity']", 'symmetrical': 'False'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hansards.Document']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_camera': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'minutes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notice': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'televised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'travel': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'webcast': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeereport': {
            'Meta': {'object_name': 'CommitteeReport'},
            'adopted_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'government_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['committees.CommitteeReport']"}),
            'presented_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['committees']

########NEW FILE########
__FILENAME__ = 0005_enfr
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        db.rename_column('committees_committee', 'name', 'name_en')
        db.rename_column('committees_committee', 'short_name', 'short_name_en')

        # Adding field 'Committee.name_fr'
        db.add_column('committees_committee', 'name_fr', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Committee.short_name_fr'
        db.add_column('committees_committee', 'short_name_fr', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        db.rename_column('committees_committeereport', 'name', 'name_en')

        # Adding field 'CommitteeReport.name_fr'
        db.add_column('committees_committeereport', 'name_fr', self.gf('django.db.models.fields.CharField')(default='', max_length=500, blank=True), keep_default=False)


    def backwards(self, orm):
        
        db.rename_column('committees_committee', 'name_en', 'name')

        db.rename_column('committees_committee', 'short_name_en', 'short_name')

        # Deleting field 'Committee.name_fr'
        db.delete_column('committees_committee', 'name_fr')

        # Deleting field 'Committee.short_name_fr'
        db.delete_column('committees_committee', 'short_name_fr')

        db.rename_column('committees_committeereport', 'name_en', 'name')

        # Deleting field 'CommitteeReport.name_fr'
        db.delete_column('committees_committeereport', 'name_fr')


    models = {
        'committees.committee': {
            'Meta': {'ordering': "['name_en']", 'object_name': 'Committee'},
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.TextField', [], {}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcommittees'", 'null': 'True', 'to': "orm['committees.Committee']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['committees.CommitteeInSession']", 'symmetrical': 'False'}),
            'short_name_en': ('django.db.models.fields.TextField', [], {}),
            'short_name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'committees.committeeactivity': {
            'Meta': {'object_name': 'CommitteeActivity'},
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'study': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeeactivityinsession': {
            'Meta': {'unique_together': "[('activity', 'session')]", 'object_name': 'CommitteeActivityInSession'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.CommitteeActivity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        'committees.committeeinsession': {
            'Meta': {'unique_together': "[('session', 'committee'), ('session', 'acronym')]", 'object_name': 'CommitteeInSession'},
            'acronym': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'committees.committeemeeting': {
            'Meta': {'unique_together': "[('session', 'committee', 'number')]", 'object_name': 'CommitteeMeeting'},
            'activities': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['committees.CommitteeActivity']", 'symmetrical': 'False'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hansards.Document']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_camera': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'minutes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notice': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'televised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'travel': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'webcast': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'committees.committeereport': {
            'Meta': {'object_name': 'CommitteeReport'},
            'adopted_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['committees.Committee']"}),
            'government_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'number': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['committees.CommitteeReport']"}),
            'presented_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['committees']

########NEW FILE########
__FILENAME__ = models
import datetime
import random
import string

from django.conf import settings
from django.db import models

from parliament.core.models import Session
from parliament.core.parsetools import slugify
from parliament.core.templatetags.ours import english_list
from parliament.core.utils import memoize_property, language_property
from parliament.hansards.models import Document, url_from_docid

class CommitteeManager(models.Manager):

    def get_by_acronym(self, acronym, session):
        try:
            return CommitteeInSession.objects.get(acronym=acronym, session=session).committee
        except CommitteeInSession.DoesNotExist:
            raise Committee.DoesNotExist()

class Committee(models.Model):
    
    name_en = models.TextField()
    short_name_en = models.TextField()
    name_fr = models.TextField(blank=True)
    short_name_fr = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', related_name='subcommittees',
        blank=True, null=True)
    sessions = models.ManyToManyField(Session, through='CommitteeInSession')

    display = models.BooleanField('Display on site?', db_index=True, default=True)

    objects = CommitteeManager()

    name = language_property('name')
    short_name = language_property('short_name')
    
    class Meta:
        ordering = ['name_en']
        
    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_name_en:
            self.short_name_en = self.name_en
        if not self.short_name_fr:
            self.short_name_fr = self.name_fr
        if not self.slug:
            self.slug = slugify(self.short_name_en, allow_numbers=True)
            if self.parent:
                self.slug = self.parent.slug + '-' + self.slug
            self.slug = self.slug[:46]
            while Committee.objects.filter(slug=self.slug).exists():
                self.slug += '-' + random.choice(string.lowercase)
        super(Committee, self).save(*args, **kwargs)
    
    @models.permalink
    def get_absolute_url(self):
        return ('parliament.committees.views.committee', [],
            {'slug': self.slug})

    def get_source_url(self):
        return self.committeeinsession_set.order_by('-session__start')[0].get_source_url()

    def get_acronym(self, session):
        return CommitteeInSession.objects.get(
            committee=self, session=session).acronym

    def latest_session(self):
        return self.sessions.order_by('-start')[0]

    @property
    def title(self):
        if 'committee' in self.name_en.lower():
            return self.name
        else:
            return self.name + u' Committee'

    def to_api_dict(self, representation):
        d = dict(
            name={'en': self.name_en, 'fr': self.name_fr},
            short_name={'en': self.short_name_en, 'fr': self.short_name_fr},
            slug=self.slug,
            parent_url=self.parent.get_absolute_url() if self.parent else None,
        )
        if representation == 'detail':
            d['sessions'] = [{
                    'session': cis.session_id,
                    'acronym': cis.acronym,
                    'source_url': cis.get_source_url(),
                } for cis in self.committeeinsession_set.all().order_by('-session__end').select_related('session')]
            d['subcommittees'] = [c.get_absolute_url() for c in self.subcommittees.all()]
        return d


class CommitteeInSession(models.Model):
    session = models.ForeignKey(Session)
    committee = models.ForeignKey(Committee)
    acronym = models.CharField(max_length=5, db_index=True)

    class Meta:
        unique_together = [
            ('session', 'committee'),
            ('session', 'acronym'),
        ]

    def __unicode__(self):
        return u"%s (%s) in %s" % (self.committee, self.acronym, self.session_id)

    def get_source_url(self):
        return 'http://parl.gc.ca/CommitteeBusiness/CommitteeHome.aspx?Cmte=%(acronym)s&Language=%(lang)s&Mode=1&Parl=%(parliamentnum)s&Ses=%(sessnum)s' % {
            'acronym': self.acronym,
            'lang': settings.LANGUAGE_CODE.upper()[0],
            'parliamentnum': self.session.parliamentnum,
            'sessnum': self.session.sessnum
        }


class CommitteeActivity(models.Model):
    
    committee = models.ForeignKey(Committee)

    name_en = models.CharField(max_length=500)
    name_fr = models.CharField(max_length=500)
    
    study = models.BooleanField(default=False) # study or activity

    name = language_property('name')
    
    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('committee_activity', [], {'activity_id': self.id})

    def get_source_url(self):
        return self.committeeactivityinsession_set.order_by('-session__start')[0].get_source_url()

    @property
    def type(self):
        return 'Study' if self.study else 'Activity'

    class Meta:
        verbose_name_plural = 'Committee activities'

class CommitteeActivityInSession(models.Model):

    activity = models.ForeignKey(CommitteeActivity)
    session = models.ForeignKey(Session)
    source_id = models.IntegerField(unique=True)

    def get_source_url(self):
        return 'http://www.parl.gc.ca/CommitteeBusiness/StudyActivityHome.aspx?Stac=%(source_id)d&Parl=%(parliamentnum)d&Ses=%(sessnum)d' % {
            'source_id': self.source_id,
            'parliamentnum': self.session.parliamentnum,
            'sessnum': self.session.sessnum
        }

    class Meta:
        unique_together = [
            ('activity', 'session')
        ]
        
class CommitteeMeeting(models.Model):
    
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    
    committee = models.ForeignKey(Committee)
    number = models.SmallIntegerField()
    session = models.ForeignKey(Session)
    
    minutes = models.IntegerField(blank=True, null=True) #docid
    notice = models.IntegerField(blank=True, null=True)
    evidence = models.OneToOneField(Document, blank=True, null=True)
    
    in_camera = models.BooleanField(default=False)
    travel = models.BooleanField(default=False)
    webcast = models.BooleanField(default=False)
    televised = models.BooleanField(default=False)
    
    activities = models.ManyToManyField(CommitteeActivity)

    class Meta:
        unique_together = [
            ('session', 'committee', 'number')
        ]
    
    def __unicode__(self):
        return u"%s on %s" % (self.committee.short_name, self.date)

    def to_api_dict(self, representation):
        d = dict(
            date=unicode(self.date),
            number=self.number,
            in_camera=self.in_camera,
            has_evidence=bool(self.evidence_id),
            committee_url=self.committee.get_absolute_url(),
        )
        if representation == 'detail':
            d.update(
                start_time=unicode(self.start_time),
                end_time=unicode(self.end_time),
                session=self.session_id,
                minutes_url=self.minutes_url if self.minutes else None,
                notice_url=self.notice_url if self.notice else None,
                webcast_url=self.webcast_url
            )
        return d

    @memoize_property
    def activities_list(self):
        return list(self.activities.all().order_by('-study'))
    
    def activities_summary(self):
        activities = self.activities_list()
        if not activities:
            return None
        if activities[0].study:
            # We have studies, so get rid of the more boring activities
            activities = filter(lambda a: a.study, activities)
        return english_list(map(lambda a: a.name_en, activities))

    @models.permalink
    def get_absolute_url(self, pretty=True):
        slug = self.committee.slug if pretty else self.committee_id
        return ('committee_meeting', [],
            {'session_id': self.session_id, 'committee_slug': slug,
             'number': self.number})

    @property
    def minutes_url(self):
        return url_from_docid(self.minutes)

    @property
    def notice_url(self):
        return url_from_docid(self.notice)

    @property
    def webcast_url(self):
        return 'http://www.parl.gc.ca/CommitteeBusiness/CommitteeMeetings.aspx?Cmte=%(acronym)s&Mode=1&ControlCallback=pvuWebcast&Parl=%(parliamentnum)d&Ses=%(sessnum)d&Organization=%(acronym)s&MeetingNumber=%(meeting_number)d&Language=%(language)s&NoJavaScript=true' % {
            'acronym': self.committee.get_acronym(self.session),
            'parliamentnum': self.session.parliamentnum,
            'sessnum': self.session.sessnum,
            'meeting_number': self.number,
            'language': settings.LANGUAGE_CODE[0].upper()
        } if self.webcast else None

    @property
    def datetime(self):
        return datetime.datetime.combine(self.date, self.start_time)

    @property
    def future(self):
        return self.datetime > datetime.datetime.now()

class CommitteeReport(models.Model):
    
    committee = models.ForeignKey(Committee)
    
    session = models.ForeignKey(Session)
    number = models.SmallIntegerField(blank=True, null=True) # watch this become a char
    name_en = models.CharField(max_length=500)
    name_fr = models.CharField(max_length=500, blank=True)

    
    source_id = models.IntegerField(unique=True, db_index=True)
    
    adopted_date = models.DateField(blank=True, null=True)
    presented_date = models.DateField(blank=True, null=True)
    
    government_response = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    name = language_property('name')
    
    def __unicode__(self):
        return u"%s report #%s" % (self.committee, self.number)

########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import *

from parliament.committees.views import *

urlpatterns = patterns('parliament.committees.views',
    url(r'^$', 'committee_list', name='committee_list'),
    url(r'^activities/(?P<activity_id>\d+)/$', 'committee_activity', name='committee_activity'),
    url(r'^meetings/$', CommitteeMeetingListView.as_view(), name='committee_meetings'),
    url(r'^(?P<slug>[^/]+)/(?P<year>2\d\d\d)/$', 'committee_year_archive', name='committee_year_archive'),
    url(r'^(?P<committee_slug>[^/]+)/(?P<session_id>\d+-\d)/(?P<number>\d+)/$', 'committee_meeting', name='committee_meeting'),
    url(r'^(?P<committee_slug>[^/]+)/(?P<session_id>\d+-\d)/(?P<number>\d+)/text-analysis/$', 'evidence_analysis'),
    url(r'^(?P<committee_slug>[^/]+)/(?P<session_id>\d+-\d)/(?P<number>\d+)/(?P<slug>[a-zA-Z0-9-]+)/$', 'committee_meeting_statement', name='committee_meeting'),
    url(r'^(?P<committee_slug>[^/]+)/(?P<session_id>\d+-\d)/(?P<number>\d+)/(?P<slug>[a-zA-Z0-9-]+)/only/$', 'evidence_permalink', name='evidence_permalink'),
    (r'^(?P<committee_id>\d+)/', 'committee_id_redirect'),
    (r'^(?P<slug>[^/]+)/$', 'committee'),
    url(r'^(?P<committee_slug>[^/]+)/analysis/$', CommitteeAnalysisView.as_view(), name='committee_analysis'),
)
########NEW FILE########
__FILENAME__ = views
import datetime
from urllib import urlencode

from django.conf import settings
from django.core import urlresolvers
from django.http import HttpResponse, HttpResponsePermanentRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.template import loader, RequestContext

from parliament.committees.models import Committee, CommitteeMeeting, CommitteeActivity
from parliament.core.api import ModelListView, ModelDetailView, APIFilters
from parliament.core.models import Session
from parliament.hansards.views import document_view, statement_permalink
from parliament.hansards.models import Statement, Document
from parliament.text_analysis.models import TextAnalysis
from parliament.text_analysis.views import TextAnalysisView


class CommitteeListView(ModelListView):

    resource_name = 'Committees'

    filters = {
        'session': APIFilters.dbfield('sessions')
    }

    def get_qs(self, request):
        qs = Committee.objects.filter(
            parent__isnull=True, display=True).order_by('name_' + settings.LANGUAGE_CODE)
        if 'session' not in request.GET:
            qs = qs.filter(sessions=Session.objects.current())
        return qs

    def get_html(self, request):
        committees = self.get_qs(request)
        recent_meetings = CommitteeMeeting.objects.order_by('-date')[:50]
        recent_studies = CommitteeActivity.objects.filter(
            study=True,
            committeemeeting__in=list(recent_meetings.values_list('id', flat=True))
        ).distinct()[:12]
        return render(request, "committees/committee_list.html", {
            'object_list': committees,
            'title': 'House Committees',
            'recent_studies': recent_studies
        })
committee_list = CommitteeListView.as_view()

def committee_id_redirect(request, committee_id):
    committee = get_object_or_404(Committee, pk=committee_id)
    return HttpResponsePermanentRedirect(request.path.replace(committee_id, committee.slug, 1))

class CommitteeView(ModelDetailView):

    resource_name = 'Committee'

    def get_object(self, request, slug):
        return get_object_or_404(Committee, slug=slug)

    def get_related_resources(self, request, qs, result):
        return {
            'meetings_url': urlresolvers.reverse('committee_meetings') + '?' +
                urlencode({'committee': self.kwargs['slug']}),
            'committees_url': urlresolvers.reverse('committee_list')
        }

    def get_html(self, request, slug):
        cmte = self.get_object(request, slug)
        recent_meetings = list(CommitteeMeeting.objects.filter(committee=cmte).order_by('-date')[:20])
        recent_studies = CommitteeActivity.objects.filter(
            study=True,
            committeemeeting__in=recent_meetings
        ).distinct()

        oldest_year = newest_year = meeting_years = None
        try:
            oldest_year = CommitteeMeeting.objects.filter(committee=cmte).order_by('date')[0].date.year
            newest_year = recent_meetings[0].date.year
            meeting_years = reversed(range(oldest_year, newest_year+1))
        except IndexError:
            pass

        title = cmte.name
        if 'Committee' not in title and not cmte.parent:
            title += u' Committee'

        t = loader.get_template("committees/committee_detail.html")
        c = RequestContext(request, {
            'title': title,
            'committee': cmte,
            'meetings': recent_meetings,
            'recent_studies': recent_studies,
            'archive_years': meeting_years,
            'subcommittees': Committee.objects.filter(parent=cmte, display=True, sessions=Session.objects.current()),
            'include_year': newest_year != datetime.date.today().year,
            'search_placeholder': u"Search %s transcripts" % cmte.short_name,
            'wordcloud_js': TextAnalysis.objects.get_wordcloud_js(
                urlresolvers.reverse('committee_analysis', kwargs={'committee_slug': slug})),
        })
        return HttpResponse(t.render(c))
committee = CommitteeView.as_view()        

def committee_year_archive(request, slug, year):
    cmte = get_object_or_404(Committee, slug=slug)
    year = int(year)

    meetings = list(
        CommitteeMeeting.objects.filter(committee=cmte, date__year=year).order_by('date')
    )
    studies = CommitteeActivity.objects.filter(
        study=True,
        committeemeeting__in=meetings
    ).distinct()

    return render(request, "committees/committee_year_archive.html", {
        'title': u"%s Committee in %s" % (cmte, year),
        'committee': cmte,
        'meetings': meetings,
        'studies': studies,
        'year': year
    })
    
def committee_activity(request, activity_id):
    activity = get_object_or_404(CommitteeActivity, id=activity_id)

    return render(request, "committees/committee_activity.html", {
        'title': unicode(activity),
        'activity': activity,
        'meetings': activity.committeemeeting_set.order_by('-date'),
        'committee': activity.committee
    })

def _get_meeting(committee_slug, session_id, number):
    try:
        return CommitteeMeeting.objects.select_related('evidence', 'committee').get(
            committee__slug=committee_slug, session=session_id, number=number)
    except CommitteeMeeting.DoesNotExist:
        raise Http404

class CommitteeMeetingListView(ModelListView):

    resource_name = 'Committee meetings'

    filters = {
        'number': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="each meeting in a session is given a sequential #"),
        'session': APIFilters.dbfield(help="e.g. 41-1"),
        'date': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="e.g. date__gt=2010-01-01"),
        'in_camera': APIFilters.dbfield(help="closed to the public? True, False"),
        'committee': APIFilters.fkey(lambda u: {'committee__slug': u[-1]},
            help="e.g. /committees/aboriginal-affairs")
    }

    def get_qs(self, request):
        return CommitteeMeeting.objects.all().order_by('-date')


class CommitteeMeetingView(ModelDetailView):

    resource_name = 'Committee meeting'

    def get_object(self, request, committee_slug, session_id, number):
        return _get_meeting(committee_slug, session_id, number)

    def get_related_resources(self, request, obj, result):
        if obj.evidence_id:
            return {
                'speeches_url': urlresolvers.reverse('speeches') + '?' +
                    urlencode({'document': result['url']})
            }

    def get_html(self, request, committee_slug, session_id, number, slug=None):
        meeting = self.get_object(request, committee_slug, session_id, number)

        document = meeting.evidence
        if document:
            return document_view(request, document, meeting=meeting, slug=slug)
        else:
            return render(request, "committees/meeting.html", {
                'meeting': meeting,
                'committee': meeting.committee
            })
committee_meeting = CommitteeMeetingView.as_view()

class EvidenceAnalysisView(TextAnalysisView):

    def get_qs(self, request, **kwargs):
        m = _get_meeting(**kwargs)
        if not m.evidence:
            raise Http404
        qs = m.evidence.statement_set.all()
        request.evidence = m.evidence
        # if 'party' in request.GET:
        #     qs = qs.filter(member__party__slug=request.GET['party'])
        return qs

    def get_corpus_name(self, request, committee_slug, **kwargs):
        return committee_slug

    def get_analysis(self, request, **kwargs):
        analysis = super(EvidenceAnalysisView, self).get_analysis(request, **kwargs)
        word = analysis.top_word
        if word and word != request.evidence.most_frequent_word:
            Document.objects.filter(id=request.evidence.id).update(most_frequent_word=word)
        return analysis

evidence_analysis = EvidenceAnalysisView.as_view()

class CommitteeAnalysisView(TextAnalysisView):

    expiry_days = 7

    def get_corpus_name(self, request, committee_slug):
        return committee_slug

    def get_qs(self, request, committee_slug):
        cmte = get_object_or_404(Committee, slug=committee_slug)
        qs = Statement.objects.filter(
            document__document_type='E',
            time__gte=datetime.datetime.now() - datetime.timedelta(days=30 * 6),
            document__committeemeeting__committee=cmte
        )
        return qs

class CommitteeMeetingStatementView(ModelDetailView):

    resource_name = 'Speech (committee meeting)'

    def get_object(self, request, committee_slug, session_id, number, slug):
        meeting = _get_meeting(committee_slug, session_id, number)
        return meeting.evidence.statement_set.get(slug=slug)

    def get_related_resources(self, request, qs, result):
        return {
            'document_speeches_url': urlresolvers.reverse('speeches') + '?' +
                urlencode({'document': result['document_url']}),
        }        

    def get_html(self, request, **kwargs):
        return committee_meeting(request, **kwargs)
committee_meeting_statement = CommitteeMeetingStatementView.as_view()


def evidence_permalink(request, committee_slug, session_id, number, slug):

    try:
        meeting = CommitteeMeeting.objects.select_related('evidence', 'committee').get(
            committee__slug=committee_slug, session=session_id, number=number)
    except CommitteeMeeting.DoesNotExist:
        raise Http404

    doc = meeting.evidence
    statement = get_object_or_404(Statement, document=doc, slug=slug)

    return statement_permalink(request, doc, statement, "committees/evidence_permalink.html",
        meeting=meeting, committee=meeting.committee)




########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.core.models import *

class PoliticianInfoInline(admin.TabularInline):
    model = PoliticianInfo

class PoliticianOptions (admin.ModelAdmin):
    inlines = [PoliticianInfoInline]
    search_fields = ('name',)
    
class RidingOptions (admin.ModelAdmin):
    list_display = ('name', 'province', 'edid')
    search_fields = ('name',)
    list_filter = ('province',)
    
class SessionOptions (admin.ModelAdmin):
    list_display = ('name', 'start', 'end')
    
class ElectedMemberOptions(admin.ModelAdmin):
    list_display=('politician', 'riding', 'party', 'start_date', 'end_date')
    list_filter=('party',)
    search_fields = ('politician__name',)
    
class InternalXrefOptions(admin.ModelAdmin):
    list_display = ('schema', 'text_value', 'int_value', 'target_id')
    search_fields = ('schema', 'text_value', 'int_value', 'target_id')
    list_editable = ('text_value', 'int_value', 'target_id')
    
class PartyOptions(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'slug')
    
class PoliticianInfoOptions(admin.ModelAdmin):
    list_display = ('politician', 'schema', 'value')
    search_fields = ('politician__name', 'schema', 'value')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "politician":
            kwargs["queryset"] = Politician.objects.elected()
            return db_field.formfield(**kwargs)
        return super(MyModelAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    
class SiteNewsOptions(admin.ModelAdmin):
    list_display = ('title', 'date', 'active')

admin.site.register(ElectedMember, ElectedMemberOptions)
admin.site.register(Riding, RidingOptions)
admin.site.register(Session, SessionOptions)
admin.site.register(Politician, PoliticianOptions)
admin.site.register(Party, PartyOptions)
admin.site.register(InternalXref, InternalXrefOptions)
admin.site.register(PoliticianInfo, PoliticianInfoOptions)
admin.site.register(SiteNews, SiteNewsOptions)


########NEW FILE########
__FILENAME__ = api
import json
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.middleware.cache import FetchFromCacheMiddleware as DjangoFetchFromCacheMiddleware
from django.shortcuts import render
from django.utils.html import escape
from django.views.generic import View

from webob.acceptparse import MIMEAccept


class APIView(View):

    # Set this to True to allow JSONP (cross-domain) requests
    allow_jsonp = False

    # Set to False to disallow CORS on GET requests, and the origin to allow otherwise
    allow_cors = '*'

    # Temporary: will need to write an actual versioning system once we want to start
    # preserving backwards compatibility
    api_version = 'v1'

    # The list of API formats should be ordered by preferability
    api_formats = [
        ('apibrowser', 'text/html'),
        ('json', 'application/json')
    ]

    # By default, if the Accept header doesn't match anything
    # we can provide, raise HTTP 406 Not Acceptable.
    # Alternatively, set this to a mimetype to be used
    # if there's no intersection between the Accept header
    # and our options.
    default_mimetype = 'application/json'

    resource_type = ''

    def __init__(self, *args, **kwargs):
        super(APIView, self).__init__(*args, **kwargs)

        if hasattr(self, 'get_json'):
            self.get_apibrowser = self.get_json

        self._formats_list = [f[0] for f in self.api_formats]
        self._mimetype_lookup = dict(
            (f[1], f[0]) for f in self.api_formats
        )

    def get_api_format(self, request):
        if request.GET.get('format') in self._formats_list:
            return request.GET['format']
        elif request.GET.get('format'):
            return None

        mimetype = MIMEAccept(request.META.get('HTTP_ACCEPT', 'application/json')).best_match(
            [f[1] for f in self.api_formats],
            default_match=self.default_mimetype
        )
        return self._mimetype_lookup[mimetype] if mimetype else None

    def dispatch(self, request, **kwargs):
        self.request = request
        self.kwargs = kwargs

        method = request.method.lower()

        request.api_request = (request.get_host().lower().startswith(settings.PARLIAMENT_API_HOST)
                              or request.GET.get('format'))

        if request.api_request:
            format = self.get_api_format(request)
            if not format:
                return self.format_not_allowed(request)
        else:
            # No format negotiation on non-API requests
            format = 'html'

            if hasattr(self, 'get_json'):
                request.apibrowser_url = '//' + settings.PARLIAMENT_API_HOST + request.path

        handler = getattr(self, '_'.join((method, format)), None)
        if handler is None:
            if method == 'get':
                return self.format_not_allowed(request)
            return self.http_method_not_allowed(request)
        try:
            result = handler(request, **kwargs)
        except BadRequest as e:
            return HttpResponseBadRequest(escape(unicode(e)), content_type='text/plain')

        processor = getattr(self, 'process_' + format, self.process_default)
        resp = processor(result, request, **kwargs)

        if self.allow_cors and method == 'get' and request.META.get('HTTP_ORIGIN'):
            # CORS
            resp['Access-Control-Allow-Origin'] = self.allow_cors

        resp['API-Version'] = self.api_version

        return resp

    def format_not_allowed(self, request):
        return HttpResponse("This resource is not available in the requested format.",
            content_type='text/plain', status=406)

    def process_default(self, result, request, **kwargs):
        return result

    def process_json(self, result, request, **kwargs):
        if isinstance(result, HttpResponse):
            return result
        
        pretty_print = (kwargs.pop('pretty_print')
            if kwargs.get('pretty_print') is not None
            else request.GET.get('indent'))

        resp = HttpResponse(content_type='application/json')
        callback = ''
        if self.allow_jsonp and 'callback' in request.GET:
            callback = re.sub(r'[^a-zA-Z0-9_]', '', request.GET['callback'])
            resp.write(callback + '(')
        if not isinstance(result, dict):
            result = {'content': result}
        json.dump(result, resp, indent=4 if pretty_print else None)
        if callback:
            resp.write(');')

        return resp

    def process_apibrowser(self, result, request, **kwargs):
        if isinstance(result, HttpResponse):
            return result

        kwargs['pretty_print'] = True
        content = self.process_json(result, request, **kwargs).content
        resource_name = getattr(self, 'resource_name', None)
        title = resource_name if resource_name else u'API'
        params = request.GET.copy()
        params['format'] = 'json'
        filters = [
            (f, getattr(self.filters[f], 'help', ''))
            for f in sorted(getattr(self, 'filters', {}).keys())
        ]
        ctx = dict(
            json=content,
            title=title,
            filters=filters,
            resource_name=resource_name,
            resource_type=self.resource_type,
            raw_json_url='?' + params.urlencode(),
            notes=getattr(self, 'api_notes', None)
        )
        if hasattr(self, 'get_html'):
            ctx['main_site_url'] = settings.SITE_URL + request.path
        return render(request, 'api/browser.html', ctx)


class APIFilters(object):

    string_filters = ['exact', 'iexact', 'contains', 'icontains',
        'startswith', 'istartswith', 'endswith', 'iendswith']

    numeric_filters = ['exact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'range']

    @staticmethod
    def dbfield(field_name=None, filter_types=['exact'], help=None):
        """Returns a filter function for a standard database query."""
        def inner(qs, view, filter_name, filter_extra, val):
            if not filter_extra:
                filter_extra = 'exact'
            if filter_extra not in filter_types:
                raise BadRequest("Invalid filter argument %s" % filter_extra)
            if val in ['true', 'True']:
                val = True
            elif val in ['false', 'False']:
                val = False
            elif val in ['none', 'None', 'null']:
                val = None
            if filter_extra == 'range':
                val = val.split(',')
            try:
                return qs.filter(**{
                    (field_name if field_name else filter_name) + '__' + filter_extra: val
                })
            except ValidationError as e:
                raise BadRequest(unicode(e))
        inner.help = help
        return inner

    @staticmethod
    def fkey(query_func, help=None):
        """Returns a filter function for a foreign-key field.
        The required argument is a function that takes an array 
        (the filter value split by '/'), and returns a dict of the ORM filters to apply.
        So a foreign key to a bill could accept an argument like
            "/bills/41-1/C-50"
        and query_func would be lambda u: {'bill__session': u[-2], 'bill__number': u[-1]}
        """
        def inner(qs, view, filter_name, filter_extra, val):
            url_bits = val.rstrip('/').split('/')
            return qs.filter(**(query_func(url_bits)))
        inner.help = help
        return inner

    @staticmethod
    def politician(field_name='politician'):
        return APIFilters.fkey(lambda u: ({field_name: u[-1]} if u[-1].isdigit()
            else {field_name + '__slug': u[-1]}),
            help="e.g. /politicians/tony-clement/")

    @staticmethod
    def choices(field_name, model):
        """Returns a filter function for a database field with defined choices;
        the filter will work whether provided the internal DB value or the display
        value."""
        choices = model._meta.get_field(field_name).choices
        def inner(qs, view, filter_name, filter_extra, val):
            try:
                search_val = next(c[0] for c in choices
                    if val in c)
            except StopIteration:
                raise BadRequest("Invalid value for %s" % filter_name)
            return qs.filter(**{field_name: search_val})
        inner.help = u', '.join(c[1] for c in choices)
        return inner

    @staticmethod
    def noop(help=None):
        """Returns a filter function that does nothing. Useful for when you want
        something to show up in autogenerated docs but are handling it elsewhere,
        e.g. by subclassing the main filter() method."""
        def inner(qs, view, filter_name, filter_extra, val):
            return qs
        inner.help = help
        return inner



class ModelListView(APIView):

    default_limit = 20

    resource_type = u'list'
    
    def object_to_dict(self, obj):
        d = obj.to_api_dict(representation='list')
        if 'url' not in d:
            d['url'] = obj.get_absolute_url()
        return d

    def get_qs(self, request, **kwargs):
        return self.model._default_manager.all()

    def filter(self, request, qs):
        for (f, val) in request.GET.items():
            filter_name, _, filter_extra = f.partition('__')
            if filter_name in getattr(self, 'filters', {}):
                qs = self.filters[filter_name](qs, self, filter_name, filter_extra, val)
        return qs

    def get_json(self, request, **kwargs):
        try:
            qs = self.get_qs(request, **kwargs)
        except ObjectDoesNotExist:
            raise Http404
        qs = self.filter(request, qs)

        paginator = APIPaginator(request, qs, limit=self.default_limit)
        (objects, page_data) = paginator.page()
        result = dict(
            objects=[self.object_to_dict(obj) for obj in objects],
            pagination=page_data
        )
        related = self.get_related_resources(request, qs, result)
        if related:
            result['related'] = related
        return result

    def get_related_resources(self, request, qs, result):
        return None


class ModelDetailView(APIView):

    resource_type = 'single'

    def object_to_dict(self, obj):
        d = obj.to_api_dict(representation='detail')
        if 'url' not in d:
            d['url'] = obj.get_absolute_url()
        return d

    def get_json(self, request, **kwargs):
        try:
            obj = self.get_object(request, **kwargs)
        except ObjectDoesNotExist:
            raise Http404
        result = self.object_to_dict(obj)
        related = self.get_related_resources(request, obj, result)
        if related:
            result['related'] = related
        return result

    def get_related_resources(self, request, obj, result):
        return None


def no_robots(request):
    if request.get_host().lower().startswith(settings.PARLIAMENT_API_HOST):
        return HttpResponse('User-agent: *\nDisallow: /\n', content_type='text/plain')
    return HttpResponse('', content_type='text/plain')

def docs(request):
    return render(request, 'api/doc.html', {'title': 'API'})


class FetchFromCacheMiddleware(DjangoFetchFromCacheMiddleware):
    # Since API resources are often served from the same URL as
    # main site resources, and we use Accept header negotiation to determine
    # formats, it's not a good fit with the full-site cache middleware.
    # So we'll just disable it for the API.

    def process_request(self, request):
        if request.get_host().lower().startswith(settings.PARLIAMENT_API_HOST):
            request._cache_update_cache = False
            return None
        return super(FetchFromCacheMiddleware, self).process_request(request)


class BadRequest(Exception):
    pass


class APIPaginator(object):
    """
    Largely cribbed from django-tastypie.
    """
    def __init__(self, request, objects, limit=None, offset=0, max_limit=500):
        """
        Instantiates the ``Paginator`` and allows for some configuration.

        The ``objects`` should be a list-like object of ``Resources``.
        This is typically a ``QuerySet`` but can be anything that
        implements slicing. Required.

        Optionally accepts a ``limit`` argument, which specifies how many
        items to show at a time. Defaults to ``None``, which is no limit.

        Optionally accepts an ``offset`` argument, which specifies where in
        the ``objects`` to start displaying results from. Defaults to 0.
        """
        self.request_data = request.GET
        self.objects = objects
        self.limit = limit
        self.max_limit = max_limit
        self.offset = offset
        self.resource_uri = request.path

    def get_limit(self):
        """
        Determines the proper maximum number of results to return.

        In order of importance, it will use:

            * The user-requested ``limit`` from the GET parameters, if specified.
            * The object-level ``limit`` if specified.
            * ``settings.API_LIMIT_PER_PAGE`` if specified.

        Default is 20 per page.
        """
        settings_limit = getattr(settings, 'API_LIMIT_PER_PAGE', 20)

        if 'limit' in self.request_data:
            limit = self.request_data['limit']
        elif self.limit is not None:
            limit = self.limit
        else:
            limit = settings_limit

        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer." % limit)

        if limit == 0:
            if self.limit:
                limit = self.limit
            else:
                limit = settings_limit

        if limit < 0:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer >= 0." % limit)

        if self.max_limit and limit > self.max_limit:
            return self.max_limit

        return limit

    def get_offset(self):
        """
        Determines the proper starting offset of results to return.

        It attempst to use the user-provided ``offset`` from the GET parameters,
        if specified. Otherwise, it falls back to the object-level ``offset``.

        Default is 0.
        """
        offset = self.offset

        if 'offset' in self.request_data:
            offset = self.request_data['offset']

        try:
            offset = int(offset)
        except ValueError:
            raise BadRequest("Invalid offset '%s' provided. Please provide an integer." % offset)

        if offset < 0:
            raise BadRequest("Invalid offset '%s' provided. Please provide a positive integer >= 0." % offset)

        return offset

    def _generate_uri(self, limit, offset):
        if self.resource_uri is None:
            return None

        # QueryDict has a urlencode method that can handle multiple values for the same key
        request_params = self.request_data.copy()
        if 'limit' in request_params:
            del request_params['limit']
        if 'offset' in request_params:
            del request_params['offset']
        request_params.update({'limit': limit, 'offset': max(offset, 0)})
        encoded_params = request_params.urlencode()

        return '%s?%s' % (
            self.resource_uri,
            encoded_params
        )

    def page(self):
        """
        Returns a tuple of (objects, page_data), where objects is one page of objects (a list),
        and page_data is a dict of pagination info.
        """
        limit = self.get_limit()
        offset = self.get_offset()

        page_data = {
            'offset': offset,
            'limit': limit,
        }

        # We get one more object than requested, to see if
        # there's a next page.
        objects = list(self.objects[offset:offset + limit + 1])
        if len(objects) > limit:
            objects.pop()
            page_data['next_url'] = self._generate_uri(limit, offset + limit)
        else:
            page_data['next_url'] = None

        page_data['previous_url'] = (self._generate_uri(limit, offset - limit)
            if offset > 0 else None)

        return (objects, page_data)

########NEW FILE########
__FILENAME__ = datautil
"""This file is mostly a dumping ground for various largely one-off data import and massaging routines.

Production code should NOT import from this file."""

import sys, re, urllib, urllib2, os, csv
from collections import defaultdict
import urlparse

from django.db import transaction, models
from django.db.models import Count
from django.core.files import File
from django.conf import settings

from parliament.core.models import *
from parliament.hansards.models import Statement
from parliament.elections.models import Election, Candidacy

def load_pol_pic(pol):
    print "#%d: %s" % (pol.id, pol)
    print pol.parlpage
    soup = BeautifulSoup(urllib2.urlopen(pol.parlpage))
    img = soup.find('img', id='MasterPage_MasterPage_BodyContent_PageContent_Content_TombstoneContent_TombstoneContent_ucHeaderMP_imgPhoto')
    if not img:
        raise Exception("Didn't work for %s" % pol.parlpage)
    imgurl = img['src']
    if '?' not in imgurl: # no query string
        imgurl = urllib.quote(imgurl.encode('utf8')) # but there might be accents!
    if 'BlankMPPhoto' in imgurl:
        print "Blank photo"
        return
    imgurl = urlparse.urljoin(pol.parlpage, imgurl)
    test = urllib2.urlopen(imgurl)
    content = urllib.urlretrieve(imgurl)
    #filename = urlparse.urlparse(imgurl).path.split('/')[-1]
    pol.headshot.save(str(pol.id) + ".jpg", File(open(content[0])), save=True)
    pol.save()

def delete_invalid_pol_pics():
    from PIL import Image
    for p in Politician.objects.exclude(headshot__isnull=True).exclude(headshot=''):
        try:
            Image.open(p.headshot)
        except IOError:
            print "DELETING image for %s" % p
            os.unlink(p.headshot.path)
            p.headshot = None
            p.save()
            
def delete_invalid_pol_urls():
    for pol in Politician.objects.filter(politicianinfo__schema='web_site').distinct():
        site = pol.info()['web_site']
        try:
            urllib2.urlopen(site)
            print "Success for %s" % site
        except urllib2.URLError, e:
            print "REMOVING %s " % site
            print e
            pol.politicianinfo_set.filter(schema='web_site').delete()
        
def export_words(outfile, queryset=None):
    if queryset is None:
        queryset = Statement.objects.all()
    for s in queryset.iterator():
        outfile.write(s.text_plain().encode('utf8'))
        outfile.write("\n")

def export_tokenized_words(outfile, queryset):
    for word in text_utils.qs_token_iterator(queryset, statement_separator="/"):
        outfile.write(word.encode('utf8'))
        outfile.write(' ')

def corpus_for_pol(pol):
    
    r_splitter = re.compile(r'[^\w\'\-]+', re.UNICODE)
    states = Statement.objects.filter(member__politician=pol).order_by('time', 'sequence')
    words = []
    for s in states:
        words.extend(re.split(r_splitter, s.text))
    return [w for w in words if len(w) > 0]

r_splitter = re.compile(r'[^\w\'\-]+', re.UNICODE)
def spark_index(bucketsize, bigrams=False):
    
    
    index = defaultdict(int)
    bucketidx = 0
    bucketcount = 0
    for s in Statement.objects.all().order_by('time'):
        tokens = re.split(r_splitter, s.text.lower())
        for t in tokens:
            if t != '':
                index[t[:15]] += 1
        bucketcount += len(tokens)
        if bucketcount >= bucketsize:
            # save
            for entry in index.iteritems():
                SparkIndex(token=entry[0], count=entry[1], bucket=bucketidx).save()
            index = defaultdict(int)
            bucketcount = 0
            bucketidx += 1
            
def get_parlinfo_ids(polset):
    
    for pol in polset:
        page = urllib2.urlopen(pol.parlpage)
        soup = BeautifulSoup(page)
        parlinfolink = soup.find('a', id='MasterPage_MasterPage_BodyContent_PageContent_Content_TombstoneContent_TombstoneContent_ucHeaderMP_hlFederalExperience')
        if not parlinfolink:
            print "Couldn't find on %s" % parlpage
        else:
            match = re.search(r'Item=(.+?)&', parlinfolink['href'])
            pol.save_parlinfo_id(match.group(1))
            print "Saved for %s" % pol

def normalize_hansard_urls():
    for h in Hansard.objects.all():
        normalized = parsetools.normalizeHansardURL(h.url)
        if normalized != h.url:
            h.url = normalized
            h.save()

def populate_members_by():
    for by in Election.objects.filter(byelection=True):
        print unicode(by)
        print "Enter session IDs: ",
        sessions = [Session.objects.get(pk=int(x)) for x in sys.stdin.readline().strip().split()]
        for session in sessions:
            print unicode(session)
            x = sys.stdin.readline()
            populate_members(by, session)

def populate_members(election, session, start_date):
    """ Label all winners in an election Members for the subsequent session. """
    for winner in Candidacy.objects.filter(election=election, elected=True):
        candidate = winner.candidate
        try:
            member = ElectedMember.objects.get(politician=candidate,
                party=winner.party, riding=winner.riding, end_date__isnull=True)
            member.sessions.add(session)
        except ElectedMember.DoesNotExist:
            em = ElectedMember.objects.create(
                politician=candidate, start_date=start_date,
                party=winner.party, riding=winner.riding)
            em.sessions.add(session)
            
def copy_members(from_session, to_session):
    raise Exception("Not yet implemented after ElectedMember refactor")
    for member in ElectedMember.objects.filter(session=from_session):
        ElectedMember(session=to_session, politician=member.politician, party=member.party, riding=member.riding).save()

def populate_parlid():
    for pol in Politician.objects.filter(parlpage__isnull=False):
        if pol.parlpage:
            match = re.search(r'Key=(\d+)', pol.parlpage)
            if not match:
                raise Exception("didn't match on %s" % pol.parlpage)
            pol.parlwebid = int(match.group(1))
            pol.save()

def replace_links(old, new):
    if old.__class__ != new.__class__:
        raise Exception("Are old and new the same type?")
    for relation in old._meta.get_all_related_objects():
        if relation.model == old.__class__:
            print "Relation to self!"
            continue
        print relation.field.name
        relation.model._default_manager.filter(**{relation.field.name: old}).update(**{relation.field.name: new})
    for relation in old._meta.get_all_related_many_to_many_objects():
        if relation.model == old.__class__:
            print "Relation to self!"
            continue
        print relation.field.name
        for obj in relation.model._default_manager.filter(**{relation.field.name: old}):
            getattr(obj, relation.field.name).remove(old)    
            getattr(obj, relation.field.name).add(new)        

def _merge_pols(good, bad):
    #ElectedMember.objects.filter(politician=bad).update(politician=good)
    #Candidacy.objects.filter(candidate=bad).update(candidate=good)
    #Statement.objects.filter(politician=bad).update(politician=good)
    replace_links(old=bad, new=good)
    seen = set()
    for xref in InternalXref.objects.filter(schema__startswith='pol_', target_id=bad.id):
        if (xref.int_value, xref.text_value) in seen:
            xref.delete()
        else:
            xref.target_id = good.id
            xref.save()
            seen.add((xref.int_value, xref.text_value))
    bad.delete()

    pi_seen = set()
    for pi in good.politicianinfo_set.all():
        val = (pi.schema, pi.value)
        if val in pi_seen:
            pi.delete()
        pi_seen.add(val)

#REFORM = (Party.objects.get(pk=25), Party.objects.get(pk=1), Party.objects.get(pk=28), Party.objects.get(pk=26))

def merge_by_party(parties):
    raise Exception("Not yet implemented after ElectedMember refactor")
    
    dupelist = Politician.objects.values('name').annotate(namecount=Count('name')).filter(namecount__gt=1).order_by('-namecount')
    for dupeset in dupelist:
        pols = Politician.objects.filter(name=dupeset['name'])
        province = None
        fail = False
        events = []
        for pol in pols:
            for em in ElectedMember.objects.filter(politician=pol):
                if em.party not in parties:
                    fail = True
                    print "%s not acceptable" % em.party
                    break
                if em.session in events:
                    fail = True
                    print "Duplicate event for %s, %s" % (pol, em.session)
                    events.append(em.session)
                    break
                if province is None:
                    province = em.riding.province
                elif em.riding.province != province:
                    fail = True
                    print "Province doesn't match for %s: %s, %s" % (pol, em.riding.province, province)
            for cand in Candidacy.objects.filter(candidate=pol):
                if cand.party not in parties:
                    fail = True
                    print "%s not acceptable" % cand.party
                    break
                if cand.election in events:
                    fail = True
                    print "Duplicate event for %s, %s" % (pol, cand.election)
                    events.append(cand.election)
                    break
                if province is None:
                    province = cand.riding.province
                elif cand.riding.province != province:
                    fail = True
                    print "Province doesn't match for %s: %s, %s" % (pol, cand.riding.province, province)
        if not fail:
            good = pols[0]
            bads = pols[1:]
            for bad in bads:
                _merge_pols(good, bad)
            print "Merged %s" % good

def merge_polnames():
    
    def _printout(pol):
        for em in ElectedMember.objects.filter(politician=pol):
            print em
        for cand in Candidacy.objects.filter(candidate=pol):
            print cand
    while True:
        print "Space-separated list of IDs: ",
        ids = sys.stdin.readline().strip().split()
        good = Politician.objects.get(pk=int(ids[0]))
        bads = [Politician.objects.get(pk=int(x)) for x in ids[1:]]
        _printout(good)
        for bad in bads: _printout(bad)
        print "Go? (y/n) ",
        yn = sys.stdin.readline().strip().lower()
        if yn == 'y':
            for bad in bads:
                _merge_pols(good, bad)
            while True:
                print "Alternate name? ",
                alt = sys.stdin.readline().strip()
                if len(alt) > 5:
                    good.add_alternate_name(alt)
                else:
                    break
            print "Done!"
    
@transaction.commit_on_success
def merge_pols():
    print "Enter ID of primary pol object: "
    goodid = int(raw_input().strip())
    good = Politician.objects.get(pk=goodid)
    for em in ElectedMember.objects.filter(politician=good):
        print em
    for cand in Candidacy.objects.filter(candidate=good):
        print cand
    print "Enter ID of bad pol object: "
    badid = int(raw_input().strip())
    bad = Politician.objects.get(pk=badid)
    for em in ElectedMember.objects.filter(politician=bad):
        print em
    for cand in Candidacy.objects.filter(candidate=bad):
        print cand
    print "Go? (y/n) "
    yn = raw_input().strip().lower()
    if yn == 'y':
        _merge_pols(good, bad)
        print "Done!"
        
def fix_mac():
    """ Alexa Mcdonough -> Alexa McDonough """
    for p in Politician.objects.filter(models.Q(name_family__startswith='Mc')|models.Q(name_family__startswith='Mac')):
        nforig = p.name_family
        def mac_replace(match):
            return match.group(1) + match.group(2).upper()
        p.name_family = re.sub(r'(Ma?c)([a-z])', mac_replace, p.name_family)
        print p.name + " -> ",
        p.name = p.name.replace(nforig, p.name_family)
        print p.name
        p.save()
        
def check_for_feeds(urls):
    for url in urls:
        try:
            response = urllib2.urlopen(url)
        except Exception, e:
            print "ERROR on %s" % url
            print e
            continue
        soup = BeautifulSoup(response.read())
        for feed in soup.findAll('link', type='application/rss+xml'):
            print "FEED ON %s" % url
            print feed
            
def twitter_from_csv(infile):
    reader = csv.DictReader(infile)
    session = Session.objects.current()
    for line in reader:
        name = line['Name'].decode('utf8')
        surname = line['Surname'].decode('utf8')
        pol = Politician.objects.get_by_name(' '.join([name, surname]), session=session)
        PoliticianInfo.objects.get_or_create(politician=pol, schema='twitter', value=line['twitter'].strip())
        
def twitter_to_list():
    from twitter import Twitter
    twit = Twitter(settings.TWITTER_USERNAME, settings.TWITTER_PASSWORD)
    for t in PoliticianInfo.objects.filter(schema='twitter'):
        twit.openparlca.mps.members(id=t.value)
        
def slugs_for_pols(qs=None):
    if not qs:
        qs = Politician.objects.current()
    for pol in qs.filter(slug=''):
        slug = slugify(pol.name)
        if Politician.objects.filter(slug=slug).exists():
            print "WARNING: %s already taken" % slug
        else:
            pol.slug = slug
            pol.save()
            
def wikipedia_from_freebase():
    import freebase
    for info in PoliticianInfo.sr_objects.filter(schema='freebase_id'):
        query = {
            'id': info.value,
            'key': [{
                'namespace': '/wikipedia/en_id',
                'value': None
            }]
        }
        result = freebase.mqlread(query)
        if result:
            # freebase.api.mqlkey.unquotekey
            wiki_id = result['key'][0]['value']
            info.politician.set_info('wikipedia_id', wiki_id)
            
def freebase_id_from_parl_id():
    import freebase
    import time
    for info in PoliticianInfo.sr_objects.filter(schema='parl_id').order_by('value'):
        if PoliticianInfo.objects.filter(politician=info.politician, schema='freebase_id').exists():
            continue
        query = {
            'type': '/base/cdnpolitics/member_of_parliament',
            'id': [],
            'key': {
                'namespace': '/source/ca/gov/house',
                'value': info.value
            }
        }
        result = freebase.mqlread(query)
        print "result: %s" % result
        #time.sleep(1)
        if not result:
            try:
                print "Nothing for %s (%s)" % (info.value, info.politician)
            except:
                pass
        else:
            freebase_id = result['id'][0]
            PoliticianInfo(politician=info.politician, schema='freebase_id', value=freebase_id).save()
            print "Saved: %s" % freebase_id
            
def pol_urls_to_ids():
    for pol in Politician.objects.exclude(parlpage=''):
        if 'Item' in pol.parlpage and 'parlinfo_id' not in pol.info():
            print pol.parlpage
            match = re.search(r'Item=([A-Z0-9-]+)', pol.parlpage)
            pol.set_info('parlinfo_id', match.group(1))
        if 'Key' in pol.parlpage and 'parl_id' not in pol.info():
            print pol.parlpage
            match = re.search(r'Key=(\d+)', pol.parlpage)
            pol.set_info('parl_id', match.group(1))
            
def export_statements(outfile, qs):
    for s in qs.iterator():
        if not s.speaker:
            outfile.write(s.text_plain().encode('utf8'))
            outfile.write("\n")
########NEW FILE########
__FILENAME__ = errors
from django.conf import settings
from django.template import Context, loader

def server_error(request, template_name='500.html'):
    "Always includes MEDIA_URL"
    from django.http import HttpResponseServerError
    t = loader.get_template(template_name)
    return HttpResponseServerError(t.render(Context({
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL
    })))
########NEW FILE########
__FILENAME__ = fields
from django.conf import settings
from django import forms
from django.utils.encoding import smart_unicode

from recaptcha.client import captcha

from parliament.core.widgets import ReCaptchaWidget

class ReCaptchaField(forms.CharField):
    default_error_messages = {
        'captcha_invalid': u"That didn't match the displayed words. Sorry: we know this can be frustrating."
    }

    def __init__(self, *args, **kwargs):
        self.widget = ReCaptchaWidget
        self.required = True
        super(ReCaptchaField, self).__init__(*args, **kwargs)

    def clean(self, values):
        super(ReCaptchaField, self).clean(values[1])
        recaptcha_challenge_value = smart_unicode(values[0])
        recaptcha_response_value = smart_unicode(values[1])
        check_captcha = captcha.submit(recaptcha_challenge_value, 
            recaptcha_response_value, settings.RECAPTCHA_PRIVATE_KEY, {})
        if not check_captcha.is_valid:
            raise forms.util.ValidationError(self.error_messages['captcha_invalid'])
        return values[0]
########NEW FILE########
__FILENAME__ = forms
from django import forms

class Form(forms.Form):
    
    required_css_class = 'required'
    
    def __init__(self, *args, **kwargs):
        if 'label_suffix' not in kwargs:
            # We generally don't want automatic colons after field names
            kwargs['label_suffix'] = ''
        super(Form, self).__init__(*args, **kwargs)
        
    def _html_output(self, *args, **kwargs):
        for field in self.fields.values():
            if field.help_text:
                field.widget.attrs['data-helptext'] = field.help_text
                field.help_text = None

        return super(Form, self)._html_output(*args, **kwargs)
########NEW FILE########
__FILENAME__ = maint
from django import http
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import Context, loader, RequestContext


import datetime, re

def memcached_status(request):

    try:
        import memcache
    except ImportError:
        raise http.Http404

    if not (request.user.is_authenticated() and
            request.user.is_staff):
        raise http.Http404

    # get first memcached URI
    m = re.match(
        "memcached://([.\w]+:\d+)", settings.CACHE_BACKEND
    )
    if not m:
        raise http.Http404

    host = memcache._Host(m.group(1))
    host.connect()
    host.send_cmd("stats")

    class Stats:
        pass

    stats = Stats()

    while 1:
        line = host.readline().split(None, 2)
        if line[0] == "END":
            break
        stat, key, value = line
        try:
            # convert to native type, if possible
            value = int(value)
            if key == "uptime":
                value = datetime.timedelta(seconds=value)
            elif key == "time":
                value = datetime.datetime.fromtimestamp(value)
        except ValueError:
            pass
        setattr(stats, key, value)

    host.close_socket()

    return render_to_response(
        'memcached_status.html', dict(
            stats=stats,
            hit_rate=100 * stats.get_hits / stats.cmd_get,
            time=datetime.datetime.now(), # server time
        ), context_instance=RequestContext(request))
########NEW FILE########
__FILENAME__ = job
from optparse import make_option
import traceback
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import mail_admins

try:
    from pudb import post_mortem
except ImportError:
    from pdb import post_mortem

from parliament import jobs

class Command(BaseCommand):
    help = "Runs a job, which is a no-arguments function in the project's jobs.py"
    args = '[job name]'
    
    option_list = BaseCommand.option_list + (
        make_option('--pdb', action='store_true', dest='pdb', 
                    help='Launch into Python debugger on exception'),
    )
    
    def handle(self, jobname, **options):
        try:
            getattr(jobs, jobname)()
        except Exception, e:
            try:
                if options.get('pdb'):
                    post_mortem()
                else:
                    tb = "\n".join(traceback.format_exception(*(sys.exc_info())))
                    mail_admins("Exception in job %s" % jobname, "\n".join(traceback.format_exception(*(sys.exc_info()))))
            except:
                print tb
            finally:
                raise e
########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'InternalXref'
        db.create_table('core_internalxref', (
            ('int_value', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('text_value', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('target_id', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('schema', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal('core', ['InternalXref'])

        # Adding model 'Party'
        db.create_table('core_party', (
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('core', ['Party'])

        # Adding model 'Politician'
        db.create_table('core_politician', (
            ('name_given', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('parlpage', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('dob', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('site', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('name_family', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('core', ['Politician'])

        # Adding model 'Session'
        db.create_table('core_session', (
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('sessnum', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parliamentnum', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Session'])

        # Adding model 'Riding'
        db.create_table('core_riding', (
            ('province', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('edid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60)),
        ))
        db.send_create_signal('core', ['Riding'])

        # Adding model 'ElectedMember'
        db.create_table('core_electedmember', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'])),
            ('riding', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Riding'])),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Session'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Party'])),
        ))
        db.send_create_signal('core', ['ElectedMember'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'InternalXref'
        db.delete_table('core_internalxref')

        # Deleting model 'Party'
        db.delete_table('core_party')

        # Deleting model 'Politician'
        db.delete_table('core_politician')

        # Deleting model 'Session'
        db.delete_table('core_session')

        # Deleting model 'Riding'
        db.delete_table('core_riding')

        # Deleting model 'ElectedMember'
        db.delete_table('core_electedmember')
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {}),
            'text_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0002_member_rename
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        db.rename_column('core_electedmember', 'member_id', 'politician_id')
    
    
    def backwards(self, orm):
        
        db.rename_column('core_electedmember', 'politician_id', 'member_id')
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {}),
            'text_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0003_polpics
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Politician.headshot'
        db.add_column('core_politician', 'headshot', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting field 'Politician.headshot'
        db.delete_column('core_politician', 'headshot')
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {}),
            'text_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0004_electedmember_refactor
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'ElectedMember.end_date'
        db.add_column('core_electedmember', 'end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'ElectedMember.start_date'
        db.add_column('core_electedmember', 'start_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(1980, 3, 29)), keep_default=False)

        # Adding M2M table for field sessions on 'ElectedMember'
        db.create_table('core_electedmember_sessions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('electedmember', models.ForeignKey(orm['core.electedmember'], null=False)),
            ('session', models.ForeignKey(orm['core.session'], null=False))
        ))
        db.create_unique('core_electedmember_sessions', ['electedmember_id', 'session_id'])
    
    
    def backwards(self, orm):
        
        # Deleting field 'ElectedMember.end_date'
        db.delete_column('core_electedmember', 'end_date')

        # Deleting field 'ElectedMember.start_date'
        db.delete_column('core_electedmember', 'start_date')

        # Removing M2M table for field sessions on 'ElectedMember'
        db.delete_table('core_electedmember_sessions')
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sessionstmp'", 'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {}),
            'text_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0005_electedmember_refactor_data
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from parliament.hansards.models import Statement

class Migration(DataMigration):
    
    def forwards(self, orm):
        sessionsequence = {}
        sessions = {}
        sessquery = orm.Session.objects.all().order_by('start')
        for i in range(len(sessquery)):
            sessionsequence[sessquery[i].id] = i
            sessions[sessquery[i].id] = sessquery[i]
            
        def update_member(member):
            print "UPDATING,"
            sess = sessions[member.session_id]
            member.start_date = sess.start
            member.end_date = sess.end
            member.save()
            member.sessions.add(sess.id)
            return member
            
        def merge_members(master, merger):
            print "MERGING,"
            sess = sessions[merger.session_id]
            master.end_date = sess.end
            master.session_id = merger.session_id
            master.save()
            master.sessions.add(sess.id)
            Statement.objects.filter(member=merger).update(member=master)
            merger.delete()
            return master
        
        for pol in orm.Politician.objects.all().annotate(electedcount=models.Count('electedmember')).filter(electedcount__gte=1):
            print pol.name,
            # For each politician who's been elected
            members = orm.ElectedMember.objects.filter(politician=pol).order_by('session__start')
            last = None
            for member in members:
                if (last
                        and last.party == member.party
                        and last.riding == member.riding
                        and sessionsequence[member.session_id] == (sessionsequence[last.session_id] + 1)):
                    last = merge_members(master=last, merger=member)
                else:
                    last = update_member(member)
                
    
    
    def backwards(self, orm):
        "Write your backwards methods here."
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sessionstmp'", 'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {}),
            'text_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0006_electedmember_refactor_remove
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting field 'ElectedMember.session'
        db.delete_column('core_electedmember', 'session_id')
    
    
    def backwards(self, orm):
        
        # Adding field 'ElectedMember.session'
        db.add_column('core_electedmember', 'session', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['core.Session']), keep_default=False)
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {}),
            'text_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0007_party_shortname
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding index on 'ElectedMember', fields ['end_date']
        db.create_index('core_electedmember', ['end_date'])

        # Adding index on 'ElectedMember', fields ['start_date']
        db.create_index('core_electedmember', ['start_date'])

        # Adding field 'Party.colour'
        db.add_column('core_party', 'colour', self.gf('django.db.models.fields.CharField')(default='', max_length=7, blank=True), keep_default=False)

        # Adding field 'Party.short_name'
        db.add_column('core_party', 'short_name', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Removing index on 'ElectedMember', fields ['end_date']
        db.delete_index('core_electedmember', ['end_date'])

        # Removing index on 'ElectedMember', fields ['start_date']
        db.delete_index('core_electedmember', ['start_date'])

        # Deleting field 'Party.colour'
        db.delete_column('core_party', 'colour')

        # Deleting field 'Party.short_name'
        db.delete_column('core_party', 'short_name')
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {}),
            'text_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'colour': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0008_politician_info
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'PoliticianInfo'
        db.create_table('core_politicianinfo', (
            ('politician', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('schema', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
        ))
        db.send_create_signal('core', ['PoliticianInfo'])

        # Adding index on 'InternalXref', fields ['int_value']
        db.create_index('core_internalxref', ['int_value'])

        # Adding index on 'InternalXref', fields ['text_value']
        db.create_index('core_internalxref', ['text_value'])

        # Adding index on 'InternalXref', fields ['target_id']
        db.create_index('core_internalxref', ['target_id'])

        # Adding index on 'InternalXref', fields ['schema']
        db.create_index('core_internalxref', ['schema'])

        # Deleting field 'Party.colour'
        db.delete_column('core_party', 'colour')
    
    
    def backwards(self, orm):
        
        # Deleting model 'PoliticianInfo'
        db.delete_table('core_politicianinfo')

        # Removing index on 'InternalXref', fields ['int_value']
        db.delete_index('core_internalxref', ['int_value'])

        # Removing index on 'InternalXref', fields ['text_value']
        db.delete_index('core_internalxref', ['text_value'])

        # Removing index on 'InternalXref', fields ['target_id']
        db.delete_index('core_internalxref', ['target_id'])

        # Removing index on 'InternalXref', fields ['schema']
        db.delete_index('core_internalxref', ['schema'])

        # Adding field 'Party.colour'
        db.add_column('core_party', 'colour', self.gf('django.db.models.fields.CharField')(default='', max_length=7, blank=True), keep_default=False)
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text_value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.politicianinfo': {
            'Meta': {'object_name': 'PoliticianInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0009_pol_slug
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding index on 'Riding', fields ['edid']
        db.create_index('core_riding', ['edid'])

        # Adding index on 'Riding', fields ['slug']
        db.create_index('core_riding', ['slug'])

        # Adding field 'Politician.slug'
        db.add_column('core_politician', 'slug', self.gf('django.db.models.fields.CharField')(db_index=True, default='', max_length=30, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Removing index on 'Riding', fields ['edid']
        db.delete_index('core_riding', ['edid'])

        # Removing index on 'Riding', fields ['slug']
        db.delete_index('core_riding', ['slug'])

        # Deleting field 'Politician.slug'
        db.delete_column('core_politician', 'slug')
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text_value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.politicianinfo': {
            'Meta': {'object_name': 'PoliticianInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0010_sitenews
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'SiteNews'
        db.create_table('core_sitenews', (
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('core', ['SiteNews'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'SiteNews'
        db.delete_table('core_sitenews')
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text_value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.politicianinfo': {
            'Meta': {'object_name': 'PoliticianInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'core.sitenews': {
            'Meta': {'object_name': 'SiteNews'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0011_change_session_pk
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Note that this migration will almost certainly require manual database hacking...
        
        # Changing field 'Session.id'
        db.alter_column('core_session', 'id', self.gf('django.db.models.fields.CharField')(max_length=4, primary_key=True))
    
    
    def backwards(self, orm):
        
        # Changing field 'Session.id'
        db.alter_column('core_session', 'id', self.gf('django.db.models.fields.AutoField')(primary_key=True))
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text_value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.politicianinfo': {
            'Meta': {'object_name': 'PoliticianInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'core.sitenews': {
            'Meta': {'object_name': 'SiteNews'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0012_xref_to_polinfo
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        for xref in orm.InternalXref.objects.filter(schema__startswith='pol'):
            try:
                pol = orm.Politician.objects.get(pk=xref.target_id)
            except orm.Politician.DoesNotExist:
                print u"INVALID: %s" % xref
                continue
            info = orm.PoliticianInfo(politician=pol)
            if xref.schema == 'pol_names':
                info.schema = 'alternate_name'
                info.value = xref.text_value
            elif xref.schema == 'pol_parlid':
                info.schema = 'parl_id'
                info.value = unicode(xref.int_value)
            elif xref.schema == 'pol_parlinfoid':
                info.schema = 'parlinfo_id'
                info.value = xref.text_value
            else:
                raise Exception("Invalid schema %s" % xref.schema)
            info.save()

    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text_value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.politicianinfo': {
            'Meta': {'ordering': "('schema',)", 'object_name': 'PoliticianInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'core.sitenews': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'SiteNews'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0013_polinfo_text
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'PoliticianInfo.value'
        db.alter_column('core_politicianinfo', 'value', self.gf('django.db.models.fields.TextField')())


    def backwards(self, orm):
        
        # Changing field 'PoliticianInfo.value'
        db.alter_column('core_politicianinfo', 'value', self.gf('django.db.models.fields.CharField')(max_length=500))


    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text_value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.politicianinfo': {
            'Meta': {'object_name': 'PoliticianInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'core.sitenews': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'SiteNews'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = 0014_remove_site_parlpage
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Politician.site'
        db.delete_column('core_politician', 'site')

        # Deleting field 'Politician.parlpage'
        db.delete_column('core_politician', 'parlpage')


    def backwards(self, orm):
        
        # Adding field 'Politician.site'
        db.add_column('core_politician', 'site', self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Politician.parlpage'
        db.add_column('core_politician', 'parlpage', self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True), keep_default=False)


    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.internalxref': {
            'Meta': {'object_name': 'InternalXref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'target_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text_value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.politicianinfo': {
            'Meta': {'object_name': 'PoliticianInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'core.sitenews': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'SiteNews'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['core']

########NEW FILE########
__FILENAME__ = models
# coding: utf-8

import datetime
import re
import urllib2

from django.conf import settings
from django.core.cache import cache
from django.core import urlresolvers
from django.db import models
from django.template.defaultfilters import slugify

import lxml.html

from parliament.core import parsetools
from parliament.core.utils import memoize_property, ActiveManager

import logging
logger = logging.getLogger(__name__)

POL_LOOKUP_URL = 'http://www.parl.gc.ca/MembersOfParliament/ProfileMP.aspx?Key=%d&Language=E'

class InternalXref(models.Model):
    """A general-purpose table for quickly storing internal links."""
    text_value = models.CharField(max_length=50, blank=True, db_index=True)
    int_value = models.IntegerField(blank=True, null=True, db_index=True)
    target_id = models.IntegerField(db_index=True)
    
    # CURRENT SCHEMAS
    # party_names
    # bill_callbackid
    # session_legisin -- LEGISinfo ID for a session
    # edid_postcode -- the EDID -- which points to a riding, but is NOT the primary  key -- for a postcode
    schema = models.CharField(max_length=15, db_index=True)
    
    def __unicode__(self):
        return u"%s: %s %s for %s" % (self.schema, self.text_value, self.int_value, self.target_id)

class PartyManager(models.Manager):
    
    def get_by_name(self, name):
        x = InternalXref.objects.filter(schema='party_names', text_value=name.strip().lower())
        if len(x) == 0:
            raise Party.DoesNotExist()
        elif len(x) > 1:
            raise Exception("More than one party matched %s" % name.strip().lower())
        else:
            return self.get_query_set().get(pk=x[0].target_id)
            
class Party(models.Model):
    """A federal political party."""
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=10, blank=True)
    short_name = models.CharField(max_length=100, blank=True)
    
    objects = PartyManager()
    
    class Meta:
        verbose_name_plural = 'Parties'
        ordering = ('name',)
        
    def __init__(self, *args, **kwargs):
        # If we're creating a new object, set a flag to save the name to the alternate-names table.
        super(Party, self).__init__(*args, **kwargs)
        self._saveAlternate = True

    def save(self):
        if not getattr(self, 'short_name', None):
            self.short_name = self.name
        super(Party, self).save()
        if getattr(self, '_saveAlternate', False):
            self.add_alternate_name(self.name)

    def delete(self):
        InternalXref.objects.filter(schema='party_names', target_id=self.id).delete()
        super(Party, self).delete()

    def add_alternate_name(self, name):
        name = name.strip().lower()
        # check if exists
        x = InternalXref.objects.filter(schema='party_names', text_value=name)
        if len(x) == 0:
            InternalXref(schema='party_names', target_id=self.id, text_value=name).save()
        else:
            if x[0].target_id != self.id:
                raise Exception("Name %s already points to a different party" % name.strip().lower())
                
    def __unicode__(self):
        return self.name

class Person(models.Model):
    """Abstract base class for models representing a person."""
    
    name = models.CharField(max_length=100)
    name_given = models.CharField("Given name", max_length=50, blank=True)
    name_family = models.CharField("Family name", max_length=50, blank=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        abstract = True
        ordering = ('name',)

class PoliticianManager(models.Manager):
    
    def elected(self):
        """Returns a QuerySet of all politicians that were once elected to office."""
        return self.get_query_set().annotate(
            electedcount=models.Count('electedmember')).filter(electedcount__gte=1)
            
    def never_elected(self):
        """Returns a QuerySet of all politicians that were never elected as MPs.
        
        (at least during the time period covered by our database)"""
        return self.get_query_set().filter(electedmember__isnull=True)
        
    def current(self):
        """Returns a QuerySet of all current MPs."""
        return self.get_query_set().filter(electedmember__end_date__isnull=True,
            electedmember__start_date__isnull=False).distinct()
        
    def elected_but_not_current(self):
        """Returns a QuerySet of former MPs."""
        return self.get_query_set().exclude(electedmember__end_date__isnull=True)
    
    def filter_by_name(self, name):
        """Returns a list of politicians matching a given name."""
        return [i.politician for i in 
            PoliticianInfo.sr_objects.filter(schema='alternate_name', value=parsetools.normalizeName(name))]
    
    def get_by_name(self, name, session=None, riding=None, election=None, party=None, saveAlternate=True, strictMatch=False):
        """ Return a Politician by name. Uses a bunch of methods to try and deal with variations in names.
        If given any of a session, riding, election, or party, returns only politicians who match.
        If given session and optinally riding, tries to match the name more laxly.
        
        saveAlternate: If we have Thomas Mulcair and we match, via session/riding, to Tom Mulcair, save Tom
            in the alternate names table
        strictMatch: Even if given a session, don't try last-name-only matching.
        
        """
        
        # Alternate names for a pol are in the InternalXref table. Assemble a list of possibilities
        poss = PoliticianInfo.sr_objects.filter(schema='alternate_name', value=parsetools.normalizeName(name))
        if len(poss) >= 1:
            # We have one or more results
            if session or riding or party:
                # We've been given extra criteria -- see if they match
                result = None
                for p in poss:
                    # For each possibility, assemble a list of matching Members
                    members = ElectedMember.objects.filter(politician=p.politician)
                    if riding: members = members.filter(riding=riding)
                    if session: members = members.filter(sessions=session)
                    if party: members = members.filter(party=party)
                    if len(members) >= 1:
                        if result: # we found another match on a previous journey through the loop
                            # can't disambiguate, raise exception
                            raise Politician.MultipleObjectsReturned(name)
                        # We match! Save the result.
                        result = members[0].politician
                if result:
                    return result
            elif election:
                raise Exception("Election not implemented yet in Politician get_by_name")
            else:
                # No extra criteria -- return what we got (or die if we can't disambiguate)
                if len(poss) > 1:
                    raise Politician.MultipleObjectsReturned(name)
                else:
                    return poss[0].politician
        if session and not strictMatch:
            # We couldn't find the pol, but we have the session and riding, so let's give this one more shot
            # We'll try matching only on last name
            match = re.search(r'\s([A-Z][\w-]+)$', name.strip()) # very naive lastname matching
            if match:
                lastname = match.group(1)
                pols = self.get_query_set().filter(name_family=lastname, electedmember__sessions=session).distinct()
                if riding:
                    pols = pols.filter(electedmember__riding=riding)
                if len(pols) > 1:
                    if riding:
                        raise Exception("DATA ERROR: There appear to be two politicians with the same last name elected to the same riding from the same session... %s %s %s" % (lastname, session, riding))
                elif len(pols) == 1:
                    # yes!
                    pol = pols[0]
                    if saveAlternate:
                        pol.add_alternate_name(name) # save the name we were given as an alternate
                    return pol
        raise Politician.DoesNotExist("Could not find politician named %s" % name)
        
    def get_by_parlinfo_id(self, parlinfoid, session=None):
        PARLINFO_LOOKUP_URL = 'http://www2.parl.gc.ca/parlinfo/Files/Parliamentarian.aspx?Item=%s&Language=E'
        try:
            info = PoliticianInfo.sr_objects.get(schema='parlinfo_id', value=parlinfoid.lower())
            return info.politician
        except PoliticianInfo.DoesNotExist:
            print "Looking up parlinfo ID %s" % parlinfoid 
            parlinfourl = PARLINFO_LOOKUP_URL % parlinfoid
            parlinfopage = urllib2.urlopen(parlinfourl).read()
            match = re.search(
              r'href="http://webinfo\.parl\.gc\.ca/MembersOfParliament/ProfileMP\.aspx\?Key=(\d+)&amp;Language=E">MP profile',
              parlinfopage)
            if not match:
                raise Politician.DoesNotExist
            pol = self.get_by_parl_id(match.group(1), session=session)
            pol.save_parlinfo_id(parlinfoid)
            return pol

    def get_by_slug_or_id(self, slug_or_id):
        if slug_or_id.isdigit():
            return self.get(id=slug_or_id)
        return self.get(slug=slug_or_id)
    
    def get_by_parl_id(self, parlid, session=None, election=None, lookOnline=True):
        try:
            info = PoliticianInfo.sr_objects.get(schema='parl_id', value=unicode(parlid))
            return info.politician
        except PoliticianInfo.DoesNotExist:
            invalid_ID_cache_key = 'invalid-pol-parl-id-%s' % parlid
            if cache.get(invalid_ID_cache_key):
                raise Politician.DoesNotExist("ID %s cached as invalid" % parlid)
            if not lookOnline:
                return None # FIXME inconsistent behaviour: when should we return None vs. exception?
            #print "Unknown parlid %d... " % parlid,
            try:
                resp = urllib2.urlopen(POL_LOOKUP_URL % parlid)
                root = lxml.html.fromstring(resp.read())
            except urllib2.HTTPError:
                cache.set(invalid_ID_cache_key, True, 300)
                raise Politician.DoesNotExist("Couldn't open " + (POL_LOOKUP_URL % parlid))
            polname = root.cssselect('title')[0].text_content()
            polriding = root.cssselect('.constituency a')[0].text_content()
            polriding = polriding.replace(u'\xe2\x80\x94', '-') # replace unicode dash
                        
            try:
                riding = Riding.objects.get_by_name(polriding)
            except Riding.DoesNotExist:
                raise Politician.DoesNotExist("Couldn't find riding %s" % polriding)
            if session:
                pol = self.get_by_name(name=polname, session=session, riding=riding)
            else:
                pol = self.get_by_name(name=polname, riding=riding)
            #print "found %s." % pol
            pol.save_parl_id(parlid)
            polid = pol.id
            # if parlinfolink:
            #     match = re.search(r'Item=(.+?)&', parlinfolink['href'])
            #     pol.save_parlinfo_id(match.group(1))
            return self.get_query_set().get(pk=polid)
    getByParlID = get_by_parl_id

class Politician(Person):
    """Someone who has run for federal office."""
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    WORDCLOUD_PATH = 'autoimg/wordcloud-pol'

    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, choices=GENDER_CHOICES)
    headshot = models.ImageField(upload_to='polpics', blank=True, null=True)
    slug = models.CharField(max_length=30, blank=True, db_index=True)
    
    objects = PoliticianManager()

    def to_api_dict(self, representation):
        d = dict(
            name=self.name
        )
        if representation == 'detail':
            info = self.info_multivalued()
            members = list(self.electedmember_set.all().select_related(depth=1).order_by('-end_date'))
            d.update(
                given_name=self.name_given,
                family_name=self.name_family,
                gender=self.get_gender_display().lower(),
                image=self.headshot.url if self.headshot else None,
                other_info=info,
                links=[]
            )
            if 'email' in info:
                d['email'] = info.pop('email')[0]
            if self.parlpage:
                d['links'].append({
                    'url': self.parlpage,
                    'note': 'Page on parl.gc.ca'
                })
            if 'web_site' in info:
                d['links'].append({
                    'url': info.pop('web_site')[0],
                    'note': 'Official site'
                })
            if 'phone' in info:
                d['voice'] = info.pop('phone')[0]
            if 'fax' in info:
                d['fax'] = info.pop('fax')[0]
            d['memberships'] = [
                member.to_api_dict('detail', include_politician=False)
                for member in members
            ]
        return d

    def add_alternate_name(self, name):
        normname = parsetools.normalizeName(name)
        if normname not in self.alternate_names():
            self.set_info_multivalued('alternate_name', normname)

    def alternate_names(self):
        """Returns a list of ways of writing this politician's name."""
        return self.politicianinfo_set.filter(schema='alternate_name').values_list('value', flat=True)
        
    def add_slug(self):
        """Assigns a slug to this politician, unless there's a conflict."""
        if self.slug:
            return True
        slug = slugify(self.name)
        if Politician.objects.filter(slug=slug).exists():
            logger.warning("Slug %s already taken" % slug)
            return False
        self.slug = slug
        self.save()
        
    @property
    @memoize_property
    def current_member(self):
        """If this politician is a current MP, returns the corresponding ElectedMember object.
        Returns False if the politician is not a current MP."""
        try:
            return ElectedMember.objects.get(politician=self, end_date__isnull=True)
        except ElectedMember.DoesNotExist:
            return False

    @property
    @memoize_property        
    def latest_member(self):
        """If this politician has been an MP, returns the most recent ElectedMember object.
        Returns None if the politician has never been elected."""
        try:
            return ElectedMember.objects.filter(politician=self).order_by('-start_date').select_related('party', 'riding')[0]
        except IndexError:
            return None

    @property
    @memoize_property
    def latest_candidate(self):
        """Returns the most recent Candidacy object for this politician.
        Returns None if we're not aware of any candidacies for this politician."""
        try:
            return self.candidacy_set.order_by('-election__date').select_related('election')[0]
        except IndexError:
            return None
        
    def save(self, *args, **kwargs):
        super(Politician, self).save(*args, **kwargs)
        self.add_alternate_name(self.name)

    def save_parl_id(self, parlid):
        if PoliticianInfo.objects.filter(schema='parl_id', value=unicode(parlid)).exists():
            raise Exception("ParlID %d already in use" % parlid)
        self.set_info_multivalued('parl_id', parlid)
        
    def save_parlinfo_id(self, parlinfoid):
        self.set_info('parlinfo_id', parlinfoid.lower())
            
    @models.permalink
    def get_absolute_url(self):
        if self.slug:
            return 'parliament.politicians.views.politician', [], {'pol_slug': self.slug}
        return ('parliament.politicians.views.politician', [], {'pol_id': self.id})

    @property
    def identifier(self):
        return self.slug if self.slug else self.id
        
    # temporary, hackish, for stupid api framework
    @property
    def url(self):
        return "http://openparliament.ca" + self.get_absolute_url()

    @property
    def parlpage(self):
        try:
            return "http://www.parl.gc.ca/MembersOfParliament/ProfileMP.aspx?Key=%s&Language=E" % self.info()['parl_id']
        except KeyError:
            return None
        
    @models.permalink
    def get_contact_url(self):
        if self.slug:
            return ('parliament.contact.views.contact_politician', [], {'pol_slug': self.slug})
        return ('parliament.contact.views.contact_politician', [], {'pol_id': self.id})
            
    @memoize_property
    def info(self):
        """Returns a dictionary of PoliticianInfo attributes for this politician.
        e.g. politician.info()['web_site']
        """
        return dict([i for i in self.politicianinfo_set.all().values_list('schema', 'value')])
        
    @memoize_property
    def info_multivalued(self):
        """Returns a dictionary of PoliticianInfo attributes for this politician,
        where each key is a list of items. This allows more than one value for a
        given key."""
        info = {}
        for i in self.politicianinfo_set.all().values_list('schema', 'value'):
            info.setdefault(i[0], []).append(i[1])
        return info
        
    def set_info(self, key, value):
        try:
            info = self.politicianinfo_set.get(schema=key)
        except PoliticianInfo.DoesNotExist:
            info = PoliticianInfo(politician=self, schema=key)
        except PoliticianInfo.MultipleObjectsReturned:
            logger.error("Multiple objects found for schema %s on politician %r: %r" %
                (key, self,
                 self.politicianinfo_set.filter(schema=key).values_list('value', flat=True)
                    ))
            self.politicianinfo_set.filter(schema=key).delete()
            info = PoliticianInfo(politician=self, schema=key)
        info.value = unicode(value)
        info.save()
        
    def set_info_multivalued(self, key, value):
        PoliticianInfo.objects.get_or_create(politician=self, schema=key, value=unicode(value))

    def del_info(self, key):
        self.politicianinfo_set.filter(schema=key).delete()

    def get_text_analysis_qs(self, debates_only=False):
        """Return a QuerySet of Statements to be used in text corpus analysis."""
        statements = self.statement_set.filter(procedural=False)
        if debates_only:
            statements = statements.filter(document__document_type='D')
        if self.current_member:
            # For current members, we limit to the last two years for better
            # comparison.
            statements = statements.filter(time__gte=datetime.datetime.now() - datetime.timedelta(weeks=100))
        return statements
        
class PoliticianInfoManager(models.Manager):
    """Custom manager ensures we always pull in the politician FK."""
    
    def get_query_set(self):
        return super(PoliticianInfoManager, self).get_query_set()\
            .select_related('politician')

# Not necessarily a full list           
POLITICIAN_INFO_SCHEMAS = (
    'alternate_name',
    'twitter',
    'parl_id',
    'parlinfo_id',
    'freebase_id',
    'wikipedia_id'
)
            
class PoliticianInfo(models.Model):
    """Key-value store for attributes of a Politician."""
    politician = models.ForeignKey(Politician)
    schema = models.CharField(max_length=40, db_index=True)
    value = models.TextField()
    
    objects = models.Manager()
    sr_objects = PoliticianInfoManager()

    def __unicode__(self):
        return u"%s: %s" % (self.politician, self.schema)
        
    @property
    def int_value(self):
        return int(self.value)

class SessionManager(models.Manager):
    
    def with_bills(self):
        return self.get_query_set().filter(bill__number_only__gt=1).distinct()
    
    def current(self):
        return self.get_query_set().order_by('-start')[0]

    def get_by_date(self, date):
        return self.filter(models.Q(end__isnull=True) | models.Q(end__gte=date))\
            .get(start__lte=date)

    def get_from_string(self, string):
        """Given a string like '41st Parliament, 1st Session, returns the session."""
        match = re.search(r'^(\d\d)\D+(\d)\D', string)
        if not match:
            raise ValueError(u"Could not find parl/session in %s" % string)
        pk = match.group(1) + '-' + match.group(2)
        return self.get_query_set().get(pk=pk)

    def get_from_parl_url(self, url):
        """Given a parl.gc.ca URL with Parl= and Ses= query-string parameters,
        return the session."""
        parlnum = re.search(r'Parl=(\d\d)', url).group(1)
        sessnum = re.search(r'Ses=(\d)', url).group(1)
        pk = parlnum + '-' + sessnum
        return self.get_query_set().get(pk=pk)

class Session(models.Model):
    "A session of Parliament."
    
    id = models.CharField(max_length=4, primary_key=True)
    name = models.CharField(max_length=100)
    start = models.DateField()
    end = models.DateField(blank=True, null=True)
    parliamentnum = models.IntegerField(blank=True, null=True)
    sessnum = models.IntegerField(blank=True, null=True)

    objects = SessionManager()
    
    class Meta:
        ordering = ('-start',)

    def __unicode__(self):
        return self.name
        
    def has_votes(self):
        return bool(self.votequestion_set.all().count())
    
class RidingManager(models.Manager):
    
    # FIXME: This should really be in the database, not the model
    FIX_RIDING = {
        'richmond-arthabasca': 'richmond-arthabaska',
        'richemond-arthabaska': 'richmond-arthabaska',
        'battle-river': 'westlock-st-paul',
        'vancouver-est': 'vancouver-east',
        'calgary-ouest': 'calgary-west',
        'kitchener-wilmot-wellesley-woolwich': 'kitchener-conestoga',
        'carleton-orleans': 'ottawa-orleans',
        'frazer-valley-west': 'fraser-valley-west',
        'laval-ouest': 'laval-west',
        'medecine-hat': 'medicine-hat',
        'lac-st-jean': 'lac-saint-jean',
        'vancouver-north': 'north-vancouver',
        'laval-est': 'laval-east',
        'ottawa-ouest-nepean': 'ottawa-west-nepean',
        'cap-breton-highlands-canso': 'cape-breton-highlands-canso',
        'winnipeg-centre-sud': 'winnipeg-south-centre',
        'renfrew-nippissing-pembroke': 'renfrew-nipissing-pembroke',
        'the-battleford-meadow-lake': 'the-battlefords-meadow-lake',
        'esquimalt-de-fuca': 'esquimalt-juan-de-fuca',
        'sint-hubert': 'saint-hubert',
        #'edmonton-mill-woods-beaumont': 'edmonton-beaumont',
    }
    
    def get_by_name(self, name):
        slug = parsetools.slugify(name)
        if slug in RidingManager.FIX_RIDING:
            slug = RidingManager.FIX_RIDING[slug]
        return self.get_query_set().get(slug=slug)

PROVINCE_CHOICES = (
    ('AB', 'Alberta'),
    ('BC', 'B.C.'),
    ('SK', 'Saskatchewan'),
    ('MB', 'Manitoba'),
    ('ON', 'Ontario'),
    ('QC', 'Québec'),
    ('NB', 'New Brunswick'),
    ('NS', 'Nova Scotia'),
    ('PE', 'P.E.I.'),
    ('NL', 'Newfoundland & Labrador'),
    ('YT', 'Yukon'),
    ('NT', 'Northwest Territories'),
    ('NU', 'Nunavut'),
)
PROVINCE_LOOKUP = dict(PROVINCE_CHOICES)

class Riding(models.Model):
    "A federal riding."
    
    name = models.CharField(max_length=60)
    province = models.CharField(max_length=2, choices=PROVINCE_CHOICES)
    slug = models.CharField(max_length=60, unique=True, db_index=True)
    edid = models.IntegerField(blank=True, null=True, db_index=True)
    
    objects = RidingManager()
    
    class Meta:
        ordering = ('province', 'name')
        
    def save(self):
        if not self.slug:
            self.slug = parsetools.slugify(self.name)
        super(Riding, self).save()
        
    @property
    def dashed_name(self):
        return self.name.replace('--', u'—')
        
    def __unicode__(self):
        return "%s (%s)" % (self.dashed_name, self.get_province_display())
        
class ElectedMemberManager(models.Manager):
    
    def current(self):
        return self.get_query_set().filter(end_date__isnull=True)
        
    def former(self):
        return self.get_query_set().filter(end_date__isnull=False)
    
    def on_date(self, date):
        return self.get_query_set().filter(models.Q(start_date__lte=date)
            & (models.Q(end_date__isnull=True) | models.Q(end_date__gte=date)))
    
    def get_by_pol(self, politician, date=None, session=None):
        if not date and not session:
            raise Exception("Provide either a date or a session to get_by_pol.")
        if date:
            return self.on_date(date).get(politician=politician)
        else:
            # In the case of floor crossers, there may be more than one ElectedMember
            # We haven't been given a date, so just return the first EM
            qs = self.get_query_set().filter(politician=politician, sessions=session).order_by('-start_date')
            if not len(qs):
                raise ElectedMember.DoesNotExist("No elected member for %s, session %s" % (politician, session))
            return qs[0]
    
class ElectedMember(models.Model):
    """Represents one person, elected to a given riding for a given party."""
    sessions = models.ManyToManyField(Session)
    politician = models.ForeignKey(Politician)
    riding = models.ForeignKey(Riding)
    party = models.ForeignKey(Party)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    
    objects = ElectedMemberManager()
    
    def __unicode__ (self):
        if self.end_date:
            return u"%s (%s) was the member from %s from %s to %s" % (self.politician, self.party, self.riding, self.start_date, self.end_date)
        else:
            return u"%s (%s) is the member from %s (since %s)" % (self.politician, self.party, self.riding, self.start_date)

    def to_api_dict(self, representation, include_politician=True):
        d = dict(
            url=self.get_absolute_url(),
            start_date=unicode(self.start_date),
            end_date=unicode(self.end_date) if self.end_date else None,
            party={
                'name': {'en':self.party.name},
                'short_name': {'en':self.party.short_name}
            },
            label={'en': u"%s MP for %s" % (self.party.short_name, self.riding.dashed_name)},
            riding={
                'name': {'en': self.riding.dashed_name},
                'province': self.riding.province,
                'id': self.riding.edid,
            }
        )
        if include_politician:
            d['politician_url'] = self.politician.get_absolute_url()
        return d

    def get_absolute_url(self):
        return urlresolvers.reverse('politician_membership', kwargs={'member_id': self.id})
            
    @property
    def current(self):
        return not bool(self.end_date)
        
class SiteNews(models.Model):
    """Entries for the semi-blog on the openparliament homepage."""
    date = models.DateTimeField(default=datetime.datetime.now)
    title = models.CharField(max_length=200)
    text = models.TextField()
    active = models.BooleanField(default=True)
    
    objects = models.Manager()
    public = ActiveManager()
    
    class Meta:
        ordering = ('-date',)


########NEW FILE########
__FILENAME__ = parsetools
import re, unicodedata, decimal
import datetime

from BeautifulSoup import NavigableString

r_politicalpost = re.compile(r'(Minister|Leader|Secretary|Solicitor|Attorney|Speaker|Deputy |Soliciter|Chair |Parliamentary|President |for )')
r_honorific = re.compile(r'^(Mr\.?|Mrs\.?|Ms\.?|Miss\.?|Hon\.?|Right Hon\.|The|A|An\.?|Some|M\.|One|Santa|Acting|L\'hon\.|Assistant|Mme)\s(.+)$', re.DOTALL | re.UNICODE)
r_notamember = re.compile(r'^(The|A|Some|Acting|Santa|One|Assistant|An\.?|Le|La|Une|Des|Voices)')
r_mister = re.compile(r'^(Mr|Mrs|Ms|Miss|Hon|Right Hon|M|Mme)\.?\s+')
r_parens = re.compile(r'\s*\(.+\)\s*$')

def countWords(text):
    # very quick-n-dirty for now
    return text.count(' ') + int(text.count("\n") / 2) + 1

def time(hour, minute):
    if hour >= 24:
        hour = hour % 24 # no, really. the house of commons is so badass they meet at 25 o'clock
    return datetime.time(hour=hour, minute=minute)

def time_to_datetime(hour, minute, date):
    """Given hour, minute, and a datetime.date, returns a datetime.datetime.

    Necessary to deal with the occasional wacky 25 o'clock timestamps in Hansard.
    """
    if hour < 24:
        return datetime.datetime.combine(date, datetime.time(hour=hour, minute=minute))
    else:
        return datetime.datetime.combine(
            date + datetime.timedelta(days=hour//24),
            datetime.time(hour=hour % 24, minute=minute)
        )

def normalizeHansardURL(u):
    docid = re.search(r'DocId=(\d+)', u).group(1)
    parl = re.search(r'Parl=(\d+)', u).group(1)
    ses = re.search(r'Ses=(\d+)', u).group(1)
    return 'http://www2.parl.gc.ca/HousePublications/Publication.aspx?Language=E&Mode=1&Parl=%s&Ses=%s&DocId=%s' % (parl, ses, docid)

def removeAccents(str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])
    
def stripHonorific(s):
    return re.sub(r'^[A-Z][a-z]+\. ', '', s)
    
def isString(o):
    #return not hasattr(o, 'contents')
    return isinstance(o, NavigableString)
    
def titleIfNecessary(s):
    if not re.search(r'[a-z]', s):
        s = s.title()
    return s
    
r_hasText = re.compile(r'\S', re.UNICODE)
def getText(tag):
    return u''.join(tag.findAll(text=r_hasText))

r_extraWhitespace = re.compile(r'\s\s*', re.UNICODE)    
def tameWhitespace(s):
    return re.sub(r_extraWhitespace, u' ', s.replace(u"\n", u' '))
    
def sane_quotes(s):
    return s.replace('``', '"').replace("''", '"')
    
def slugify(s, allow_numbers=False):
    if allow_numbers:
        pattern = r'[^a-zA-Z0-9]'
    else:
        pattern = r'[^a-zA-Z]'
    s = re.sub(pattern, '-', removeAccents(s.strip().lower()))
    return re.sub(r'--+', '-', s)

def normalizeName(s):
    return tameWhitespace(removeAccents(stripHonorific(s).lower())).strip()

def munge_date(date):
    if date.count('0000') > 0:
        return None
    elif date == '':
        return None
    elif date == u'&nbsp;':
        return None
    else:
        return date

def munge_decimal(num):
    try:
        return decimal.Decimal(num.replace(',', ''))
    except (ValueError, decimal.InvalidOperation):
        return decimal.Decimal(0)

def munge_int(num):
    num = re.sub(r'\D', '', num)
    if num == '':
        return None
    else:
        return int(num)

def munge_time(time):
    match = re.search(r'(\d\d:\d\d:\d\d)', time)
    if match:
        return match.group(1)
    else:
        return None

def munge_postcode (code):
    if code:
        code = code.upper()
        if len(code) == 6: # Add a space if there isn't one
            code = code[:3] + ' ' + code[3:]
        if re.search(r'^[ABCEGHJKLMNPRSTVXYZ]\d[A-Z] \d[A-Z]\d$', code):
            return code
    return None
    
def none_to_empty(s):
    return s if s is not None else ''
    
def etree_extract_text(elem):
    text = ''
    for x in elem.getiterator():
        if text and x.tag in ('Para', 'P', 'p'):
            text += "\n\n"
        text += (none_to_empty(x.text) + none_to_empty(x.tail)).replace("\n", ' ')
    return text
########NEW FILE########
__FILENAME__ = search_indexes
from haystack import site
from haystack import indexes

from parliament.core.models import Politician
from parliament.search.index import SearchIndex

class PolIndex(SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    boosted = indexes.CharField(use_template=True, stored=False)
    politician = indexes.CharField(model_attr='name', indexed=False)
    party = indexes.CharField(model_attr='latest_member__party__short_name')
    province = indexes.CharField(model_attr='latest_member__riding__province')
    url = indexes.CharField(model_attr='get_absolute_url', indexed=False)
    doctype = indexes.CharField(default='mp')
    
    def get_queryset(self):
        return Politician.objects.elected()

site.register(Politician, PolIndex)

########NEW FILE########
__FILENAME__ = sitemap
from django.contrib.sitemaps import Sitemap
from parliament.core.models import Politician
from parliament.hansards.models import Document
from parliament.bills.models import Bill, VoteQuestion

class PoliticianSitemap(Sitemap):

    def items(self):
        return Politician.objects.elected()

class HansardSitemap(Sitemap):
    
    def items(self):
        return Document.objects.all()
        
    def lastmod(self, obj):
        return obj.date
        
class BillSitemap(Sitemap):
    
    def items(self):
        return Bill.objects.all()
        
class VoteQuestionSitemap(Sitemap):
    def items(self):
        return VoteQuestion.objects.all()
        
    def lastmod(self, obj):
        return obj.date
        
sitemaps = {
    'politician': PoliticianSitemap,
    'hansard': HansardSitemap,
    'bill': BillSitemap,
    'votequestion': VoteQuestionSitemap,
}
########NEW FILE########
__FILENAME__ = json
from __future__ import absolute_import
from json import dumps

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='json')
def jsonfilter(obj):
    return mark_safe(
        dumps(obj)
    )

########NEW FILE########
__FILENAME__ = markup
from django import template
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(is_safe=True)
def markdown(value, arg=''):
    """
    Runs Markdown over a given value, optionally using various
    extensions python-markdown supports.

    Syntax::

        {{ value|markdown:"extension1_name,extension2_name..." }}

    To enable safe mode, which strips raw HTML and only returns HTML
    generated by actual Markdown syntax, pass "safe" as the first
    extension in the list.

    If the version of Markdown in use does not support extensions,
    they will be silently ignored.

    """

    try:
        import markdown
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError("Error in 'markdown' filter: The Python markdown library isn't installed.")
        return force_text(value)
    else:
        markdown_vers = getattr(markdown, "version_info", 0)
        if markdown_vers < (2, 1):
            if settings.DEBUG:
                raise template.TemplateSyntaxError(
                    "Error in 'markdown' filter: Django does not support versions of the Python markdown library < 2.1.")
            return force_text(value)
        else:
            extensions = [e for e in arg.split(",") if e]
            if extensions and extensions[0] == "safe":
                extensions = extensions[1:]
                return mark_safe(markdown.markdown(
                    force_text(value), extensions, safe_mode=True, enable_attributes=False))
            else:
                return mark_safe(markdown.markdown(
                    force_text(value), extensions, safe_mode=False))

########NEW FILE########
__FILENAME__ = ours
import datetime, re, types

from django import template

from parliament.core.models import PROVINCE_LOOKUP

register = template.Library()

@register.filter(name='expand_province')
def expand_province(value):
    return PROVINCE_LOOKUP.get(value, None)
    
@register.filter(name='heshe')
def heshe(pol):
    if pol.gender == 'F':
        return 'She'
    elif pol.gender =='M':
        return 'He'
    else:
        return 'He/she'
        
@register.filter(name='hisher')
def heshe(pol):
    if pol.gender == 'F':
        return 'Her'
    elif pol.gender == 'M':
        return 'His'
    else:
        return 'Their'
        
@register.filter(name='himher')
def himher(pol):
    if pol.gender == 'F':
        return 'Her'
    elif pol.gender == 'M':
        return 'Him'
    else:
        return 'Them'
        
@register.filter(name='mrms')
def mrms(pol):
    if pol.gender == 'M':
        return 'Mr.'
    elif pol.gender == 'F':
        return 'Ms.'
    else:
        return 'Mr./Ms.'
        
@register.filter(name='month_num')
def month_num(month):
    return datetime.date(2010, month, 1).strftime("%B")
    
@register.filter(name='strip_act')
def strip_act(value):
    value = re.sub(r'An Act (to )?([a-z])', lambda m: m.group(2).upper(), value)
    return re.sub(r' Act$', '', value)
    
@register.filter(name='time_since')
def time_since(value):
    today = datetime.date.today()
    days_since = (today - value).days
    if value > today or days_since == 0:
        return 'Today'
    elif days_since == 1:
        return 'Yesterday'
    elif days_since == 2:
        return 'Two days ago'
    elif days_since == 3:
        return 'Three days ago'
    elif days_since < 7:
        return 'This week'
    elif days_since < 14:
        return 'A week ago'
    elif days_since < 21:
        return 'Two weeks ago'
    elif days_since < 28:
        return 'Three weeks ago'
    elif days_since < 45:
        return 'A month ago'
    elif days_since < 75:
        return 'Two months ago'
    elif days_since < 105:
        return 'Three months ago'
    else:
        return 'More than three months ago'
        
@register.filter(name='english_list')
def english_list(value, arg=', '):
    if not type(value) == types.ListType:
        raise Exception("Tag english_list takes a list as argument")
    if len(value) == 1:
        return "%s" % value[0]
    elif len(value) == 0:
        return ''
    elif len(value) == 2:
        return "%s and %s" % (value[0], value[1])
    else:
        return "%s%s and %s" % (arg.join(value[0:-1]), arg, value[-1])
        
@register.filter(name='list_prefix')
def list_prefix(value, arg):
    return ["%s%s" % (arg, i) for i in value]
    
@register.filter(name='list_filter')
def list_filter(value, arg):
    return filter(lambda x: x != arg, value)
########NEW FILE########
__FILENAME__ = pagination
from django import template

register = template.Library()

# http://djangosnippets.org/snippets/2763/
LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 8
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 6
NUM_PAGES_OUTSIDE_RANGE = 2
ADJACENT_PAGES = 2

@register.assignment_tag(takes_context=True)
def long_paginator(context):
    '''
    To be used in conjunction with the object_list generic view.

    Adds pagination context variables for use in displaying leading, adjacent and
    trailing page links in addition to those created by the object_list generic
    view.
    '''

    page_obj = context['page']
    try:
        paginator = page_obj.paginator
    except AttributeError:
        return ''
    pages = paginator.num_pages
    if pages <= 1:
        return ''
    page = page_obj.number
    in_leading_range = in_trailing_range = False
    pages_outside_leading_range = pages_outside_trailing_range = range(0)
    if pages <= LEADING_PAGE_RANGE_DISPLAYED + NUM_PAGES_OUTSIDE_RANGE + 1:
        in_leading_range = in_trailing_range = True
        page_range = [n for n in range(1, pages + 1)]
    elif page <= LEADING_PAGE_RANGE:
        in_leading_range = True
        page_range = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1)]
        pages_outside_leading_range = [n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
    elif page > pages - TRAILING_PAGE_RANGE:
        in_trailing_range = True
        page_range = [n for n in range(pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, pages + 1) if n > 0 and n <= pages]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    else: 
        page_range = [n for n in range(page - ADJACENT_PAGES, page + ADJACENT_PAGES + 1) if n > 0 and n <= pages]
        pages_outside_leading_range = [n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]

    # Now try to retain GET params, except for 'page'
    # Add 'django.core.context_processors.request' to settings.TEMPLATE_CONTEXT_PROCESSORS beforehand
    request = context['request']
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    if 'partial' in params:
        del params['partial']
    get_params = params.urlencode()

    pagination_ctx = {
        'pages': pages,
        'page': page,
        'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next': page_obj.next_page_number() if page_obj.has_next() else None,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'page_range': page_range,
        'in_leading_range': in_leading_range,
        'in_trailing_range': in_trailing_range,
        'pages_outside_leading_range': pages_outside_leading_range,
        'pages_outside_trailing_range': pages_outside_trailing_range,
        'get_params': get_params,
        'allow_single_page': context.get('allow_single_page')
    }

    return template.loader.get_template("long_paginator.html").render(template.Context(pagination_ctx))


########NEW FILE########
__FILENAME__ = test_utils
from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

class TestSuiteRunner(DjangoTestSuiteRunner):
    """By default, runs tests only for our code, not third-party apps."""
        
    def run_tests(self, test_labels, **kwargs):
        if not test_labels:
            test_labels = [app.split('.')[-1] 
                for app in settings.INSTALLED_APPS
                if app.startswith(settings.TEST_APP_PREFIX)]
        print "Running tests for: %s" % ', '.join(test_labels)        
        super(TestSuiteRunner, self).run_tests(test_labels, **kwargs)
########NEW FILE########
__FILENAME__ = thumbnail

def crop_first(image, requested_size, opts):
    if 'crop_first' in opts:
        (t, r, b, l) = (int(x) for x in opts['crop_first'].split(','))
        (w, h) = image.size
        image = image.crop((l, t, w-r, h-b))
    return image
crop_first.valid_options = ['crop_first']
########NEW FILE########
__FILENAME__ = utils
import urllib, urllib2
import re
import httplib2
import json
from functools import wraps

from django.db import models
from django.conf import settings
from django.core import urlresolvers
from django.core.mail import mail_admins
from django.http import HttpResponsePermanentRedirect

import logging
logger = logging.getLogger(__name__)


def postcode_to_edid(postcode):
    # First try Elections Canada
    postcode = postcode.replace(' ', '')
    try:
        #return postcode_to_edid_ec(postcode)
        return postcode_to_edid_webserv(postcode)
    except:
        return postcode_to_edid_represent(postcode)


def postcode_to_edid_represent(postcode):
    url = 'http://represent.opennorth.ca/postcodes/%s/' % postcode
    try:
        content = json.load(urllib2.urlopen(url))
    except urllib2.HTTPError as e:
        if e.code != 404:
            logger.exception("Represent error for %s" % url)
        return None
    edid = [
        b['external_id'] for b in
        content.get('boundaries_concordance', []) + content.get('boundaries_centroid', [])
        if b['boundary_set_name'] == 'Federal electoral district'
    ]
    return int(edid[0]) if edid else None


EC_POSTCODE_URL = 'http://elections.ca/scripts/pss/FindED.aspx?L=e&PC=%s'
r_ec_edid = re.compile(r'&ED=(\d{5})&')
def postcode_to_edid_ec(postcode):
    h = httplib2.Http(timeout=1)
    h.follow_redirects = False
    (response, content) = h.request(EC_POSTCODE_URL % postcode.replace(' ', ''))
    match = r_ec_edid.search(response['location'])
    return int(match.group(1))
    
def postcode_to_edid_webserv(postcode):
    try:
        response = urllib2.urlopen('http://postal-code-to-edid-webservice.heroku.com/postal_codes/' + postcode)
    except urllib2.HTTPError as e:
        if e.code == 404:
            return None
        raise e
    codelist = json.load(response)
    if not isinstance(codelist, list):
        mail_admins("Invalid response from postcode service", repr(codelist))
        raise Exception()
    if len(codelist) > 1:
        mail_admins("Multiple results for postcode", postcode + repr(codelist))
        return None
    return int(codelist[0])
    
def memoize_property(target):
    """Caches the result of a method that takes no arguments."""
    
    cacheattr = '_cache_' + target.__name__
    
    @wraps(target)
    def wrapped(self):
        if not hasattr(self, cacheattr):
            setattr(self, cacheattr, target(self))
        return getattr(self, cacheattr)
    return wrapped

def language_property(fieldname):
    if settings.LANGUAGE_CODE.startswith('fr'):
        fieldname = fieldname + '_fr'
    else:
        fieldname = fieldname + '_en'

    return property(lambda self: getattr(self, fieldname))
    
def redir_view(view):
    """Function factory to redirect requests to the given view."""
    
    def wrapped(request, *args, **kwargs):
        return HttpResponsePermanentRedirect(
            urlresolvers.reverse(view, args=args, kwargs=kwargs)
        )
    return wrapped
    
def get_twitter_share_url(url, description, add_plug=True):
    """Returns a URL for a Twitter post page, prepopulated with a sharing message.
    
    url -- URL to the shared page -- should start with / and not include the domain
    description -- suggested content for sharing message
    add_plug -- if True, will add a mention of openparliament.ca, if there's room """
    
    PLUG = ' (from openparliament.ca)'
    
    longurl = settings.SITE_URL + url
    
    try:
        shorten_resp_raw = urllib2.urlopen(settings.BITLY_API_URL + urllib.urlencode({'longurl': longurl}))
        shorten_resp = json.load(shorten_resp_raw)
        shorturl = shorten_resp['data']['url']
    except Exception, e:
        # FIXME logging
        shorturl = longurl
    
    if (len(description) + len(shorturl)) > 139:
        description = description[:136-len(shorturl)] + '...'
    elif add_plug and (len(description) + len(shorturl) + len(PLUG)) < 140:
        description += PLUG
    message = "%s %s" % (description, shorturl)
    return 'http://twitter.com/home?' + urllib.urlencode({'status': message})
    
#http://stackoverflow.com/questions/561486/how-to-convert-an-integer-to-the-shortest-url-safe-string-in-python
import string
ALPHABET = string.ascii_uppercase + string.ascii_lowercase + \
           string.digits + '-_'
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
SIGN_CHARACTER = '$'
def int64_encode(n):
    """Given integer n, returns a base64-ish string representation."""
    if n < 0:
        return SIGN_CHARACTER + int64_encode(-n)
    s = []
    while True:
        n, r = divmod(n, BASE)
        s.append(ALPHABET[r])
        if n == 0: break
    return ''.join(reversed(s))


def int64_decode(s):
    """Turns the output of int64_encode back into an integer"""
    if s[0] == SIGN_CHARACTER:
        return -int64_decode(s[1:])
    n = 0
    for c in s:
        n = n * BASE + ALPHABET_REVERSE[c]
    return n
        
class ActiveManager(models.Manager):

    def get_query_set(self):
        return super(ActiveManager, self).get_query_set().filter(active=True)

def feed_wrapper(feed_class):
    """Decorator that ensures django.contrib.syndication.Feed objects are created for
    each request, not reused over several requests. This means feed classes can safely
    store request-specific attributes on self."""
    def call_feed(request, *args, **kwargs):
        feed_instance = feed_class()
        feed_instance.request = request
        return feed_instance(request, *args, **kwargs)
    return call_feed
########NEW FILE########
__FILENAME__ = views
import datetime

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template import Context, loader, RequestContext
from django.utils.html import conditional_escape
from django.views.decorators.cache import never_cache

from parliament.core.models import Session, SiteNews
from parliament.bills.models import VoteQuestion
from parliament.hansards.models import Document
from parliament.core.models import Session, SiteNews
from parliament.core.templatetags.markup import markdown
from parliament.text_analysis.models import TextAnalysis

def home(request):
    
    t = loader.get_template("home.html")
    latest_hansard = Document.debates.filter(date__isnull=False, public=True)[0]
    c = RequestContext(request, {
        'latest_hansard': latest_hansard,
        'sitenews': SiteNews.objects.filter(active=True,
            date__gte=datetime.datetime.now() - datetime.timedelta(days=90))[:6],
        'votes': VoteQuestion.objects.filter(session=Session.objects.current())\
            .select_related('bill')[:6],
        'wordcloud_js': TextAnalysis.objects.get_wordcloud_js(
            key=latest_hansard.get_text_analysis_url())
    })
    return HttpResponse(t.render(c))
    
@never_cache
def closed(request, message=None):
    if not message:
        message = "We're currently down for planned maintenance. We'll be back soon."
    resp = flatpage_response(request, 'closedparliament.ca', message)
    resp.status_code = 503
    return resp

@never_cache
def db_readonly(request, *args, **kwargs):
    title = "Temporarily unavailable"
    message = """We're currently running on our backup database, and this particular functionality is down.
        It should be back up soon. Sorry for the inconvenience!"""
    resp = flatpage_response(request, title, message)
    resp.status_code = 503
    return resp

def disable_on_readonly_db(view):
    if settings.PARLIAMENT_DB_READONLY:
        return db_readonly
    return view
    
def flatpage_response(request, title, message):
    t = loader.get_template("flatpages/default.html")
    c = RequestContext(request, {
        'flatpage': {
            'title': title,
            'content': """<div class="focus"><p>%s</p></div>""" % conditional_escape(message)},
    })
    return HttpResponse(t.render(c))
    
class SiteNewsFeed(Feed):
    
    title = "openparliament.ca: Site news"
    link = "http://openparliament.ca/"
    description = "Announcements about the openparliament.ca site"
    
    def items(self):
        return SiteNews.public.all()[:6]
        
    def item_title(self, item):
        return item.title
        
    def item_description(self, item):
        return markdown(item.text)
        
    def item_link(self):
        return 'http://openparliament.ca/'
        
    def item_guid(self, item):
        return unicode(item.id)
    
########NEW FILE########
__FILENAME__ = widgets
from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings

from recaptcha.client import captcha

class ReCaptchaWidget(forms.widgets.Widget):
    recaptcha_challenge_name = 'recaptcha_challenge_field'
    recaptcha_response_name = 'recaptcha_response_field'

    def render(self, name, value, attrs=None):
        return mark_safe(u'<div class="recaptcha">%s</div>' % captcha.displayhtml(settings.RECAPTCHA_PUBLIC_KEY))

    def value_from_datadict(self, data, files, name):
        return [data.get(self.recaptcha_challenge_name, None), 
            data.get(self.recaptcha_response_name, None)]
########NEW FILE########
__FILENAME__ = default_settings
import os

DEBUG = True

ADMINS = [
    ('Michael Mulley', 'michael@michaelmulley.com'),
]

MANAGERS = ADMINS

PROJ_ROOT = os.path.dirname(os.path.realpath(__file__))

HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SITECONF = 'parliament.search_sites'

CACHE_MIDDLEWARE_KEY_PREFIX = 'parl'
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

# Set to True to disable functionality where user-provided data is saved
PARLIAMENT_DB_READONLY = False

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/Montreal'

# Language code for this installation.
# MUST BE either 'en' or 'fr'
LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.realpath(os.path.join(PROJ_ROOT, '..', '..', 'mediafiles'))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

STATICFILES_DIRS = [os.path.join(PROJ_ROOT, 'static')]
STATIC_ROOT = os.path.realpath(os.path.join(PROJ_ROOT, '..', '..', 'staticfiles'))
STATIC_URL = '/static/'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter'
]
COMPRESS_JS_FILTERS = []
COMPRESS_OFFLINE = True

PARLIAMENT_LANGUAGE_MODEL_PATH = os.path.realpath(os.path.join(PROJ_ROOT, '..', '..', 'language_models'))
PARLIAMENT_DISABLE_WORDCLOUD = True

APPEND_SLASH = False

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60*60*24*60  # 60 days

PARLIAMENT_API_HOST = 'api.openparliament.ca'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'parliament.accounts.middleware.AuthenticatedEmailMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'parliament.core.api.FetchFromCacheMiddleware',
]

ROOT_URLCONF = 'parliament.urls'

WSGI_APPLICATION = 'parliament.wsgi.application'

TEMPLATE_DIRS = [
    os.path.join(PROJ_ROOT, 'templates'),
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.flatpages',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django_extensions',
    'haystack',
    'south',
    'sorl.thumbnail',
    'compressor',
    'parliament.core',
    'parliament.accounts',
    'parliament.hansards',
    'parliament.elections',
    'parliament.bills',
    'parliament.politicians',
    'parliament.activity',
    'parliament.alerts',
    'parliament.committees',
    'parliament.search',
    'parliament.text_analysis',
]

THUMBNAIL_SUBDIR = '_thumbs'
THUMBNAIL_PROCESSORS = (
    'sorl.thumbnail.processors.colorspace',
    'sorl.thumbnail.processors.autocrop',
    'parliament.core.thumbnail.crop_first',
    'sorl.thumbnail.processors.scale_and_crop',
    'sorl.thumbnail.processors.filters',
)

SOUTH_TESTS_MIGRATE = False
TEST_RUNNER = 'parliament.core.test_utils.TestSuiteRunner'
TEST_APP_PREFIX = 'parliament'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(module)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers':['null'],
            'propagate': True,
            'level':'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'parliament': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    },
}



########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.elections.models import *

admin.site.register(Election)
admin.site.register(Candidacy)
########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Election'
        db.create_table('elections_election', (
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('byelection', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('elections', ['Election'])

        # Adding model 'Candidacy'
        db.create_table('elections_candidacy', (
            ('candidate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'])),
            ('elected', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('election', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['elections.Election'])),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Party'])),
            ('riding', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Riding'])),
            ('votetotal', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('occupation', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('elections', ['Candidacy'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Election'
        db.delete_table('elections_election')

        # Deleting model 'Candidacy'
        db.delete_table('elections_candidacy')
    
    
    models = {
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'elections.candidacy': {
            'Meta': {'object_name': 'Candidacy'},
            'candidate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'elected': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'election': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['elections.Election']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'occupation': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'votetotal': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'elections.election': {
            'Meta': {'object_name': 'Election'},
            'byelection': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    complete_apps = ['elections']

########NEW FILE########
__FILENAME__ = 0002_votepercent
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Candidacy.votepercent'
        db.add_column('elections_candidacy', 'votepercent', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting field 'Candidacy.votepercent'
        db.delete_column('elections_candidacy', 'votepercent')
    
    
    models = {
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'elections.candidacy': {
            'Meta': {'object_name': 'Candidacy'},
            'candidate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'elected': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'election': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['elections.Election']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'occupation': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'votepercent': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'votetotal': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'elections.election': {
            'Meta': {'object_name': 'Election'},
            'byelection': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    complete_apps = ['elections']

########NEW FILE########
__FILENAME__ = models
from decimal import Decimal
from collections import defaultdict

from django.db import models

from parliament.core.models import Politician, Riding, Party, ElectedMember

import logging
logger = logging.getLogger(__name__)

class Election (models.Model):
    date = models.DateField(db_index=True)
    byelection = models.BooleanField()
    
    class Meta:
        ordering = ('-date',)
    
    def __unicode__ (self):
        if self.byelection:
            return u"Byelection of %s" % self.date
        else:
            return u"General election of %s" % self.date
    
    def calculate_vote_percentages(self):
        candidacies = self.candidacy_set.all()
        riding_candidacies = defaultdict(list)
        riding_votetotals = defaultdict(Decimal)
        for candidacy in candidacies:
            riding_candidacies[candidacy.riding_id].append(candidacy)
            riding_votetotals[candidacy.riding_id] += candidacy.votetotal
        for riding in riding_candidacies:
            for candidacy in riding_candidacies[riding]:
                candidacy.votepercent = (Decimal(candidacy.votetotal) / riding_votetotals[riding]) * 100
                candidacy.save()
                
    def label_winners(self):
        """Sets the elected boolean on this election's Candidacies"""
        candidacies = self.candidacy_set.all()
        candidacies.update(elected=None)
        riding_candidacies = defaultdict(list)
        for candidacy in candidacies:
            riding_candidacies[candidacy.riding_id].append(candidacy)
        for riding_candidacies in riding_candidacies.values():
            winner = max(riding_candidacies, key=lambda c: c.votetotal)
            winner.elected = True
            winner.save()
        candidacies.filter(elected=None).update(elected=False)
        
    def create_members(self, session=None):
        for candidacy in self.candidacy_set.filter(elected=True):
            candidacy.create_member(session)
                
class CandidacyManager(models.Manager):
    
    def create_from_name(self, first_name, last_name, riding, party, election,
        votetotal, elected, votepercent=None, occupation='', interactive=True):
        """Create a Candidacy based on a candidate's name; checks for prior
        Politicians representing the same person.
        
        first_name and last_name are strings; remaining arguments are as in
        the Candidacy model"""
        
        candidate = None
        fullname = u' '.join((first_name, last_name))
        candidates = Politician.objects.filter_by_name(fullname)
        # If there's nothing in the list, try a little harder
        if not candidates:
            # Does the candidate have many given names?
            if first_name.strip().count(' ') >= 1:
                minifirst = first_name.strip().split(' ')[0]
                candidates = Politician.objects.filter_by_name("%s %s" % (minifirst, last_name))
        # Then, evaluate the possibilities in the list
        for posscand in candidates:
            # You're only a match if you've run for office for the same party in the same province
            match = ElectedMember.objects.filter(riding__province=riding.province, party=party, politician=posscand).count() >= 1 or Candidacy.objects.filter(riding__province=riding.province, party=party, candidate=posscand).count() >= 1
            if match:
                if candidate is not None:
                    if interactive:
                        print "Please enter Politician ID for %r (%r)" % (fullname, riding.name)
                        candidate = Politician.objects.get(pk=raw_input().strip())
                        break
                    else:
                        raise Politician.MultipleObjectsReturned(
                            "Could not disambiguate among existing candidates for %s" % fullname)
                candidate = posscand
                    
        if candidate is None:
            candidate = Politician(name=fullname, name_given=first_name, name_family=last_name)
            candidate.save()
            
        return self.create(
            candidate=candidate,
            riding=riding,
            party=party,
            election=election,
            votetotal=votetotal,
            elected=elected,
            votepercent=votepercent,
            occupation=occupation
        )
        

class Candidacy (models.Model):
    candidate = models.ForeignKey(Politician)
    riding = models.ForeignKey(Riding)
    party = models.ForeignKey(Party)
    election = models.ForeignKey(Election)
    occupation = models.CharField(max_length=100, blank=True)
    votetotal = models.IntegerField(blank=True, null=True)
    votepercent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    elected = models.NullBooleanField(blank=True, null=True)
    
    objects = CandidacyManager()
    
    class Meta:
        verbose_name_plural = 'Candidacies'
        
    def create_member(self, session=None):
        """Creates an ElectedMember for a winning candidate"""
        if not self.elected:
            return False
        try:
            member = ElectedMember.objects\
                .filter(models.Q(end_date__isnull=True) | models.Q(end_date=self.election.date))\
                .get(politician=self.candidate,
                riding=self.riding,
                party=self.party)
            member.end_date = None
            member.save()
        except ElectedMember.DoesNotExist:
            member = ElectedMember.objects.create(
                politician=self.candidate,
                riding=self.riding,
                party=self.party,
                start_date=self.election.date
            )
        if session:
            member.sessions.add(session)
        if not self.politician.slug:
            self.politician.add_slug()
        return member
    
    def __unicode__ (self):
        return u"%s (%s) was a candidate in %s in the %s" % (self.candidate, self.party, self.riding, self.election)

########NEW FILE########
__FILENAME__ = views
# Create your views here.

########NEW FILE########
__FILENAME__ = models
"""This is a half-finished module to track Elections Canada
contribution data.

It and the scraper in parliament.imports.ec were written in summer 2009
and haven't been touched since. Not that they're not worthwhile--they're
just looking for a home, and parents.
"""

from django.db import models

from parliament.elections.models import Candidacy
from parliament.core.models import Person

class Contributor (Person):
    city = models.CharField(max_length=50, blank=True)
    province = models.CharField(max_length=2, blank=True)
    postcode = models.CharField(max_length=7, blank=True)
    
    def __unicode__ (self):
        if self.city and self.province:
            return u"%s (%s, %s)" % (self.name, self.city, self.province)
        else:
            return self.name
    
    def save(self):
        if self.city is None:
            self.city = ''
        if self.province is None:
            self.province = ''
        if len(self.province) > 2:
            self.province = self.province[:2]
        if self.postcode is None:
            self.postcode = ''
        super(Contributor, self).save()
    
class Contribution (models.Model):
    contributor = models.ForeignKey(Contributor)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    amount_monetary = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    amount_nonmonetary = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    individual_recipient = models.ForeignKey(Candidacy)
    
    class Meta:
        ordering = ('-date',)
    
    def __unicode__ (self):
        return u"%s contributed %s to %s (%s) on %s" % (self.contributor.name, self.amount, self.individual_recipient.candidate, self.individual_recipient.party, self.date)

########NEW FILE########
__FILENAME__ = views
# Create your views here.

########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.hansards.models import *

class DocumentOptions(admin.ModelAdmin):
    list_display=('number', 'date', 'session', 'document_type', 'committeemeeting')
    list_filter=('document_type', 'session', 'date', 'multilingual', 'public')
    
admin.site.register(Document, DocumentOptions)
admin.site.register(Statement)
########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Hansard'
        db.create_table('hansards_hansard', (
            ('sequence', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=6, blank=True)),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Session'])),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('hansards', ['Hansard'])

        # Adding model 'HansardCache'
        db.create_table('hansards_hansardcache', (
            ('hansard', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hansards.Hansard'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('hansards', ['HansardCache'])

        # Adding model 'Statement'
        db.create_table('hansards_statement', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ElectedMember'], null=True, blank=True)),
            ('hansard', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hansards.Hansard'])),
            ('sequence', self.gf('django.db.models.fields.IntegerField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('who', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('wordcount', self.gf('django.db.models.fields.IntegerField')()),
            ('heading', self.gf('django.db.models.fields.CharField')(max_length=110, blank=True)),
            ('topic', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('hansards', ['Statement'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Hansard'
        db.delete_table('hansards_hansard')

        # Deleting model 'HansardCache'
        db.delete_table('hansards_hansardcache')

        # Deleting model 'Statement'
        db.delete_table('hansards_statement')
    
    
    models = {
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.hansard': {
            'Meta': {'object_name': 'Hansard'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'object_name': 'Statement'},
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {})
        }
    }
    
    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0002_bills
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding M2M table for field bills on 'Statement'
        db.create_table('hansards_statement_bills', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('statement', models.ForeignKey(orm['hansards.statement'], null=False)),
            ('bill', models.ForeignKey(orm['bills.bill'], null=False))
        ))
        db.create_unique('hansards_statement_bills', ['statement_id', 'bill_id'])
    
    
    def backwards(self, orm):
        
        # Removing M2M table for field bills on 'Statement'
        db.delete_table('hansards_statement_bills')
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.hansard': {
            'Meta': {'object_name': 'Hansard'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'blank': 'True'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {})
        }
    }
    
    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0003_pol_shortcut
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Statement.politician'
        db.add_column('hansards_statement', 'politician', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Politician'], null=True, blank=True), keep_default=False)

        # Adding index on 'Statement', fields ['sequence']
        db.create_index('hansards_statement', ['sequence'])
    
    
    def backwards(self, orm):
        
        # Deleting field 'Statement.politician'
        db.delete_column('hansards_statement', 'politician_id')

        # Removing index on 'Statement', fields ['sequence']
        db.delete_index('hansards_statement', ['sequence'])
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.hansard': {
            'Meta': {'object_name': 'Hansard'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'blank': 'True'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {})
        }
    }
    
    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0004_time_index
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding index on 'Statement', fields ['time']
        db.create_index('hansards_statement', ['time'])
    
    
    def backwards(self, orm):
        
        # Removing index on 'Statement', fields ['time']
        db.delete_index('hansards_statement', ['time'])
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'colour': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.hansard': {
            'Meta': {'object_name': 'Hansard'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'blank': 'True'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {})
        }
    }
    
    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0005_april18
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Statement.speaker'
        db.add_column('hansards_statement', 'speaker', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True), keep_default=False)

        # Adding field 'Statement.written_question'
        db.add_column('hansards_statement', 'written_question', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding M2M table for field mentioned_politicians on 'Statement'
        db.create_table('hansards_statement_mentioned_politicians', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('statement', models.ForeignKey(orm['hansards.statement'], null=False)),
            ('politician', models.ForeignKey(orm['core.politician'], null=False))
        ))
        db.create_unique('hansards_statement_mentioned_politicians', ['statement_id', 'politician_id'])
    
    
    def backwards(self, orm):
        
        # Deleting field 'Statement.speaker'
        db.delete_column('hansards_statement', 'speaker')

        # Deleting field 'Statement.written_question'
        db.delete_column('hansards_statement', 'written_question')

        # Removing M2M table for field mentioned_politicians on 'Statement'
        db.delete_table('hansards_statement_mentioned_politicians')
    
    
    models = {
        'bills.bill': {
            'Meta': {'object_name': 'Bill'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.hansard': {
            'Meta': {'object_name': 'Hansard'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'blank': 'True'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'speaker': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        }
    }
    
    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0006_wordoftheday
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Hansard.wordoftheday'
        db.add_column('hansards_hansard', 'wordoftheday', self.gf('django.db.models.fields.CharField')(default='', max_length=20, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Hansard.wordoftheday'
        db.delete_column('hansards_hansard', 'wordoftheday')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('number_only',)", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.hansard': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Hansard'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'wordoftheday': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'speaker': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0007_auto__add_field_hansard_wordcloud
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Hansard.wordcloud'
        db.add_column('hansards_hansard', 'wordcloud', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Hansard.wordcloud'
        db.delete_column('hansards_hansard', 'wordcloud')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('number_only',)", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.hansard': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Hansard'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'wordoftheday': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'hansard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Hansard']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'speaker': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0008_rename_to_document
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        db.rename_table('hansards_hansard', 'hansards_document')
        db.rename_column('hansards_hansardcache', 'hansard_id', 'document_id')
        db.rename_column('hansards_statement', 'hansard_id', 'document_id')


    def backwards(self, orm):
        
        db.rename_table('hansards_document', 'hansards_hansard')
        db.rename_column('hansards_hansardcache', 'document_id', 'hansard_id')
        db.rename_column('hansards_statement', 'document_id', 'hansard_id')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('number_only',)", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'wordoftheday': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'speaker': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0009_document_fields
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        db.rename_column('hansards_document', 'wordoftheday', 'most_frequent_word')

        # Deleting field 'Document.sequence'
        db.delete_column('hansards_document', 'sequence')

        # Adding field 'Document.document_type'
        db.add_column('hansards_document', 'document_type', self.gf('django.db.models.fields.CharField')(default='D', max_length=1, db_index=True), keep_default=False)

        # Adding field 'Document.source_id'
        db.add_column('hansards_document', 'source_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):

        # Adding field 'Document.sequence'
        db.add_column('hansards_document', 'sequence', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Deleting field 'Document.document_type'
        db.delete_column('hansards_document', 'document_type')

        # Deleting field 'Document.source_id'
        db.delete_column('hansards_document', 'source_id')

        db.rename_column('hansards_document', 'most_frequent_word', 'wordoftheday')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('number_only',)", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parlpage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '110', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'speaker': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0010_statement_fields
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding index on 'Document', fields ['source_id']
        db.create_index('hansards_document', ['source_id'])

        db.rename_column('hansards_statement', 'topic', 'h2')

        db.rename_column('hansards_statement', 'text', 'content_en')

        db.rename_column('hansards_statement', 'speaker', 'procedural')

        db.rename_column('hansards_statement', 'heading', 'h1')

        # Adding field 'Statement.h1'
        db.alter_column('hansards_statement', 'h1', self.gf('django.db.models.fields.CharField')(default='', max_length=300, blank=True))

        # Adding field 'Statement.h2'
        db.alter_column('hansards_statement', 'h2', self.gf('django.db.models.fields.CharField')(default='', max_length=300, blank=True))

        # Adding field 'Statement.h3'
        db.add_column('hansards_statement', 'h3', self.gf('django.db.models.fields.CharField')(default='', max_length=300, blank=True), keep_default=False)

        # Adding field 'Statement.who_hocid'
        db.add_column('hansards_statement', 'who_hocid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Statement.content_fr'
        db.add_column('hansards_statement', 'content_fr', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Statement.statement_type'
        db.add_column('hansards_statement', 'statement_type', self.gf('django.db.models.fields.CharField')(default='', max_length=15, blank=True), keep_default=False)

        db.delete_column('hansards_statement', 'written_question')

        db.add_column('hansards_statement', 'written_question', self.gf('django.db.models.fields.CharField')(default='', max_length=1, blank=True), keep_default=False)

        # Changing field 'Statement.time'
        db.alter_column('hansards_statement', 'time', self.gf('django.db.models.fields.DateTimeField')())
        

    def backwards(self, orm):
        
        # Removing index on 'Document', fields ['source_id']
        db.delete_index('hansards_document', ['source_id'])

        db.rename_column('hansards_statement', 'h2', 'topic')
        # Adding field 'Statement.topic'
        db.alter_column('hansards_statement', 'topic', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True))

        db.rename_column('hansards_statement', 'content_en', 'text')

        db.rename_column('hansards_statement', 'procedural', 'speaker')

        db.rename_column('hansards_statement', 'h1', 'heading')
        db.alter_column('hansards_statement', 'heading', self.gf('django.db.models.fields.CharField')(default='', max_length=110, blank=True))

        # Deleting field 'Statement.h3'
        db.delete_column('hansards_statement', 'h3')

        # Deleting field 'Statement.who_hocid'
        db.delete_column('hansards_statement', 'who_hocid')

        # Deleting field 'Statement.content_fr'
        db.delete_column('hansards_statement', 'content_fr')

        # Deleting field 'Statement.statement_type'
        db.delete_column('hansards_statement', 'statement_type')

        db.delete_column('hansards_statement', 'written_question')

        # Changing field 'Statement.written_question'
        db.add_column('hansards_statement', 'written_question', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'Statement.time'
        db.alter_column('hansards_statement', 'time', self.gf('django.db.models.fields.DateTimeField')(null=True))


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0011_statement_data
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

import re, sys
from django.core import urlresolvers

from parliament.core.templatetags.markup import markdown

r_statement_affil = re.compile(r'<(bill|pol) id="(\d+)" name="(.*?)">(.+?)</\1>', re.UNICODE)
def statement_affil_link(match):
    if match.group(1) == 'bill':
        # FIXME hardcode url for speed?
        view = 'parliament.bills.views.bill_pk_redirect'
    else:
        view = 'parliament.politicians.views.politician'
    return '<a href="%s" class="related_link %s" title="%s">%s</a>' % \
            (urlresolvers.reverse(view, args=(match.group(2),)),
             ('legislation' if match.group(1) == 'bill' else 'politician'),
             match.group(3), match.group(4))

class Migration(DataMigration):

    def forwards(self, orm):

        def _process_statements(qs):
            for s in qs:
                _process_statement(s)
        def _process_statement(s):
            s.content_en = r_statement_affil.sub(statement_affil_link, s.content_en)
            s.content_en = markdown(s.content_en)
            if s.who == 'Proceedings':
                s.who = ''
            s.save()

        for n in range(500):
            sys.stderr.write("%s\n" % n)
            sys.stderr.flush()
            _process_statements(orm.Statement.objects.filter(sequence=n))
        _process_statements(orm.Statement.objects.filter(sequence__gte=500))

    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0012_document_docid
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

import re

class Migration(DataMigration):

    def forwards(self, orm):
        for doc in orm.Document.objects.all():
            match = re.search(r'docid=(\d+)', doc.url.lower())
            if match:
                doc.source_id = int(match.group(1))
                doc.save()

    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.hansardcache': {
            'Meta': {'object_name': 'HansardCache'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0013_remove_cache_table
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'HansardCache'
        db.delete_table('hansards_hansardcache')

        # Deleting field 'Document.url'
        db.delete_column('hansards_document', 'url')

        # Adding field 'Document.downloaded'
        db.add_column('hansards_document', 'downloaded', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Changing field 'Document.source_id'
        db.alter_column('hansards_document', 'source_id', self.gf('django.db.models.fields.IntegerField')(unique=True))

        # Adding unique constraint on 'Document', fields ['source_id']
        db.create_unique('hansards_document', ['source_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Document', fields ['source_id']
        db.delete_unique('hansards_document', ['source_id'])

        # Adding model 'HansardCache'
        db.create_table('hansards_hansardcache', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hansards.Document'])),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('hansards', ['HansardCache'])

        # Adding field 'Document.url'
        db.add_column('hansards_document', 'url', self.gf('django.db.models.fields.URLField')(default='', max_length=200), keep_default=False)

        # Deleting field 'Document.downloaded'
        db.delete_column('hansards_document', 'downloaded')

        # Changing field 'Document.source_id'
        db.alter_column('hansards_document', 'source_id', self.gf('django.db.models.fields.IntegerField')(null=True))


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0014_who_context
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Statement.source_id'
        db.add_column('hansards_statement', 'source_id', self.gf('django.db.models.fields.CharField')(default='', max_length=15, blank=True), keep_default=False)

        # Adding field 'Statement.who_context'
        db.add_column('hansards_statement', 'who_context', self.gf('django.db.models.fields.CharField')(default='', max_length=300, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Statement.source_id'
        db.delete_column('hansards_statement', 'source_id')

        # Deleting field 'Statement.who_context'
        db.delete_column('hansards_statement', 'who_context')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0015_longer_type
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Statement.statement_type'
        db.alter_column('hansards_statement', 'statement_type', self.gf('django.db.models.fields.CharField')(max_length=35))


    def backwards(self, orm):
        
        # Changing field 'Statement.statement_type'
        db.alter_column('hansards_statement', 'statement_type', self.gf('django.db.models.fields.CharField')(max_length=15))


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0016_document_flags
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Document.public'
        db.add_column('hansards_document', 'public', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Document.multilingual'
        db.add_column('hansards_document', 'multilingual', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Document.public'
        db.delete_column('hansards_document', 'public')

        # Deleting field 'Document.multilingual'
        db.delete_column('hansards_document', 'multilingual')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0017_set_document_flags
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        # Set documents with statements to public
        for d in orm.Document.objects.all().annotate(scount=models.Count('statement'))\
            .filter(scount__gt=0):
            d.public = True
            s = d.statement_set.all()[0]
            if s.content_fr:
                d.multilingual = True
            d.save()


    def backwards(self, orm):
        orm.Document.objects.all().update(multilingual=False, public=False)


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0018_statement_slug
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'OldSequenceMapping'
        db.create_table('hansards_oldsequencemapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hansards.Document'])),
            ('sequence', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=100, db_index=True)),
        ))
        db.send_create_signal('hansards', ['OldSequenceMapping'])

        # Adding unique constraint on 'OldSequenceMapping', fields ['document', 'sequence']
        db.create_unique('hansards_oldsequencemapping', ['document_id', 'sequence'])

        # Adding field 'Statement.slug'
        db.add_column('hansards_statement', 'slug', self.gf('django.db.models.fields.SlugField')(default=None, max_length=100, null=True, db_index=True, blank=True), keep_default=False)

        # Adding unique constraint on 'Statement', fields ['document', 'slug']
        db.create_unique('hansards_statement', ['document_id', 'slug'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Statement', fields ['document', 'slug']
        db.delete_unique('hansards_statement', ['document_id', 'slug'])

        # Removing unique constraint on 'OldSequenceMapping', fields ['document', 'sequence']
        db.delete_unique('hansards_oldsequencemapping', ['document_id', 'sequence'])

        # Deleting model 'OldSequenceMapping'
        db.delete_table('hansards_oldsequencemapping')

        # Deleting field 'Statement.slug'
        db.delete_column('hansards_statement', 'slug')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.oldsequencemapping': {
            'Meta': {'unique_together': "(('document', 'sequence'),)", 'object_name': 'OldSequenceMapping'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sequence': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': 'None', 'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0019_populate_slugs
# encoding: utf-8
import datetime
import re

from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        from collections import defaultdict
        from django.template.defaultfilters import slugify

        r_mister = re.compile(r'^(Mr|Mrs|Ms|Miss|Hon|Right Hon|M|Mme)\.?\s+')
        def _get_display_name(st):
            if st.member_id:
                return st.politician.name
            else:
                return r_mister.sub('', st.who)

        def _set_slugs(statements):
            counter = defaultdict(int)
            for statement in statements:
                slug = slugify(_get_display_name(statement))[:50]
                if not slug:
                    slug = 'procedural'
                counter[slug] += 1
                slug = slug + '-%s' % counter[slug]
                orm.Statement.objects.filter(id=statement.id).update(slug=slug)

        for document in orm.Document.objects.all():
            _set_slugs(document.statement_set.filter(slug__isnull=True).select_related('politician'))


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.oldsequencemapping': {
            'Meta': {'unique_together': "(('document', 'sequence'),)", 'object_name': 'OldSequenceMapping'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sequence': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': 'None', 'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0020_slugs_not_null
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Statement.slug'
        db.alter_column('hansards_statement', 'slug', self.gf('django.db.models.fields.SlugField')(max_length=100))


    def backwards(self, orm):
        
        # Changing field 'Statement.slug'
        db.alter_column('hansards_statement', 'slug', self.gf('django.db.models.fields.SlugField')(max_length=100, null=True))


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.oldsequencemapping': {
            'Meta': {'unique_together': "(('document', 'sequence'),)", 'object_name': 'OldSequenceMapping'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sequence': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0021_document_skip
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Document.skip_parsing'
        db.add_column('hansards_document', 'skip_parsing', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Document.skip_parsing'
        db.delete_column('hansards_document', 'skip_parsing')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.oldsequencemapping': {
            'Meta': {'unique_together': "(('document', 'sequence'),)", 'object_name': 'OldSequenceMapping'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sequence': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0022_urlcache
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Statement.urlcache'
        db.add_column('hansards_statement', 'urlcache', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding index on 'Statement', fields ['who_hocid']
        db.create_index('hansards_statement', ['who_hocid'])


    def backwards(self, orm):
        
        # Removing index on 'Statement', fields ['who_hocid']
        db.delete_index('hansards_statement', ['who_hocid'])

        # Deleting field 'Statement.urlcache'
        db.delete_column('hansards_statement', 'urlcache')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.oldsequencemapping': {
            'Meta': {'unique_together': "(('document', 'sequence'),)", 'object_name': 'OldSequenceMapping'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sequence': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'urlcache': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0023_statement_fr
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Statement.h1_fr'
        db.add_column('hansards_statement', 'h1_fr', self.gf('django.db.models.fields.CharField')(default='', max_length=400, blank=True), keep_default=False)

        # Adding field 'Statement.h2_fr'
        db.add_column('hansards_statement', 'h2_fr', self.gf('django.db.models.fields.CharField')(default='', max_length=400, blank=True), keep_default=False)

        # Adding field 'Statement.h3_fr'
        db.add_column('hansards_statement', 'h3_fr', self.gf('django.db.models.fields.CharField')(default='', max_length=400, blank=True), keep_default=False)

        # Adding field 'Statement.who_fr'
        db.add_column('hansards_statement', 'who_fr', self.gf('django.db.models.fields.CharField')(default='', max_length=500, blank=True), keep_default=False)

        # Adding field 'Statement.who_context_fr'
        db.add_column('hansards_statement', 'who_context_fr', self.gf('django.db.models.fields.CharField')(default='', max_length=500, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Statement.h1_fr'
        db.delete_column('hansards_statement', 'h1_fr')

        # Deleting field 'Statement.h2_fr'
        db.delete_column('hansards_statement', 'h2_fr')

        # Deleting field 'Statement.h3_fr'
        db.delete_column('hansards_statement', 'h3_fr')

        # Deleting field 'Statement.who_fr'
        db.delete_column('hansards_statement', 'who_fr')

        # Deleting field 'Statement.who_context_fr'
        db.delete_column('hansards_statement', 'who_context_fr')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.oldsequencemapping': {
            'Meta': {'unique_together': "(('document', 'sequence'),)", 'object_name': 'OldSequenceMapping'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sequence': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h1_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'h2': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'h3': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'urlcache': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'who_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = 0024_rename_en
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        db.rename_column('hansards_statement', 'h1', 'h1_en')
        db.rename_column('hansards_statement', 'h2', 'h2_en')
        db.rename_column('hansards_statement', 'h3', 'h3_en')
        db.rename_column('hansards_statement', 'who', 'who_en')
        db.rename_column('hansards_statement', 'who_context', 'who_context_en')


    def backwards(self, orm):
        
        db.rename_column('hansards_statement', 'h1_en', 'h1')
        db.rename_column('hansards_statement', 'h2_en', 'h2')
        db.rename_column('hansards_statement', 'h3_en', 'h3')
        db.rename_column('hansards_statement', 'who_en', 'who')
        db.rename_column('hansards_statement', 'who_context_en', 'who_context')


    models = {
        'bills.bill': {
            'Meta': {'ordering': "('privatemember', 'institution', 'number_only')", 'object_name': 'Bill'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'law': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'number_only': ('django.db.models.fields.SmallIntegerField', [], {}),
            'privatemember': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'through': "orm['bills.BillInSession']", 'symmetrical': 'False'}),
            'short_title_en': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_title_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status_fr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_docid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bills.billinsession': {
            'Meta': {'object_name': 'BillInSession'},
            'bill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bills.Bill']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduced': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'legisinfo_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'sponsor_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'sponsor_politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'})
        },
        'core.electedmember': {
            'Meta': {'object_name': 'ElectedMember'},
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Party']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']"}),
            'riding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Riding']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Session']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'core.party': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Party'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.politician': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Politician'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'headshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        },
        'core.riding': {
            'Meta': {'ordering': "('province', 'name')", 'object_name': 'Riding'},
            'edid': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        },
        'core.session': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Session'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parliamentnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sessnum': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'hansards.document': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Document'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'downloaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_frequent_word': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'multilingual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Session']"}),
            'skip_parsing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'wordcloud': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'hansards.oldsequencemapping': {
            'Meta': {'unique_together': "(('document', 'sequence'),)", 'object_name': 'OldSequenceMapping'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sequence': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'hansards.statement': {
            'Meta': {'ordering': "('sequence',)", 'unique_together': "(('document', 'slug'),)", 'object_name': 'Statement'},
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bills.Bill']", 'symmetrical': 'False', 'blank': 'True'}),
            'content_en': ('django.db.models.fields.TextField', [], {}),
            'content_fr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansards.Document']"}),
            'h1_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h1_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'h2_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h2_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'h3_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'h3_fr': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ElectedMember']", 'null': 'True', 'blank': 'True'}),
            'mentioned_politicians': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'statements_with_mentions'", 'blank': 'True', 'to': "orm['core.Politician']"}),
            'politician': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Politician']", 'null': 'True', 'blank': 'True'}),
            'procedural': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'statement_type': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'urlcache': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'who_context_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_context_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'who_en': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'who_fr': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'who_hocid': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'wordcount': ('django.db.models.fields.IntegerField', [], {}),
            'written_question': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['hansards']

########NEW FILE########
__FILENAME__ = models
#coding: utf-8

import gzip, os, re
from collections import defaultdict
import datetime

from django.db import models
from django.conf import settings
from django.core import urlresolvers
from django.core.files.base import ContentFile
from django.template.defaultfilters import slugify
from django.utils.datastructures import SortedDict
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from parliament.core.models import Session, ElectedMember, Politician
from parliament.core import parsetools
from parliament.core.utils import memoize_property, language_property
from parliament.activity import utils as activity

import logging
logger = logging.getLogger(__name__)

class DebateManager(models.Manager):

    def get_query_set(self):
        return super(DebateManager, self).get_query_set().filter(document_type=Document.DEBATE)

class EvidenceManager(models.Manager):

    def get_query_set(self):
        return super(EvidenceManager, self).get_query_set().filter(document_type=Document.EVIDENCE)

class NoStatementManager(models.Manager):
    """Manager restricts to Documents that haven't had statements parsed."""

    def get_query_set(self):
        return super(NoStatementManager, self).get_query_set()\
            .annotate(scount=models.Count('statement'))\
            .exclude(scount__gt=0)

def url_from_docid(docid):
    return "http://www.parl.gc.ca/HousePublications/Publication.aspx?DocId=%s&Language=%s&Mode=1" % (
        docid, settings.LANGUAGE_CODE[0].upper()
    ) if docid else None

class Document(models.Model):
    
    DEBATE = 'D'
    EVIDENCE = 'E'
    
    document_type = models.CharField(max_length=1, db_index=True, choices=(
        ('D', 'Debate'),
        ('E', 'Committee Evidence'),
    ))
    date = models.DateField(blank=True, null=True)
    number = models.CharField(max_length=6, blank=True) # there exist 'numbers' with letters
    session = models.ForeignKey(Session)
    
    source_id = models.IntegerField(unique=True, db_index=True)
    
    most_frequent_word = models.CharField(max_length=20, blank=True)
    wordcloud = models.ImageField(upload_to='autoimg/wordcloud', blank=True, null=True)

    downloaded = models.BooleanField(default=False,
        help_text="Has the source data been downloaded?")
    skip_parsing = models.BooleanField(default=False,
        help_text="Don't try to parse this, presumably because of errors in the source.")

    public = models.BooleanField("Display on site?", default=False)
    multilingual = models.BooleanField("Content parsed in both languages?", default=False)

    objects = models.Manager()
    debates = DebateManager()
    evidence = EvidenceManager()
    without_statements = NoStatementManager()
    
    class Meta:
        ordering = ('-date',)
    
    def __unicode__ (self):
        if self.document_type == self.DEBATE:
            return u"Hansard #%s for %s (#%s/#%s)" % (self.number, self.date, self.id, self.source_id)
        else:
            return u"%s evidence for %s (#%s/#%s)" % (
                self.committeemeeting.committee.short_name, self.date, self.id, self.source_id)
        
    @memoize_property
    def get_absolute_url(self):
        if self.document_type == self.DEBATE:
            return urlresolvers.reverse('debate', kwargs={
                'year': self.date.year, 'month': self.date.month, 'day': self.date.day
            })
        elif self.document_type == self.EVIDENCE:
            return self.committeemeeting.get_absolute_url()

    def get_text_analysis_url(self):
        # Let's violate DRY!
        return self.get_absolute_url() + 'text-analysis/'

    def to_api_dict(self, representation):
        d = dict(
            date=unicode(self.date) if self.date else None,
            number=self.number,
            most_frequent_word={'en': self.most_frequent_word},
        )
        if representation == 'detail':
            d.update(
                source_id=self.source_id,
                source_url=self.source_url,
                session=self.session_id,
                document_type=self.get_document_type_display(),
            )
        return d

    @property
    def url(self):
        return self.source_url

    @property
    def source_url(self):
        return url_from_docid(self.source_id)
        
    def _topics(self, l):
        topics = []
        last_topic = ''
        for statement in l:
            if statement[0] and statement[0] != last_topic:
                last_topic = statement[0]
                topics.append((statement[0], statement[1]))
        return topics
        
    def topics(self):
        """Returns a tuple with (topic, statement slug) for every topic mentioned."""
        return self._topics(self.statement_set.all().values_list('h2_' + settings.LANGUAGE_CODE, 'slug'))
        
    def headings(self):
        """Returns a tuple with (heading, statement slug) for every heading mentioned."""
        return self._topics(self.statement_set.all().values_list('h1_' + settings.LANGUAGE_CODE, 'slug'))
    
    def topics_with_qp(self):
        """Returns the same as topics(), but with a link to Question Period at the start of the list."""
        statements = self.statement_set.all().values_list(
            'h2_' + settings.LANGUAGE_CODE, 'slug', 'h1_' + settings.LANGUAGE_CODE)
        topics = self._topics(statements)
        qp_seq = None
        for s in statements:
            if s[2] == 'Oral Questions':
                qp_seq = s[1]
                break
        if qp_seq is not None:
            topics.insert(0, ('Question Period', qp_seq))
        return topics

    @memoize_property
    def speaker_summary(self):
        """Returns a sorted dictionary (in order of appearance) summarizing the people
        speaking in this document.

        Keys are names, suitable for displays. Values are dicts with keys:
            slug: Slug of first statement by the person
            politician: Boolean -- is this an MP?
            description: Short title or affiliation
        """
        ids_seen = set()
        speakers = SortedDict()
        for st in self.statement_set.filter(who_hocid__isnull=False).values_list(
                'who_' + settings.LANGUAGE_CODE,            # 0
                'who_context_' + settings.LANGUAGE_CODE,    # 1
                'slug',                                     # 2
                'politician__name',                         # 3
                'who_hocid'):                               # 4
            if st[4] in ids_seen:
                continue
            ids_seen.add(st[4])
            if st[3]:
                who = st[3]
            else:
                who = parsetools.r_parens.sub('', st[0])
                who = re.sub('^\s*\S+\s+', '', who).strip() # strip honorific
            if who not in speakers:
                info = {
                    'slug': st[2],
                    'politician': bool(st[3])
                }
                if st[1]:
                    info['description'] = st[1]
                speakers[who] = info
        return speakers

    def outside_speaker_summary(self):
        """Same as speaker_summary, but only non-MPs."""
        return SortedDict(
            [(k, v) for k, v in self.speaker_summary().items() if not v['politician']]
        )

    def mp_speaker_summary(self):
        """Same as speaker_summary, but only MPs."""
        return SortedDict(
            [(k, v) for k, v in self.speaker_summary().items() if v['politician']]
        )
    
    def save_activity(self):
        statements = self.statement_set.filter(procedural=False).select_related('member', 'politician')
        politicians = set([s.politician for s in statements if s.politician])
        for pol in politicians:
            topics = {}
            wordcount = 0
            for statement in filter(lambda s: s.politician == pol, statements):
                wordcount += statement.wordcount
                if statement.topic in topics:
                    # If our statement is longer than the previous statement on this topic,
                    # use its text for the excerpt.
                    if len(statement.text_plain()) > len(topics[statement.topic][1]):
                        topics[statement.topic][1] = statement.text_plain()
                        topics[statement.topic][2] = statement.get_absolute_url()
                else:
                    topics[statement.topic] = [statement.slug, statement.text_plain(), statement.get_absolute_url()]
            for topic in topics:
                if self.document_type == Document.DEBATE:
                    activity.save_activity({
                        'topic': topic,
                        'url': topics[topic][2],
                        'text': topics[topic][1],
                    }, politician=pol, date=self.date, guid='statement_%s' % topics[topic][2], variety='statement')
                elif self.document_type == Document.EVIDENCE:
                    assert len(topics) == 1
                    if wordcount < 80:
                        continue
                    (seq, text, url) = topics.values()[0]
                    activity.save_activity({
                        'meeting': self.committeemeeting,
                        'committee': self.committeemeeting.committee,
                        'text': text,
                        'url': url,
                        'wordcount': wordcount,
                    }, politician=pol, date=self.date, guid='cmte_%s' % url, variety='committee')

    def get_filename(self, language):
        assert self.source_id
        assert language in ('en', 'fr')
        return '%d-%s.xml.gz' % (self.source_id, language)

    def get_filepath(self, language):
        filename = self.get_filename(language)
        if hasattr(settings, 'HANSARD_CACHE_DIR'):
            return os.path.join(settings.HANSARD_CACHE_DIR, filename)
        else:
            return os.path.join(settings.MEDIA_ROOT, 'document_cache', filename)

    def _save_file(self, path, content):
        out = gzip.open(path, 'wb')
        out.write(content)
        out.close()

    def get_cached_xml(self, language):
        if not self.downloaded:
            raise Exception("Not yet downloaded")
        return gzip.open(self.get_filepath(language), 'rb')

    def delete_downloaded(self):
        for lang in ('en', 'fr'):
            path = self.get_filepath(lang)
            if os.path.exists(path):
                os.unlink(path)
        self.downloaded = False
        self.save()

    def _fetch_xml(self, language):
        import urllib2
        return urllib2.urlopen('http://www.parl.gc.ca/HousePublications/Publication.aspx?DocId=%s&Language=%s&Mode=1&xml=true'
        % (self.source_id, language[0].upper())).read()

    def download(self):
        if self.downloaded:
            return True
        if self.date and self.date.year < 2006:
            raise Exception("No XML available before 2006")
        langs = ('en', 'fr')
        paths = [self.get_filepath(l) for l in langs]
        if not all((os.path.exists(p) for p in paths)):
            for path, lang in zip(paths, langs):
                self._save_file(path, self._fetch_xml(lang))
        self.downloaded = True
        self.save()

class Statement(models.Model):
    document = models.ForeignKey(Document)
    time = models.DateTimeField(db_index=True)
    source_id = models.CharField(max_length=15, blank=True)

    slug = models.SlugField(max_length=100, blank=True)
    urlcache = models.CharField(max_length=200, blank=True)

    h1_en = models.CharField(max_length=300, blank=True)
    h2_en = models.CharField(max_length=300, blank=True)
    h3_en = models.CharField(max_length=300, blank=True)
    h1_fr = models.CharField(max_length=400, blank=True)
    h2_fr = models.CharField(max_length=400, blank=True)
    h3_fr = models.CharField(max_length=400, blank=True)

    member = models.ForeignKey(ElectedMember, blank=True, null=True)
    politician = models.ForeignKey(Politician, blank=True, null=True) # a shortcut -- should == member.politician
    who_en = models.CharField(max_length=300, blank=True)
    who_fr = models.CharField(max_length=500, blank=True)
    who_hocid = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    who_context_en = models.CharField(max_length=300, blank=True)
    who_context_fr = models.CharField(max_length=500, blank=True)


    content_en = models.TextField()
    content_fr = models.TextField(blank=True)
    sequence = models.IntegerField(db_index=True)
    wordcount = models.IntegerField()

    procedural = models.BooleanField(default=False, db_index=True)
    written_question = models.CharField(max_length=1, blank=True, choices=(
        ('Q', 'Question'),
        ('R', 'Response')
    ))
    statement_type = models.CharField(max_length=35, blank=True)
    
    bills = models.ManyToManyField('bills.Bill', blank=True)
    mentioned_politicians = models.ManyToManyField(Politician, blank=True, related_name='statements_with_mentions')
        
    class Meta:
        ordering = ('sequence',)
        unique_together = (
            ('document', 'slug')
        )

    h1 = language_property('h1')
    h2 = language_property('h2')
    h3 = language_property('h3')
    who = language_property('who')
    who_context = language_property('who_context')

    def save(self, *args, **kwargs):
        if not self.wordcount:
            self.wordcount = parsetools.countWords(self.text_plain())
        self.content_en = self.content_en.replace('\n', '').replace('</p>', '</p>\n').strip()
        self.content_fr = self.content_fr.replace('\n', '').replace('</p>', '</p>\n').strip()
        if ((not self.procedural) and self.wordcount <= 300
            and ( 
                (parsetools.r_notamember.search(self.who) and re.search(r'(Speaker|Chair|président)', self.who))
                or (not self.who)
                or not any(p for p in self.content_en.split('\n') if 'class="procedural"' not in p)
            )):
            # Some form of routine, procedural statement (e.g. somethng short by the speaker)
            self.procedural = True
        if not self.urlcache:
            self.generate_url()
        super(Statement, self).save(*args, **kwargs)
            
    @property
    def date(self):
        return datetime.date(self.time.year, self.time.month, self.time.day)
    
    def generate_url(self):
        self.urlcache = "%s%s/" % (
            self.document.get_absolute_url(),
            (self.slug if self.slug else self.sequence))

    def get_absolute_url(self):
        if not self.urlcache:
            self.generate_url()
        return self.urlcache

    def __unicode__ (self):
        return u"%s speaking about %s around %s" % (self.who, self.topic, self.time)

    @property
    @memoize_property
    def content_floor(self):
        if not self.content_fr:
            return self.content_en
        el, fl = self.content_en.split('\n'), self.content_fr.split('\n')
        if len(el) != len(fl):
            logger.error("Different en/fr paragraphs in %s" % self.get_absolute_url())
            return self.content_en
        r = []
        for e, f in zip(el, fl):
            idx = e.find('data-originallang="')
            if idx and e[idx+19:idx+21] == 'fr':
                r.append(f)
            else:
                r.append(e)
        return u"\n".join(r)

            

    def text_html(self, language=settings.LANGUAGE_CODE):
        return mark_safe(getattr(self, 'content_' + language))

    def text_plain(self, language=settings.LANGUAGE_CODE):
        return (strip_tags(getattr(self, 'content_' + language)
            .replace('\n', '')
            .replace('<br>', '\n')
            .replace('</p>', '\n\n'))
            .strip())

    # temp compatibility
    @property
    def heading(self):
        return self.h1

    @property
    def topic(self):
        return self.h2
        
    def to_api_dict(self, representation):
        d = dict(
            time=unicode(self.time) if self.time else None,
            attribution={'en': self.who_en, 'fr': self.who_fr},
            content={'en': self.content_en, 'fr': self.content_fr},
            url=self.get_absolute_url(),
            politician_url=self.politician.get_absolute_url() if self.politician else None,
            politician_membership_url=urlresolvers.reverse('politician_membership',
                kwargs={'member_id': self.member_id}) if self.member_id else None,
            procedural=self.procedural,
            source_id=self.source_id
        )
        for h in ('h1', 'h2', 'h3'):
            if getattr(self, h):
                d[h] = {'en': getattr(self, h + '_en'), 'fr': getattr(self, h + '_fr')}
        d['document_url'] = d['url'][:d['url'].rstrip('/').rfind('/')+1]
        return d
    
    @property
    @memoize_property    
    def name_info(self):
        info = {
            'post': None,
            'named': True
        }
        if not self.member:
            info['display_name'] = parsetools.r_mister.sub('', self.who)
            if self.who_context:
                if self.who_context in self.who:
                    info['display_name'] = parsetools.r_parens.sub('', info['display_name'])
                    info['post'] = self.who_context
                else:
                    info['post_reminder'] = self.who_context
                if self.who_hocid:
                    info['url'] = '/search/?q=Witness%%3A+%%22%s%%22' % self.who_hocid
        else:
            info['url'] = self.member.politician.get_absolute_url()
            if parsetools.r_notamember.search(self.who):
                info['display_name'] = self.who
                if self.member.politician.name in self.who:
                    info['display_name'] = re.sub(r'\(.+\)', '', self.who)
                info['named'] = False
            elif not '(' in self.who or not parsetools.r_politicalpost.search(self.who):
                info['display_name'] = self.member.politician.name
            else:
                post_match = re.search(r'\((.+)\)', self.who)
                if post_match:
                    info['post'] = post_match.group(1).split(',')[0]
                info['display_name'] = self.member.politician.name
        return info

    @staticmethod
    def set_slugs(statements):
        counter = defaultdict(int)
        for statement in statements:
            slug = slugify(statement.name_info['display_name'])[:50]
            if not slug:
                slug = 'procedural'
            counter[slug] += 1
            statement.slug = slug + '-%s' % counter[slug]

    @property
    def committee_name(self):
        if self.document.document_type != Document.EVIDENCE:
            return ''
        return self.document.committeemeeting.committee.short_name

    @property
    def committee_slug(self):
        if self.document.document_type != Document.EVIDENCE:
            return ''
        return self.document.committeemeeting.committee.slug

class OldSequenceMapping(models.Model):
    document = models.ForeignKey(Document)
    sequence = models.PositiveIntegerField()
    slug = models.SlugField(max_length=100)

    class Meta:
        unique_together = (
            ('document', 'sequence')
        )

    def __unicode__(self):
        return u"%s -> %s" % (self.sequence, self.slug)
            

########NEW FILE########
__FILENAME__ = parseall

from parliament.core import datautil
import sys, os
reload(sys)
sys.setdefaultencoding('utf8')
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0) # unbuffered stdout

datautil.parse_all_hansards()

        
########NEW FILE########
__FILENAME__ = redirect_views
import datetime

from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404

from parliament.hansards.models import Document, OldSequenceMapping

def hansard_redirect(request, hansard_id=None, hansard_date=None, sequence=None, only=False):
    if not (hansard_id or hansard_date):
        raise Http404

    if hansard_id:
        doc = get_object_or_404(Document.debates, pk=hansard_id)
    else:
        doc = get_object_or_404(Document.debates, date=datetime.date(*[int(x) for x in hansard_date.split('-')]))

    url = doc.get_absolute_url()

    if sequence:
        try:
            map = OldSequenceMapping.objects.get(document=doc, sequence=sequence)
            sequence = map.slug
        except OldSequenceMapping.DoesNotExist:
            pass
        url += '%s/' % sequence

    if only:
        url += 'only/'

    return HttpResponsePermanentRedirect(url)
########NEW FILE########
__FILENAME__ = search_indexes
from haystack import site
from haystack import indexes

from parliament.search.index import SearchIndex
from parliament.hansards.models import Statement

class StatementIndex(SearchIndex):
    text = indexes.CharField(document=True, model_attr='text_plain')
    searchtext = indexes.CharField(stored=False, use_template=True)
    date = indexes.DateTimeField(model_attr='time')
    politician = indexes.CharField(use_template=True)
    politician_id = indexes.CharField(model_attr='member__politician__identifier', null=True)
    who_hocid = indexes.IntegerField(model_attr='who_hocid', null=True)
    party = indexes.CharField(model_attr='member__party__short_name', null=True)
    province = indexes.CharField(model_attr='member__riding__province', null=True)
    topic = indexes.CharField(model_attr='topic')
    url = indexes.CharField(model_attr='get_absolute_url', indexed=False)
    doc_url = indexes.CharField(model_attr='document__get_absolute_url')
    committee = indexes.CharField(model_attr='committee_name')
    committee_slug = indexes.CharField(model_attr='committee_slug')
    doctype = indexes.CharField(null=True)
    
    def get_queryset(self):
        return Statement.objects.all().prefetch_related(
            'member__politician', 'member__party', 'member__riding', 'document',
            'document__committeemeeting__committee'
        ).order_by('-date')

    def prepare_doctype(self, obj):
        if obj.committee_name:
            return 'committee'
        else:
            return 'debate'

site.register(Statement, StatementIndex)
########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import patterns, include, url

urlpatterns = patterns('parliament.hansards.views',
    url(r'^$', 'index', name='debates'),
    (r'^(?P<year>\d{4})/$', 'by_year'),
    (r'^(?P<year>\d{4})/(?P<month>\d{1,2})/', include(patterns('parliament.hansards.views',
        (r'^$', 'by_month'),
        url(r'^(?P<day>\d{1,2})/$', 'hansard', name='debate'),
        url(r'^(?P<day>\d{1,2})/text-analysis/$', 'hansard_analysis', name='debate_analysis'),
        url(r'^(?P<day>\d{1,2})/(?P<slug>[a-zA-Z0-9-]+)/$', 'hansard_statement', name="debate"),
        url(r'^(?P<day>\d{1,2})/(?P<slug>[a-zA-Z0-9-]+)/only/$',
            'debate_permalink', name="hansard_statement_only"),

    ))),
    (r'^(?P<document_id>\d+)/local/(?P<language>en|fr)/$', 'document_cache'),
)
########NEW FILE########
__FILENAME__ = views
import datetime
from urllib import urlencode

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core import urlresolvers
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import loader, RequestContext
from django.views.generic.dates import (ArchiveIndexView, YearArchiveView, MonthArchiveView)
from django.views.decorators.vary import vary_on_headers

from parliament.committees.models import CommitteeMeeting
from parliament.core.api import ModelDetailView, ModelListView, APIFilters
from parliament.hansards.models import Document, Statement
from parliament.text_analysis.models import TextAnalysis
from parliament.text_analysis.views import TextAnalysisView

def _get_hansard(year, month, day):
    return get_object_or_404(Document.debates,
        date=datetime.date(int(year), int(month), int(day)))

class HansardView(ModelDetailView):

    resource_name = 'House debate'

    def get_object(self, request, **kwargs):
        return _get_hansard(**kwargs)

    def get_html(self, request, **kwargs):
        return document_view(request, _get_hansard(**kwargs))

    def get_related_resources(self, request, obj, result):
        return {
            'speeches_url': urlresolvers.reverse('speeches') + '?' +
                urlencode({'document': result['url']}),
            'debates_url': urlresolvers.reverse('debates')
        }
hansard = HansardView.as_view()


class HansardStatementView(ModelDetailView):

    resource_name = 'Speech (House debate)'

    def get_object(self, request, year, month, day, slug):
        date = datetime.date(int(year), int(month), int(day))
        return Statement.objects.get(
            document__document_type='D',
            document__date=date,
            slug=slug
        )

    def get_related_resources(self, request, qs, result):
        return {
            'document_speeches_url': urlresolvers.reverse('speeches') + '?' +
                urlencode({'document': result['document_url']}),
        }

    def get_html(self, request, year, month, day, slug):
        return document_view(request, _get_hansard(year, month, day), slug=slug)
hansard_statement = HansardStatementView.as_view()

def document_redirect(request, document_id, slug=None):
    try:
        document = Document.objects.select_related(
            'committeemeeting', 'committeemeeting__committee').get(
            pk=document_id)
    except Document.DoesNotExist:
        raise Http404
    url = document.get_absolute_url()
    if slug:
        url += "%s/" % slug
    return HttpResponsePermanentRedirect(url)

@vary_on_headers('X-Requested-With')
def document_view(request, document, meeting=None, slug=None):

    per_page = 15
    if 'singlepage' in request.GET:
        per_page = 50000
    
    statement_qs = Statement.objects.filter(document=document)\
        .select_related('member__politician', 'member__riding', 'member__party')
    paginator = Paginator(statement_qs, per_page)

    highlight_statement = None
    try:
        if slug is not None and 'page' not in request.GET:
            if slug.isdigit():
                highlight_statement = int(slug)
            else:
                highlight_statement = statement_qs.filter(slug=slug).values_list('sequence', flat=True)[0]
            page = int(highlight_statement/per_page) + 1
        else:
            page = int(request.GET.get('page', '1'))
    except (ValueError, IndexError):
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        statements = paginator.page(page)
    except (EmptyPage, InvalidPage):
        statements = paginator.page(paginator.num_pages)
    
    if highlight_statement is not None:
        try:
            highlight_statement = filter(
                    lambda s: s.sequence == highlight_statement, statements.object_list)[0]
        except IndexError:
            raise Http404
        
    ctx = {
        'document': document,
        'page': statements,
        'highlight_statement': highlight_statement,
        'singlepage': 'singlepage' in request.GET,
        'allow_single_page': True
    }
    if document.document_type == Document.DEBATE:
        ctx.update({
            'hansard': document,
            'pagination_url': document.get_absolute_url(),
        })
    elif document.document_type == Document.EVIDENCE:
        ctx.update({
            'meeting': meeting,
            'committee': meeting.committee,
            'pagination_url': meeting.get_absolute_url(),
        })

    if request.is_ajax():
        t = loader.get_template("hansards/statement_page.inc")
    else:
        if document.document_type == Document.DEBATE:
            t = loader.get_template("hansards/hansard_detail.html")
        elif document.document_type == Document.EVIDENCE:
            t = loader.get_template("committees/meeting_evidence.html")
        ctx['wordcloud_js'] = TextAnalysis.objects.get_wordcloud_js(
            key=document.get_text_analysis_url())

    return HttpResponse(t.render(RequestContext(request, ctx)))


class SpeechesView(ModelListView):

    def document_filter(qs, view, filter_name, filter_extra, val):
        u = val.rstrip('/').split('/')
        if u[-4] == 'debates':
            # /debates/2013/2/15/
            date = datetime.date(int(u[-3]), int(u[-2]), int(u[-1]))
            return qs.filter(
                document__document_type='D',
                document__date=date
            ).order_by('sequence')
        elif u[-4] == 'committees':
            # /commmittees/national-defence/41-1/63/
            meeting = CommitteeMeeting.objects.get(
                committee__slug=u[-3], session=u[-2], number=u[-1])
            return qs.filter(document=meeting.evidence_id).order_by('sequence')
    document_filter.help = "the URL of the debate or committee meeting"

    filters = {
        'procedural': APIFilters.dbfield(help="is this a short, routine procedural speech? True or False"),
        'document': document_filter,
        'politician': APIFilters.politician(),
        'politician_membership': APIFilters.fkey(lambda u: {'member': u[-1]}),
        'time': APIFilters.dbfield(filter_types=APIFilters.numeric_filters,
            help="e.g. time__range=2012-10-19 10:00,2012-10-19 11:00"),
        'mentioned_politician': APIFilters.politician('mentioned_politicians'),
        'mentioned_bill': APIFilters.fkey(lambda u: {
            'bills__billinsession__session': u[-2],
            'bills__number': u[-1]
        }, help="e.g. /bills/41-1/C-14/")
    }

    resource_name = 'Speeches'

    def get_qs(self, request):
        qs = Statement.objects.all().prefetch_related('politician')
        if 'document' not in request.GET:
            qs = qs.order_by('-time')
        return qs
speeches = SpeechesView.as_view()

class DebatePermalinkView(ModelDetailView):

    def _get_objs(self, request, slug, year, month, day):
        doc = _get_hansard(year, month, day)
        if slug.isdigit():
            statement = get_object_or_404(Statement, document=doc, sequence=slug)
        else:
            statement = get_object_or_404(Statement, document=doc, slug=slug)
        return doc, statement

    def get_json(self, request, **kwargs):
        url = self._get_objs(request, **kwargs)[1].get_absolute_url()
        return HttpResponseRedirect(url + '?' + request.GET.urlencode())

    def get_html(self, request, **kwargs):
        doc, statement = self._get_objs(request, **kwargs)
        return statement_permalink(request, doc, statement, "hansards/statement_permalink.html",
            hansard=doc)
debate_permalink = DebatePermalinkView.as_view()

def statement_permalink(request, doc, statement, template, **kwargs):
    """A page displaying only a single statement. Used as a non-JS permalink."""

    if statement.politician:
        who = statement.politician.name
    else:
        who = statement.who
    title = who
    
    if statement.topic:
        title += u' on %s' % statement.topic
    elif 'committee' in kwargs:
        title += u' at the ' + kwargs['committee'].title

    t = loader.get_template(template)
    ctx = {
        'title': title,
        'who': who,
        'page': {'object_list': [statement]},
        'doc': doc,
        'statement': statement,
        'statements_full_date': True,
        'statement_url': statement.get_absolute_url(),
        #'statements_context_link': True
    }
    ctx.update(kwargs)
    return HttpResponse(t.render(RequestContext(request, ctx)))
    
def document_cache(request, document_id, language):
    document = get_object_or_404(Document, pk=document_id)
    xmlfile = document.get_cached_xml(language)
    resp = HttpResponse(xmlfile.read(), content_type="text/xml")
    xmlfile.close()
    return resp

class TitleAdder(object):

    def get_context_data(self, **kwargs):
        context = super(TitleAdder, self).get_context_data(**kwargs)
        context.update(title=self.page_title)
        return context

class APIArchiveView(ModelListView):

    resource_name = 'House debates'

    filters = {
        'session': APIFilters.dbfield(help='e.g. 41-1'),
        'date': APIFilters.dbfield(help='e.g. date__range=2010-01-01,2010-09-01'),
        'number': APIFilters.dbfield(help='each Hansard in a session is given a sequential #'),
    }

    def get_html(self, request, **kwargs):
        return self.get(request, **kwargs)

    def get_qs(self, request, **kwargs):
        return self.get_dated_items()[1]

class DebateIndexView(TitleAdder, ArchiveIndexView, APIArchiveView):
    queryset = Document.debates.all()
    date_field = 'date'
    template_name = "hansards/hansard_archive.html"
    page_title='The Debates of the House of Commons'
index = DebateIndexView.as_view()

class DebateYearArchive(TitleAdder, YearArchiveView, APIArchiveView):
    queryset = Document.debates.all().order_by('date')
    date_field = 'date'
    make_object_list = True
    template_name = "hansards/hansard_archive_year.html"
    page_title = lambda self: 'Debates from %s' % self.get_year()
by_year = DebateYearArchive.as_view()

class DebateMonthArchive(TitleAdder, MonthArchiveView, APIArchiveView):
    queryset = Document.debates.all().order_by('date')
    date_field = 'date'
    make_object_list = True
    month_format = "%m"
    template_name = "hansards/hansard_archive_year.html"
    page_title = lambda self: 'Debates from %s' % self.get_year()
by_month = DebateMonthArchive.as_view()

class HansardAnalysisView(TextAnalysisView):

    def get_corpus_name(self, request, year, **kwargs):
        # Use a special corpus for old debates
        if int(year) < (datetime.date.today().year - 1):
            return 'debates-%s' % year
        return 'debates'

    def get_qs(self, request, **kwargs):
        h = _get_hansard(**kwargs)
        request.hansard = h
        qs = h.statement_set.all()
        # if 'party' in request.GET:
            # qs = qs.filter(member__party__slug=request.GET['party'])
        return qs

    def get_analysis(self, request, **kwargs):
        analysis = super(HansardAnalysisView, self).get_analysis(request, **kwargs)
        word = analysis.top_word
        if word and word != request.hansard.most_frequent_word:
            Document.objects.filter(id=request.hansard.id).update(most_frequent_word=word)
        return analysis

hansard_analysis = HansardAnalysisView.as_view()
########NEW FILE########
__FILENAME__ = billtext
import re
import urllib2

import lxml.html
from lxml.html.clean import clean

from parliament.imports import CannotScrapeException


def get_bill_text_element(bill_or_url):
    """Given a Bill object or URL to a full-text page on parl.gc.ca,
    returns an lxml Element object for the container div of the full
    bill text."""

    if hasattr(bill_or_url, 'get_billtext_url'):
        bill_or_url = bill_or_url.get_billtext_url(single_page=True)

    resp = urllib2.urlopen(bill_or_url)
    root = lxml.html.parse(resp).getroot()

    is_two_columns = not root.cssselect('div.HeaderMenuLinks .HeaderLink a')

    div = root.cssselect('div#publicationContent')[0]

    if is_two_columns:
        # Remove the second column of text (the French text)
        # I haven't made this multilingual since it's highly,
        # highly hacky, and it may well be deleting English text
        # anyway in some instances
        for tr in div.xpath('table/tr'):
            cells = tr.xpath('td')
            if len(cells) in (3, 5, 7):
                cells[2].drop_tree()

    return div


def get_plain_bill_text(bill_or_url):
    content = get_bill_text_element(bill_or_url)
    clean(content)
    text = content.text_content()
    text = re.sub(r'\n[\s\n]+', '\n', text.replace('\t', ' ').replace('\r', '')).strip()
    text = re.sub(r'  +', ' ', text)
    if len(text) < 200:
        raise CannotScrapeException
    return text

########NEW FILE########
__FILENAME__ = ec
"""This is a half-finished module to import Elections Canada
contribution data.

It and parliament.financials were written in summer 2009
and haven't been touched since. Not that they're not worthwhile--they're
just looking for a home, and parents.
"""
import urllib, urllib2
from xml.etree.ElementTree import ElementTree
import re, datetime
import decimal

from BeautifulSoup import BeautifulSoup
from django.db import transaction

from parliament.core import parsetools
from parliament.core.models import *

AGENT_HEADER = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
}

POST_indivcontrib = {
"PrevReturn":0,
"contribclass":	12,
"contribed":	-1,
"contribfiscalfrom":	0,
"contribfiscalto":	0,
"contribname":	'',
"contribpp":	-1,
"contribprov":	-1,
"contribrange":	-1,
"entity":	1,
"filter":	31,
"id":	'',
"ids":	'',
"lang":	'e',
"option":	4,
"page":	1,
"part":	'',
"period":	-1,
"return":	1,
"searchentity":	0,
"sort":	0,
"style":	0,
"table": '',
}
URL_indivcontrib = 'http://www.elections.ca/scripts/webpep/fin2/detail_report.aspx'

def tmp_contribsoup():
    postdata = urllib.urlencode(POST_indivcontrib)
    request = urllib2.Request(URL_indivcontrib, postdata)
    response = urllib2.urlopen(request)
    return BeautifulSoup(response)

    def ec_indivContribRunner(election):

        while (True):
            postdata = urllib.urlencode(POST_indivcontrib)
            request = urllib2.Request(URL_indivcontrib, postdata, AGENT_HEADER)
            print "Requesting page %d... " % POST_indivcontrib['page'],
            response = urllib2.urlopen(request)
            soup = BeautifulSoup(response)
            print "done."
            ec_indivContribPage(soup, election)
            print "Checking for next link... ",
            if soup.find('a', href='javascript:ShowPage(-1);'):
                print "found!"
                POST_indivcontrib['page'] += 1
            else:
                print "not found -- complete!"
                break

    @transaction.commit_on_success
    def ec_indivContribPage(soup, election):
        """ Parses a page of Elections Canada's individual contributions to candidates > $200 list. """

        CONTRIB_URL = 'http://www.elections.ca/scripts/webpep/fin2/contributor.aspx'

        def create_politician(first, last):
            pol = Politician(name_given=first, name_family=last, name="%s %s" % (first, last))
            pol.save()
            return pol

        def get_contributor(href, name):
            """ The Elections Canada page provides postal codes only a separate popup
            window -- so, for each contributor, we have to fetch it."""
            match = re.search(r"contributor.aspx(\?[^']+)'", href)
            if not match:
                raise Exception("Couldn't parse link %s" % href)
            if not name:
                raise Exception("Invalid name %s" % name)
            pname = name.title()
            url = CONTRIB_URL + re.sub(r'&amp;', '&', match.group(1))
            req = urllib2.Request(url, headers=AGENT_HEADER)
            response = urllib2.urlopen(req)
            contribsoup = BeautifulSoup(response)
            (city, province, postcode) = (contribsoup.find('span', id='lblCity').string, contribsoup.find('span', id='lblProvince').string, parsetools.munge_postcode(contribsoup.find('span', id='lblPostalCode').string))
            if postcode:
                try:
                    contrib = Contributor.objects.get(name=pname, postcode=postcode)
                except Contributor.DoesNotExist:
                    pass
                else:
                    return contrib
            contrib = Contributor(name=pname, city=city, postcode=postcode, province=province)
            contrib.save()
            return contrib

        mainTable = soup.find('table', rules='all')
        for row in mainTable.findAll('tr', attrs={'class' : ['odd_row', 'even_row']}):
            cells = row.findAll('td')
            if len(cells) != 7:
                raise Exception('Wrong number of cells in %s' % row)

            # Get the contribution amount 
            amount_mon = parsetools.munge_decimal(cells[5].string)
            amount_non = parsetools.munge_decimal(cells[6].string)
            amount = amount_mon + amount_non
            if amount == 0:
                print "WARNING: Zero amount -- %s and %s" % (cells[5].string, cells[6].string)
                continue

            # Is there a date?
            if len(cells[2].string) > 6:
                try:
                    if cells[2].string.count('.') > 0:
                        date = datetime.datetime.strptime(cells[2].string, '%b. %d, %Y')
                    else:
                        date = datetime.datetime.strptime(cells[2].string, '%b %d, %Y')                    
                except ValueError:
                    print "WARNING: Unparsable date %s" % cells[2].string
                    date = None
            else:
                date = None

            # Who's the contribution to?
            # This is the unfortunately-long part
            recipient = cells[1].string.split(' / ')
            if len(recipient) != 3:
                print "WARNING: Unparsable recipient: %s" % cells[1].string
                continue
            (cname, partyname, ridingname) = recipient

            # First, get the recipient's name
            cname = cname.split(', ')
            if len(cname) != 2:
                print "WARNING: Couldn't parse candidate name %s" % recipient[0]
                continue
            (last, first) = cname

            # Get the recipient's riding
            try:
                riding = Riding.objects.get(name=ridingname)
            except Riding.DoesNotExist:
                print "WARNING: Riding not found: %s" % ridingname
                continue

            # Get the recipient's party    
            try:
                party = Party.objects.get(name=partyname)
            except Party.DoesNotExist:
                print "CREATING party: %s" % partyname
                party = Party(name=partyname)
                party.save()

            # With all this info, we can get a Candidacy object
            try:
                if partyname == 'Independent':
                    # Independent is the only 'party' where two candidates might be running in the same riding & election
                    candidacy = Candidacy.objects.get(riding=riding, party=party, election=election, candidate__name_family=last)
                else:
                    candidacy = Candidacy.objects.get(riding=riding, party=party, election=election)
            except Candidacy.DoesNotExist:
                # No candidacy -- let's create one
                # Let's see if this person already exists
                try:
                    pol = Politician.objects.get(name_given=first, name_family=last)
                except Politician.DoesNotExist:
                    pol = create_politician(first, last)
                except Politician.MultipleObjectsReturned:
                    # ah, similar names
                    # FIXME: after importing this first election, this should search candidacies as well as successful elections
                    possiblepols = Politician.objects.filter(name_given=first, name_family=last, electedmember__party=party)
                    if len(possiblepols) == 1:
                        pol = possiblepols[0]
                    elif len(possiblepols) > 1:
                        # Two people, with the same name, elected from the same party!
                        print "WARNING: Can't disambiguate politician %s" % recipient[0]
                        continue
                    else:
                        # let's create a new one for now
                        pol = create_politician(first, last)

                candidacy = Candidacy(riding=riding, party=party, election=election, candidate=pol)
                candidacy.save()
            else:
                pol = candidacy.candidate
                if pol.name != "%s %s" % (first, last):
                    # FIXME doesn't handle independents properly
                    print "WARNING: Politician names don't match: %s and %s %s" % (pol.name, first, last)

            # Finally, the contributor!
            if cells[0].contents[0].name != 'a':
                print "WARNING: Can't parse contributor"
                continue
            contriblink = cells[0].contents[0]
            try:
                contributor = get_contributor(contriblink['href'], contriblink.string)
            except Exception, e:
                print "WARNING: Error getting contributor: %s" % e
                continue

            # WE HAVE EVERYTHING!!!
            Contribution(contributor=contributor, amount=amount, amount_monetary=amount_mon, amount_nonmonetary=amount_non, date=date, individual_recipient=candidacy).save()
        return True

########NEW FILE########
__FILENAME__ = election
from decimal import Decimal
import re
import urllib2

from BeautifulSoup import BeautifulSoup
from django.db import transaction

from parliament.core import parsetools
from parliament.core.models import Riding, Party, Politician, ElectedMember
from parliament.elections.models import Candidacy

@transaction.commit_on_success
def import_ec_results(election, url="http://enr.elections.ca/DownloadResults.aspx",
    acceptable_types=('validated',)):
    """Import an election from the text format used on enr.elections.ca
    (after the 2011 general election)"""
    
    for line in urllib2.urlopen(url):
        line = line.decode('iso-8859-1').split('\t')
        edid = line[0]
        if not edid.isdigit():
            continue
        result_type = line[3]
        if result_type not in acceptable_types:
            continue
        last_name = line[5]
        first_name = line[7]
        party_name = line[8]
        votetotal = int(line[10])
        votepercent = Decimal(line[11])
        
        riding = Riding.objects.get(edid=edid)
        try:
            party = Party.objects.get_by_name(party_name)
        except Party.DoesNotExist:
            print "No party found for %r" % party_name
            print "Please enter party ID:"
            party = Party.objects.get(pk=raw_input().strip())
            party.add_alternate_name(party_name)
            print repr(party.name)
            
        Candidacy.objects.create_from_name(
            first_name=first_name,
            last_name=last_name,
            party=party,
            riding=riding,
            election=election,
            votetotal=votetotal,
            votepercent=votepercent,
            elected=None
        )

PROVINCES_NORMALIZED = {
    'ab': 'AB',
    'alberta': 'AB',
    'bc': 'BC',
    'b.c.': 'BC',
    'british columbia': 'BC',
    'mb': 'MB',
    'manitoba': 'MB',
    'nb': 'NB',
    'new brunswick': 'NB',
    'nf': 'NL',
    'nl': 'NL',
    'newfoundland': 'NL',
    'newfoundland and labrador': 'NL',
    'nt': 'NT',
    'northwest territories': 'NT',
    'ns': 'NS',
    'nova scotia': 'NS',
    'nu': 'NU',
    'nunavut': 'NU',
    'on': 'ON',
    'ontario': 'ON',
    'pe': 'PE',
    'pei': 'PE',
    'p.e.i.': 'PE',
    'prince edward island': 'PE',
    'pq': 'QC',
    'qc': 'QC',
    'quebec': 'QC',
    'sk': 'SK',
    'saskatchewan': 'SK',
    'yk': 'YT',
    'yt': 'YT',
    'yukon': 'YT',
    'yukon territory': 'YT',
}        

def import_parl_election(url, election, session=None, soup=None): # FIXME session none only for now
    """Import an election from parl.gc.ca results.
    
    Sample URL: http://www2.parl.gc.ca/Sites/LOP/HFER/hfer.asp?Language=E&Search=Bres&ridProvince=0&genElection=0&byElection=2009%2F11%2F09&submit1=Search"""
    
    def _addParty(link):
        match = re.search(r'\?([^"]+)', link)
        if not match: raise Exception("Couldn't parse link in addParty")
        partyurl = 'http://www2.parl.gc.ca/Sites/LOP/HFER/hfer-party.asp?' + match.group(1)
        partypage = urllib2.urlopen(partyurl)
        partypage = re.sub(r'</?font[^>]*>', '', partypage.read()) # strip out font tags
        partysoup = BeautifulSoup(partypage, convertEntities='html')
        partyname = partysoup.find('td', width='85%').string.strip()
        if partyname:
            party = Party(name=partyname)
            party.save()
            return party
        else:
            raise Exception("Couldn't parse party name")
    
    page = urllib2.urlopen(url)
    page = re.sub(re.compile(r'</?font[^>]*>', re.I), '', page.read()) # strip out font tags
    if soup is None: soup = BeautifulSoup(page, convertEntities='html')
    
    # this works for elections but not byelections -- slightly diff format    
    #for row in soup.find('table', width="95%").findAll('tr'):
    
    for row in soup.find(text=re.compile('click on party abbreviation')).findNext('table').findAll('tr'):
      
        if row.find('h5'):
            # It's a province name
            province = row.find('h5').string
            province = PROVINCES_NORMALIZED[province.lower()]
            print "PROVINCE: %s" % province
            
        elif row.find('td', 'pro'):
            # It's a province name -- formatted differently on byelection pages
            provincetmp = row.find('b').string
            try:
                province = PROVINCES_NORMALIZED[provincetmp.lower()]
                print "PROVINCE: %s" % province
            except KeyError:
                # the 'province' class is sometimes used for non-province headings. thanks, parliament!
                print "NOT A PROVINCE: %s" % provincetmp

            
        elif row.find('td', 'rid'):
            # It's a riding name
            a = row.find('a')
            href = a['href']
            ridingname = a.string
            try:
                riding = Riding.objects.get_by_name(ridingname)
            except Riding.DoesNotExist:
                print "WARNING: Could not find riding %s" % ridingname
                riding = Riding(name=ridingname.strip().title(), province=province)
                riding.save()
            else:
                print "RIDING: %s" % riding
        
        elif row.find('td', bgcolor='#00224a'):
            # It's a heading
            pass
        elif row.find('td', align='right'):
            # It's a results row
            cells = row.findAll('td')
            if len(cells) != 6:
                raise Exception("Couldn't parse row: %s" % row)
                
            # Cell 2: party name
            link = cells[1].find('a')
            partylink = link['href']
            partyabbr = link.string
            try:
                party = Party.objects.get_by_name(partyabbr)
            except Party.DoesNotExist:
                party = _addParty(partylink)
                party.add_alternate_name(partyabbr)
                print "WARNING: Could not find party %s" % partyabbr
                
            # Cell 6: elected
            if cells[5].find('img'):
                elected = True
            else:
                elected = False
                
            # Cell 1: candidate name
            link = cells[0].find('a')
            if link:
                parllink = link['href']
                candidatename = link.string
            else:
                candidatename = cells[0].string.strip()
            (last, first) = candidatename.split(', ')
            last = last.strip().title()
            first = first.strip()
            
            # First, assemble a list of possible candidates
            candidate = None
            saveCandidate = False
            candidates = Politician.objects.filter_by_name("%s %s" % (first, last))
            # If there's nothing in the list, try a little harder
            if len(candidates) == 0:
                # Does the candidate have many given names?
                if first.strip().count(' ') >= 1:
                    minifirst = first.strip().split(' ')[0]
                    candidates = Politician.objects.filter_by_name("%s %s" % (minifirst, last))
            # Then, evaluate the possibilities in the list
            for posscand in candidates:
                # You're only a match if you've run for office for the same party in the same province
                match = ElectedMember.objects.filter(riding__province=riding.province, party=party, politician=posscand).count() >= 1 or Candidacy.objects.filter(riding__province=riding.province, party=party, candidate=posscand).count() >= 1
                if match:
                    if candidate is not None:
                        print "WARNING: Could not disambiguate existing candidates %s" % candidatename
                        candidate = None
                        break
                    else:
                        candidate = posscand
            if candidate is None:
                saveCandidate = True
                candidate = Politician(name="%s %s" % (first, last), name_given=first, name_family=last)
            
            # Cell 3: occupation
            occupation = cells[2].string
            
            # Cell 4: votes
            votetotal = parsetools.munge_int(cells[3].string)
            
            # Okay -- now see if this candidacy already exists
            candidacy = None
            if party.name != 'Independent':
                candidacies = Candidacy.objects.filter(election=election, riding=riding, party=party)
                if len(candidacies) > 1:
                    raise Exception("Too many candidacies!")
                elif len(candidacies) == 1:
                    candidacy = candidacies[0]
                    if candidate != candidacy.candidate:
                        print "WARNING: Forced riding/party match for candidate %s: %s" % (candidatename, candidacy.candidate)
                        candidate = candidacy.candidate
            if candidacy is None:
                candidacies = Candidacy.objects.filter(candidate=candidate, election=election)
                if len(candidacies) > 1:
                    raise Exception("Two candidacies for one candidate!")
                elif len(candidacies) == 1:
                    candidacy = candidacies[0]
                    if candidacy.riding != riding or candidacy.party != party:
                        print "WARNING: Invalid riding/party match for %s - %s (%s), %s (%s)" % (candidacy, riding, candidacy.riding == riding, party, candidacy.party == party)
                        continue
                else:
                    if saveCandidate: candidate.save()
                    candidacy = Candidacy(candidate=candidate, election=election, riding=riding, party=party)
            candidacy.occupation = unicode(occupation)
            candidacy.votetotal = votetotal
            candidacy.elected = elected
            candidacy.save()
            #print "%s (%s), a %s, got %d votes (elected: %s)" % (candidatename, partyabbr, occupation, votecount, elected)
    election.calculate_vote_percentages()
    

########NEW FILE########
__FILENAME__ = common
# coding: utf8
"""This module parses the Hansards of the House from HTML

There are two parsers, for two different HTML formats (1994-2006, 2006-).

However, XML is now available for the 2006-present documents, and
the (better) parser for that is in parl_document.py and the
alpheus module.

In other words, this module is historical and unmaintained. Interfaces
with the outside world are probably broken.

This module is organized like so:
__init__.py - utility functions, simple parse interface
common.py - infrastructure used in the parsers, i.e. regexes
current.py - parser for the Hansard format used from 2006 to the present
old.py - (fairly crufty) parser for the format used from 1994 to 2006

"""
import re, urllib, urllib2, datetime, sys, codecs

from BeautifulSoup import BeautifulSoup, Comment, NavigableString
from django.db.models import Q
from django.db import transaction
from django.utils.html import escape
from django.conf import settings

from parliament.core.models import *
from parliament.hansards.models import Statement
from parliament.hansards.models import Document as Hansard
from parliament.bills.models import Bill
from parliament.core import parsetools
from parliament.core.parsetools import r_politicalpost, r_honorific, r_notamember

ENABLE_READLINE = False
ENABLE_PRINT = False
GET_PARLID_ONLINE = True
VERBOSE = False
SAVE_GENDER = True

## REGEXES
r_time_paren = re.compile(r'^\s*D?\s*\(\s*(\d\d)(\d\d)\s*\)\s*$', re.UNICODE)
r_time_noparen = re.compile(r'^\s*(\d\d)(\d\d)\s*$', re.UNICODE)
r_time_optionalparen = re.compile(r'\s*\(?\s*(\d\d)(\d\d)\s*\)?\s*$', re.UNICODE)
r_time_glyph = re.compile(r'arobas\.gif')
r_arrow_img = re.compile(r'arrow\d+\.gif')
r_housemet = re.compile(r'The\s+House\s+met\s+at\s+(\d[\d:\.]*)\s+([ap]\.m\.)', re.I | re.UNICODE)
r_proceedings = re.compile(r'^\s*The\s+House\s+(resumed|proceeded)', re.UNICODE)

r_letter = re.compile(r'\w')
r_notspace = re.compile(r'\S', re.UNICODE)
r_timeanchor = re.compile(r'^T\d\d\d\d$')
r_division = re.compile(r'^\s*\(?\s*Division\s+No\.\s+\d+\s*\)\s*$', re.I | re.UNICODE)
r_letterbutnotD = re.compile(r'[a-zA-CE-S]')

STARTUP_RE = (
    (re.compile(r'Peri</b>\s*G\s*<b>', re.I), 'Peric '),  # hardcoded just for you, Janko. mwah.
    (re.compile(r'<b>—</b>', re.I), '—'),
)
STARTUP_RE_1994 = (
    # Deal with self-closing <a name> tags
    (re.compile(r'<a name="[^"]+" />'), ''),# we're just getting rid of them, since we don't care about them
    # And empty bold tags
    (re.compile(r'</?b>(\s*)</?b>', re.I | re.UNICODE), r'\1'), 
    # Another RE for empty bolds
    (re.compile(r'<b>[^\w\d<]+</b>', re.I | re.UNICODE), ' '),
    # And line breaks or <hr>
    (re.compile(r'</?[bh]r[^>]*>', re.I), ''),
    # And [<i>text</i>]
    (re.compile(r'\[<i>[^<>]+</i>\]', re.I), ''),
    (re.compile(r'Canadian Alliance, PC/DR'), 'Canadian Alliance / PC/DR'),
    (re.compile(r'Mr\. Antoine Dubé Lévis'), 'Mr. Antoine Dubé (Lévis'), # antoine comes up often
    (re.compile(r'Hon\. David Anderson:'), 'Hon. David Anderson (Victoria):'),
    (re.compile(r'<b>>', re.I), '<b>'),
    (re.compile(r'<>'), ''),
)
STARTUP_RE_2009 = (
    (re.compile(r'<b>\s*<A class="WebOption" onclick="GetWebOptions\(\'PRISM\',\'Affiliation\'[^>]+></a>\s*</b>', re.I | re.UNICODE), '<b><a class="deleteMe"></a></b>'), # empty speaker links -- will be further dealt with once we have a parse tree
    (re.compile(r'&nbsp;'), ' '),
    (re.compile(r'<div>\s*<b>\s*</b>\s*</div>', re.I | re.UNICODE), ' '), # <div><b></b></div>
    # Another RE for empty bolds
    (re.compile(r'<b>[^\w\d<]*</b>', re.I | re.UNICODE), ''),    
)




class ParseTracker(object):
    def __init__(self):
        self._current = dict()
        self._next = dict()
        self._textbuffer = []
        self._ignoretext = False
        
    def __setitem__(self, key, val):
        self._current[key] = val
    
    def setNext(self, key, val):
        self._next[key] = val
        
    def __getitem__(self, key):
        try:
            return self._current[key]
        except KeyError:
            return None
    
    def hasText(self):
        return len(self._textbuffer) >= 1
        
    def ignoreText(self, ignore=True):
        self._ignoretext = ignore
        
    def ignoringText(self):
        return self._ignoretext
         
    def addText(self, text, blockquote=False):
        if not self._ignoretext:
            t = parsetools.tameWhitespace(text.strip())
            t = parsetools.sane_quotes(t)
            if t.startswith(':'):
                # Strip initial colon
                t = t[1:].strip()
            if t.startswith('He said: '):
                t = t[8:].strip()
            if t.startswith('She said: '):
                t = t[9:].strip()
            if len(t) > 0 and not t.isspace():
                #if t[0].islower() and not t.startswith('moved'):
                #    print "WARNING: Block of text begins with lowercase letter: %s" % t
                if blockquote or (t.startswith('moved ') and not self.hasText()):
                    self._textbuffer.append(u'> ' + t)
                else:
                    self._textbuffer.append(t)
                    
    def appendToText(self, text, italic=False):
        if self.hasText() and not self._ignoretext:
            t = parsetools.tameWhitespace(text.strip())
            if len(t) > 0 and not t.isspace():
                if italic: t = u' <em>' + t + u'</em> '
                self._textbuffer[-1] += t
        
    def getText(self):
        return u"\n\n".join(self._textbuffer)
        
    def onward(self):
        self._textbuffer = []
        self._current = self._next.copy()
        self._ignoretext = False
        
class ParseException(Exception):
    pass

class HansardParser(object):
    """Base class for Hansard parsers"""
    def __init__(self, hansard, html):
        super(HansardParser, self).__init__()
        self.hansard = hansard
        for regex in STARTUP_RE:
            html = re.sub(regex[0], regex[1], html)

        self.soup = BeautifulSoup(html, convertEntities='html')
        
        # remove comments
        for t in self.soup.findAll(text=lambda x: isinstance(x, Comment)):
            t.extract()
        
    def parse(self):
        self.statements = []
        self.statement_index = 0
        
    def houseTime(self, number, ampm):
        ampm = ampm.replace('.', '')
        number = number.replace('.', ':')
        match = re.search(r'(\d+):(\d+)', number)
        if match:
            # "2:30 p.m."
            return datetime.datetime.strptime("%s:%s %s" % (match.group(1), match.group(2), ampm), "%I:%M %p").time()
        else:
            # "2 p.m."
            return datetime.datetime.strptime("%s %s" % (number, ampm), "%I %p").time()
            
    def saveProceedingsStatement(self, text, t):
        text = parsetools.sane_quotes(parsetools.tameWhitespace(text.strip()))
        if len(text):
            timestamp = t['timestamp']
            if not isinstance(timestamp, datetime.datetime):
                # The older parser provides only datetime.time objects
                timestamp = datetime.datetime.combine(self.date, timestamp)
            statement = Statement(hansard=self.hansard,
                time=timestamp,
                text=text, sequence=self.statement_index,
                who='Proceedings')
            self.statement_index += 1
            self.statements.append(statement)
        
    def saveStatement(self, t):
        def mcUp(match):
            return 'Mc' + match.group(1).upper()
        if t['topic']:
            # Question No. 139-- -> Question No. 139
            t['topic'] = re.sub(r'\-+$', '', t['topic'])
            t['topic'] = re.sub(r"'S", "'s", t['topic'])
            t['topic'] = re.sub(r'Mc([a-z])', mcUp, t['topic'])
        if t.hasText():
            if not t['member_title']:
                t['member_title'] = 'Proceedings'
                print "WARNING: No title for %s" % t.getText().encode('ascii', 'replace')
            timestamp = t['timestamp']
            if not isinstance(timestamp, datetime.datetime):
                # The older parser provides only datetime.time objects
                timestamp = datetime.datetime.combine(self.date, timestamp)
            statement = Statement(hansard=self.hansard, heading=t['heading'], topic=t['topic'],
             time=timestamp, member=t['member'],
             politician=t['politician'], who=t['member_title'],
             text=t.getText(), sequence=self.statement_index, written_question=bool(t['written_question']))
            if r_notamember.search(t['member_title'])\
              and ('Speaker' in t['member_title'] or 'The Chair' in t['member_title']):
                statement.speaker = True
            self.statement_index += 1
            self.statements.append(statement)
            
            if ENABLE_PRINT:
                print u"HEADING: %s" % t['heading']
                print u"TOPIC: %s" % t['topic']
                print u"MEMBER TITLE: %s" % t['member_title']
                print u"MEMBER: %s" % t['member']
                print u"TIME: %s" % t['timestamp']
                print u"TEXT: %s" % t.getText()
            if ENABLE_READLINE:
                sys.stdin.readline()
        t.onward()
########NEW FILE########
__FILENAME__ = current
"""This *was* the parser for the current HTML format on parl.gc.ca.

But now we have XML. See parl_document.py.

This module is organized like so:
__init__.py - utility functions, simple parse interface
common.py - infrastructure used in the parsers, i.e. regexes
current.py - parser for the Hansard format used from 2006 to the present
old.py - (fairly crufty) parser for the format used from 1994 to 2006

"""
from parliament.imports.hans_old.common import *

import logging
logger = logging.getLogger(__name__)

class HansardParser2009(HansardParser):
    
    def __init__(self, hansard, html):
        
        for regex in STARTUP_RE_2009:
            html = re.sub(regex[0], regex[1], html)

        super(HansardParser2009, self).__init__(hansard, html)
        
        for x in self.soup.findAll('a', 'deleteMe'):
            x.findParent('div').extract()
            
    def process_related_link(self, tag, string, current_politician=None):
        #print "PROCESSING RELATED for %s" % string
        resid = re.search(r'ResourceID=(\d+)', tag['href'])
        restype = re.search(r'ResourceType=(Document|Affiliation)', tag['href'])
        if not resid and restype:
            return string
        resid, restype = int(resid.group(1)), restype.group(1)
        if restype == 'Document':
            try:
                bill = Bill.objects.get_by_legisinfo_id(resid)
            except Bill.DoesNotExist:
                match = re.search(r'\b[CS]\-\d+[A-E]?\b', string)
                if not match:
                    logger.error("Invalid bill link %s" % string)
                    return string
                bill = Bill.objects.create_temporary_bill(legisinfo_id=resid,
                    number=match.group(0), session=self.hansard.session)
            except Exception, e:
                print "Related bill search failed for callback %s" % resid
                print repr(e)
                return string
            return u'<bill id="%d" name="%s">%s</bill>' % (bill.id, escape(bill.name), string)
        elif restype == 'Affiliation':
            try:
                pol = Politician.objects.getByParlID(resid)
            except Politician.DoesNotExist:
                print "Related politician search failed for callback %s" % resid
                if getattr(settings, 'PARLIAMENT_LABEL_FAILED_CALLBACK', False):
                    # FIXME migrate away from internalxref?
                    InternalXref.objects.get_or_create(schema='pol_parlid', int_value=resid, target_id=-1)
                return string
            if pol == current_politician:
                return string # When someone mentions her riding, don't link back to her
            return u'<pol id="%d" name="%s">%s</pol>' % (pol.id, escape(pol.name), string)
    
    def get_text(self, cursor):
        text = u''
        for string in cursor.findAll(text=parsetools.r_hasText):
            if string.parent.name == 'a' and string.parent['class'] == 'WebOption':
                text += self.process_related_link(string.parent, string, self.t['politician'])
            else:
                text += unicode(string)
        return text
        
    def parse(self):
        
        super(HansardParser2009, self).parse()
        
        # Initialize variables
        t = ParseTracker()
        self.t = t
        member_refs = {}
        
        
        # Get the date
        c = self.soup.find(text='OFFICIAL REPORT (HANSARD)').findNext('h2')
        self.date = datetime.datetime.strptime(c.string.strip(), "%A, %B %d, %Y").date()
        self.hansard.date = self.date
        self.hansard.save()
        
        c = c.findNext(text=r_housemet)
        match = re.search(r_housemet, c.string)
        t['timestamp'] = self.houseTime(match.group(1), match.group(2))
        t.setNext('timestamp', t['timestamp'])
        
        # Move the pointer to the start
        c = c.next
    
        # And start the big loop
        while c is not None:
        
            # It's a string
            if not hasattr(c, 'name'):
                pass
            # Heading
            elif c.name == 'h2':
                c = c.next
                if not parsetools.isString(c): raise ParseException("Expecting string right after h2")
                t.setNext('heading', parsetools.titleIfNecessary(parsetools.tameWhitespace(c.string.strip())))
            
            # Topic
            elif c.name == 'h3':
                top = c.find(text=r_letter)
                #if not parsetools.isString(c):
                    # check if it's an empty header
                #    if c.parent.find(text=r_letter):
                #        raise ParseException("Expecting string right after h3")
                if top is not None:
                    c = top
                    t['topic_set'] = True
                    t.setNext('topic', parsetools.titleIfNecessary(parsetools.tameWhitespace(c.string.strip())))
            
            elif c.name == 'h4':
                if c.string == 'APPENDIX':
                    self.saveStatement(t)
                    print "Appendix reached -- we're done!"
                    break
            # Timestamp
            elif c.name == 'a' and c.has_key('name') and c['name'].startswith('T'):
                match = re.search(r'^T(\d\d)(\d\d)$', c['name'])
                if match:
                    t.setNext('timestamp', parsetools.time_to_datetime(
                        hour=int(match.group(1)),
                        minute=int(match.group(2)),
                        date=self.date))
                else:
                    raise ParseException("Couldn't match time %s" % c.attrs['name'])
                
            elif c.name == 'b' and c.string:
                # Something to do with written answers
                match = r_honorific.search(c.string)
                if match:
                    # It's a politician asking or answering a question
                    # We don't get a proper link here, so this has to be a name match
                    polname = re.sub(r'\(.+\)', '', match.group(2)).strip()
                    self.saveStatement(t)
                    t['member_title'] = c.string.strip()
                    t['written_question'] = True
                    try:
                        pol = Politician.objects.get_by_name(polname, session=self.hansard.session)
                        t['politician'] = pol
                        t['member'] = ElectedMember.objects.get_by_pol(politician=pol, date=self.date)
                    except Politician.DoesNotExist:
                        print "WARNING: No name match for %s" % polname
                    except Politician.MultipleObjectsReturned:
                        print "WARNING: Multiple pols for %s" % polname
                else:
                    if not c.string.startswith('Question'):
                        print "WARNING: Unexplained boldness: %s" % c.string
                
            # div -- the biggie
            elif c.name == 'div':
                origdiv = c
                if c.find('b'):
                    # We think it's a new speaker
                    # Save the current buffer
                    self.saveStatement(t)
                
                    c = c.find('b')
                    if c.find('a'):
                        # There's a link...
                        c = c.find('a')
                        match = re.search(r'ResourceType=Affiliation&ResourceID=(\d+)', c['href'])
                        if match and c.find(text=r_letter):
                            parlwebid = int(match.group(1))
                            # We have the parl ID. First, see if we already know this ID.
                            pol = Politician.objects.getByParlID(parlwebid, lookOnline=False)
                            if pol is None:
                                # We don't. Try to do a quick name match first (if flags say so)
                                if not GET_PARLID_ONLINE:
                                    who = c.next.string
                                    match = re.search(r_honorific, who)
                                    if match:
                                        polname = re.sub(r'\(.+\)', '', match.group(2)).strip()
                                        try:
                                            #print "Looking for %s..." % polname,
                                            pol = Politician.objects.get_by_name(polname, session=self.hansard.session)
                                            #print "found."
                                        except Politician.DoesNotExist:
                                            pass
                                        except Politician.MultipleObjectsReturned:
                                            pass
                                if pol is None:
                                    # Still no match. Go online...
                                    try:
                                        pol = Politician.objects.getByParlID(parlwebid, session=self.hansard.session)
                                    except Politician.DoesNotExist:
                                        print "WARNING: Couldn't find politician for ID %d" % parlwebid
                            if pol is not None:
                                t['member'] = ElectedMember.objects.get_by_pol(politician=pol, date=self.date)
                                t['politician'] = pol
                    c = c.next
                    if not parsetools.isString(c): raise Exception("Expecting string in b for member name")
                    t['member_title'] = c.strip()
                    #print c
                    if t['member_title'].endswith(':'): # Remove colon in e.g. Some hon. members:
                        t['member_title'] = t['member_title'][:-1]
                    
                    # Sometimes we don't get a link for short statements -- see if we can identify by backreference
                    if t['member']:
                        member_refs[t['member_title']] = t['member']
                        # Also save a backref w/o position/riding
                        member_refs[re.sub(r'\s*\(.+\)\s*', '', t['member_title'])] = t['member']
                    elif t['member_title'] in member_refs:
                        t['member'] = member_refs[t['member_title']]
                        t['politician'] = t['member'].politician
                    
                    c.findParent('b').extract() # We've got the title, now get the rest of the paragraph
                    c = origdiv
                    t.addText(self.get_text(c))
                else:
                    # There should be text in here
                    if c.find('div'):
                        if c.find('div', 'Footer'):
                            # We're done!
                            self.saveStatement(t)
                            print "Footer div reached -- done!"
                            break
                        raise Exception("I wasn't expecting another div in here")
                    txt = self.get_text(c).strip()
                    if r_proceedings.search(txt):
                        self.saveStatement(t)
                        self.saveProceedingsStatement(txt, t)
                    else:
                        t.addText(txt, blockquote=bool(c.find('small')))
            else:
                #print c.name
                if c.name == 'b':
                    print "B: ",
                    print c
                #if c.name == 'p':
                #    print "P: ",
                #    print c
                
            c = c.next
        return self.statements

########NEW FILE########
__FILENAME__ = old
"""This module parses the Hansards of the House from HTML

There are two parsers, for two different HTML formats (1994-2006, 2006-).

However, XML is now available for the 2006-present documents, and
the (better) parser for that is in parl_document.py and the
alpheus module.

In other words, this module is historical and unmaintained. Interfaces
with the outside world are probably broken.

This module is organized like so:
__init__.py - utility functions, simple parse interface
common.py - infrastructure used in the parsers, i.e. regexes
current.py - parser for the Hansard format used from 2006 to the present
old.py - (fairly crufty) parser for the format used from 1994 to 2006

"""
from parliament.imports.hans_old.common import *

r_bill = re.compile(r'[bB]ill C-(\d+)')
class HansardParser1994(HansardParser):
    
    def __init__(self, hansard, html):
        
        for regex in STARTUP_RE_1994:
            html = re.sub(regex[0], regex[1], html)

        super(HansardParser1994, self).__init__(hansard, html)
        
    def replace_bill_link(self, billmatch):
        billnumber = int(billmatch.group(1))
        try:
            bill = Bill.objects.get(sessions=self.hansard.session, number_only=billnumber)
        except Bill.DoesNotExist:
            #print "NO BILL FOUND for %s" % billmatch.group(0)
            return billmatch.group(0)
        result = u'<bill id="%d" name="%s">%s</bill>' % (bill.id, escape(bill.name), "Bill C-%s" % billnumber)
        #print "REPLACING %s with %s" % (billmatch.group(0), result)
        return result
    
    def label_bill_links(self, txt):
        return r_bill.sub(self.replace_bill_link, txt)
    
    def parse(self):
        
        super(HansardParser1994, self).parse()

        # Initialize variables
        t = ParseTracker()
        members = []
        session = self.hansard.session
                
        # Get the date
        try:
            #c = self.soup.find('h1', align=re.compile(r'CENTER', re.I)).findNext(text='HOUSE OF COMMONS').findNext(('b', 'h4'))
            c = self.soup.find('h1').findNext(text=lambda x: x.string == 'HOUSE OF COMMONS' and x.parent.name == 'h1').findNext(('b', 'h4'))
        except AttributeError:
            # alternate page style
            c = self.soup.find('td', height=85).findNext(text=re.compile(r'^\s*OFFICIAL\s+REPORT\s+\(HANSARD\)\s*$')).findNext('h2', align='center')
        if c.string is None:
            raise ParseException("Couldn't navigate to date. %s" % c)
        self.date = datetime.datetime.strptime(c.string.strip(), "%A, %B %d, %Y").date()
        self.hansard.date = self.date
        self.hansard.save()  

        # And the time
        c = c.findNext(text=r_housemet)
        match = re.search(r_housemet, c.string)
        t['timestamp'] = self.houseTime(match.group(1), match.group(2))
        t.setNext('timestamp', t['timestamp'])
        
        # Move the pointer to the start
        c = c.next
    
        # And start the big loop
        while c is not None:

            if parsetools.isString(c):
                # It's a string
                if re.search(r_letter, c):
                    # And it contains words!
                    if r_proceedings.search(c):
                        # It's a "The House resumed" statement
                        self.saveStatement(t)
                        self.saveProceedingsStatement(c, t)
                    else:
                        # Add it to the buffer
                        txt = self.label_bill_links(c)
                        t.addText(txt, blockquote=bool(c.parent.name=='blockquote'
                                            or c.parent.name=='small'
                                            or c.parent.name=='ul'
                                            or c.parent.parent.name=='ul'
                                            or c.parent.parent.name=='blockquote'))
            
            elif c.name == 'h2' and c.has_key('align') and c['align'].lower() == 'center':
                # Heading
                c = c.findNext(text=r_letter)
                
                #c = c.next
                #if not parsetools.isString(c): raise ParseException("Expecting string right after h2")
                t.setNext('heading', parsetools.titleIfNecessary(parsetools.tameWhitespace(c.string.strip())))
            
            elif (c.name == 'h3' and c.has_key('align') and c['align'].lower() == 'center') or (c.name == 'center' and (c.find('h3') or c.find('b'))):
                # Topic
                if c.find(text=r_letter):
                    c = c.find(text=r_letter)
                    if 'Division No.' in c.string:
                        # It's a vote
                        # Set a flag to ignore text till the next speaker
                        t.ignoreText(True)
                    t.setNext('topic', parsetools.titleIfNecessary(parsetools.tameWhitespace(c.string.strip())))
            elif c.name == 'h4':
                # Either asterisks or a vote (hopefully)
                if c.string is not None and 'Division' in c.string:
                    # It's a vote
                    # Set a flag to ignore text till the next speaker
                    t.ignoreText(True)
                if c.string == 'APPENDIX':
                    self.saveStatement(t)
                    break
                c = c.nextSibling.previous
            elif c.name == 'i':
                # Italics -- let's make sure it's inline formatting
                if t.hasText() and c.string is not None and parsetools.isString(c.next.next) and re.search(r_notspace, c.next.next):
                    t.appendToText(c.string, italic=True)
                    c = c.next.next
                    t.appendToText(c.string)
            elif c.name == 'h5' or c.name == 'center' or (c.name == 'p' and c.has_key('align') and c['align'] == 'center'):
                # A heading we don't care about (hopefully!)
                if c.nextSibling is not None:
                    c = c.nextSibling.previous
                else: 
                    c = c.next
            elif c.name == 'table':
                # We don't want tables, right?
                if c.find(text=r_division):
                    # It's a vote
                    t.ignoreText(True)
                if not c.find('small'):
                    if not t.ignoringText():
                        # It's not a vote, so print a debug message to make sure we're not discarding important stuff
                        if VERBOSE: print "WARNING: Extracting table %s" % c
                    if c.nextSibling:
                        c = c.nextSibling.previous
                    else:
                        c = c.next
            elif c.name == 'div':
                if c.has_key('class') and c['class'] == 'Footer':
                    # We're done!
                    self.saveStatement(t)
                    break
            elif (c.name == 'a' and ( c.find('img', src=r_time_glyph) or (c.has_key('name') and re.search(r_timeanchor, c['name'])) )) or (c.name == 'li' and parsetools.isString(c.next) and re.search(r_time_paren, c.next)) or (c.name == 'p' and c.find(text=r_time_paren) and not c.find(text=r_letterbutnotD)):
                # Various kinds of timestamps
                if c.name == 'a':
                    c = c.findNext(text=r_notspace)
                else:
                    c = c.find(text=r_time_optionalparen)
                match = re.search(r_time_optionalparen, c.string)
                if not match: raise ParseException("Couldn't match time in %s\n%s" (c, c.parent))
                t.setNext('timestamp', parsetools.time(hour=int(match.group(1)), minute=int(match.group(2))))
            elif c.name == 'a' and c.has_key('class') and c['class'] == 'toc':
                # TOC link
                c = c.next
            elif c.name == 'b':
                if c.find('a'):
                    # 1. It's a page number -- ignore
                    c = c.find('a').next
                elif c.string is not None and re.search(r_time_paren, c.string):
                    # 2. It's a timestamp
                    match = re.search(r_time_paren, c.string)
                    t.setNext('timestamp', parsetools.time(hour=int(match.group(1)), minute=int(match.group(2))))
                    c = c.next
                elif c.string is not None and re.search(r_honorific, c.string.strip()):
                    # 3. It's the name of a new speaker
                    # Save the current buffer
                    self.saveStatement(t)
                    
                    # And start wrangling. First, get the colon out
                    member = None
                    t['member_title'] = parsetools.tameWhitespace(c.string.strip())
                    if t['member_title'].endswith(':'):
                        t['member_title'] = t['member_title'][:-1]
                    # Then, get the honorific out
                    match = re.search(r_honorific, t['member_title'])
                    (honorific, who) = (match.group(1), match.group(2))
                    if re.search(r_notamember, honorific):
                        # It's the speaker or someone unidentified. Don't bother matching to a member ID.
                        pass
                    else:
                        partyname = None
                        if 'Mr.' in honorific:
                            gender = 'M'
                        elif 'Mrs.' in honorific or 'Ms.' in honorific or 'Miss' in honorific:
                            gender = 'F'
                        else:
                            gender = None
                        if '(' in who:
                            # We have a post or riding
                            match = re.search(r'^(.+?) \((.+)\)', who)
                            if not match:
                                raise ParseException("Couldn't parse title %s" % who)
                            (name, paren) = (match.group(1).strip(), match.group(2).strip())
                            if paren == 'None':
                                # Manually labelled to not match
                                t['member_title'].replace(' (None)', '')
                                c = c.next.next
                                continue
                            # See if there's a party name; if so, strip it out
                            match = re.search(r'^(.+), (.+)$', paren)
                            if match:
                                (paren, partyname) = (match.group(1).strip(), match.group(2))
                            if re.search(r_politicalpost, paren):
                                # It's a post, not a riding
                                riding = None
                            else:
                                try:
                                    riding = Riding.objects.get_by_name(paren)
                                except Riding.DoesNotExist:
                                    raise ParseException("WARNING: Could not find riding %s" % paren)
                                    riding = None
                        else:
                            name = who.strip()
                            riding = None
                        if ' ' not in name or (riding is None and '(' not in who):
                            # We think it's a backreference, because either
                            # (a) there's only a last name
                            # (b) there's no riding AND no title was provided
                            # Go through the list of recent speakers and try to match
                            for possible in members:
                                if name in possible['name']:
                                    #print "Backreference successful: %s %s %s" % (possible['name'], name, possible['member'])
                                    # A match!
                                    member = possible['member']
                                    # Probably. If we have a riding, let's double-check
                                    if riding is not None and riding != possible['riding']:
                                        if VERBOSE: print "WARNING: Name backref matched (%s, %s) but not riding (%s, %s)" % (name, possible['name'], riding, possible['riding'])
                                        member = None
                                    # Also double-check on gender
                                    elif gender is not None and possible['gender'] is not None and gender != possible['gender']:
                                        member = None
                                    else:
                                        break
                            if member is None:
                                # Last-ditch: try a match by name...
                                try:
                                    pol = Politician.objects.get_by_name(name, session=session)
                                    member = ElectedMember.objects.get_by_pol(politician=pol, date=self.date)
                                except (Politician.DoesNotExist, Politician.MultipleObjectsReturned):
                                    # and, finally, just by last name
                                    poss = ElectedMember.objects.filter(sessions=session, politician__name_family__iexact=name)
                                    if riding:
                                        poss = poss.filter(riding=riding)
                                    if gender:
                                        poss = poss.filter(Q(politician__gender=gender) | Q(politician__gender=''))
                                    if len(poss) == 1:
                                        member = poss[0]
                                        if VERBOSE: print "WARNING: Last-name-only match for %s -- %s" % (name, member)
                                    else:
                                        raise ParseException( "WARNING: Backreference match failed for %s (%s)" % (name, t['member_title']) )
                        else:
                            # Try to do a straight match
                            try:
                                if riding is not None:
                                    pol = Politician.objects.get_by_name(name, riding=riding, session=session)
                                else:
                                    pol = Politician.objects.get_by_name(name, session=session)
                            except Politician.DoesNotExist:
                                pol = None
                                if riding is not None:
                                    # In case we're dealing with a renamed riding, try matching without the riding
                                    try:
                                        pol = Politician.objects.get_by_name(name, session=session)
                                    except Politician.DoesNotExist:
                                        # We'll raise the exception later
                                        pass
                                    else:
                                        if VERBOSE: print "WARNING: Forced match without riding for %s: %s" % (t['member_title'], pol)
                                if pol is None:
                                    raise ParseException("Couldn't match speaker: %s (%s)\nriding: %s" % (name, t['member_title'], riding))
                            except Politician.MultipleObjectsReturned:
                                # Our name match can't disambiguate properly.
                                if partyname:
                                    # See if we can go by party
                                    try:
                                        party = Party.objects.get_by_name(partyname)
                                        pol = Politician.objects.get_by_name(name, session=session, party=party)
                                    except Party.DoesNotExist:
                                        pass # we'll produce our own exception in a moment
                                if pol is None:
                                    raise ParseException("Couldn't disambiguate politician: %s" % name)
                            member = ElectedMember.objects.get_by_pol(politician=pol, date=self.date)
                            if riding is not None: riding = member.riding
                            # Save in the list for backreferences
                            members.insert(0, {'name':name, 'member':member, 'riding':riding, 'gender':gender})
                            # Save the gender if appropriate
                            if gender and pol.gender != gender and SAVE_GENDER:
                                if pol.gender != '':
                                    raise ParseException("Gender conflict! We say %s, database says %s for %s (pol: %s)." % (gender, pol.gender, t['member_title'], pol))
                                if VERBOSE: print "Saving gender (%s) for %s" % (gender, t['member_title'])
                                pol.gender = gender
                                pol.save()
                            
                        # Okay! We finally have our member!
                        t['member'] = member
                        t['politician'] = member.politician
                    c = c.next
                elif c.string is None and len(c.contents) == 0:
                    # an empty bold tag!
                    pass
                elif c.string == 'APPENDIX':
                    # We don't want the appendix -- finish up
                    self.saveStatement(t)
                    break
                elif hasattr(c.string, 'count') and 'Government House' in c.string:
                    # quoted letter, discard
                    c = c.next
                else:
                    raise ParseException("Unexplained boldness! %s\n**\n%s" % (c, c.parent))
            
            # Okay, so after that detour we're back at the indent level of the main for loop
            # We're also done with the possible tags we care about, so advance the cursor and loop back...
            c = c.next
        return self.statements
########NEW FILE########
__FILENAME__ = legisinfo
import datetime
import urllib2

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from lxml import etree

from parliament.bills.models import Bill, BillInSession, BillText, BillEvent
from parliament.committees.models import Committee, CommitteeMeeting
from parliament.core.models import Session, Politician, ElectedMember
from parliament.hansards.models import Document
from parliament.imports import CannotScrapeException
from parliament.imports.billtext import get_plain_bill_text

import logging
logger = logging.getLogger(__name__)

LEGISINFO_XML_LIST_URL = 'http://parl.gc.ca/LegisInfo/Home.aspx?language=E&ParliamentSession=%(sessid)s&Page=%(page)s&Mode=1&download=xml'
LEGISINFO_SINGLE_BILL_URL = 'http://www.parl.gc.ca/LegisInfo/BillDetails.aspx?Language=E&Mode=1&billId=%(legisinfo_id)s&download=xml'

def _parse_date(d):
    return datetime.date(*[int(x) for x in d[:10].split('-')])

def _get_previous_session(session):
    try:
        return Session.objects.filter(start__lt=session.start)\
            .order_by('-start')[0]
    except IndexError:
        return None

@transaction.commit_on_success
def import_bills(session):
    """Import bill data from LegisInfo for the given session.
    
    session should be a Session object"""
    
    previous_session = _get_previous_session(session)
        
    page = 0
    fetch_next_page = True
    while fetch_next_page:
        page += 1
        url = LEGISINFO_XML_LIST_URL % {
            'sessid': session.id,
            'page': page
        }
        tree = etree.parse(urllib2.urlopen(url))
        bills = tree.xpath('//Bill')
        if len(bills) < 500:
            # As far as I can tell, there's no indication within the XML file of
            # whether it's a partial or complete list, but it looks like the 
            # limit for one file/page is 500.
            fetch_next_page = False

        for lbill in bills:
            try:
                _import_bill(lbill, session, previous_session)
            except urllib2.HTTPError as e:
                logger.error("%s %s" % (e, getattr(e, 'url', '(no url)')))

    return True

def import_bill_by_id(legisinfo_id):
    """Imports a single bill based on its LEGISinfo id."""
    
    url = LEGISINFO_SINGLE_BILL_URL % {'legisinfo_id': legisinfo_id}
    try:
        tree = etree.parse(urllib2.urlopen(url))
    except urllib2.HTTPError:
        raise Bill.DoesNotExist("HTTP error retrieving bill")
    bill = tree.xpath('/Bill')
    assert len(bill) == 1
    bill = bill[0]

    sessiontag = bill.xpath('ParliamentSession')[0]
    session = Session.objects.get(parliamentnum=int(sessiontag.get('parliamentNumber')),
        sessnum=int(sessiontag.get('sessionNumber')))
    return _import_bill(bill, session)

def _update(obj, field, value):
    if value is None:
        return
    if not isinstance(value, datetime.date):
        value = unicode(value)
    if getattr(obj, field) != value:
        setattr(obj, field, value)
        obj._changed = True

def _import_bill(lbill, session, previous_session=None):
    #lbill should be an ElementTree Element for the Bill tag

    if previous_session is None:
        previous_session = _get_previous_session(session)

    lbillnumber = lbill.xpath('BillNumber')[0]
    billnumber = (lbillnumber.get('prefix') + '-' + lbillnumber.get('number')
        + lbillnumber.get('suffix', ''))
    try:
        bill = Bill.objects.get(number=billnumber, sessions=session)
        bis = bill.billinsession_set.get(session=session)
    except Bill.DoesNotExist:
        bill = Bill(number=billnumber)
        bis = BillInSession(bill=bill, session=session)
        bill._changed = True
        bis._changed = True
        bill.set_temporary_session(session)

    _update(bill, 'name_en', lbill.xpath('BillTitle/Title[@language="en"]')[0].text)

    if not bill.status_code:
        # This is presumably our first import of the bill; check if this
        # looks like a reintroduced bill and we want to merge with an
        # older Bill object.
        bill._newbill = True
        try:
            if previous_session:
                mergebill = Bill.objects.get(sessions=previous_session,
                                             number=bill.number,
                                             name_en__iexact=bill.name_en)

                if bill.id:
                    # If the new bill has already been saved, let's not try
                    # to merge automatically
                    logger.error("Bill %s may need to be merged. IDs: %s %s" %
                                 (bill.number, bill.id, mergebill.id))
                else:
                    logger.warning("Merging bill %s" % bill.number)
                    bill = mergebill
                    bis.bill = bill
        except Bill.DoesNotExist:
            # Nothing to merge
            pass

    _update(bill, 'name_fr', lbill.xpath('BillTitle/Title[@language="fr"]')[0].text)
    _update(bill, 'short_title_en', lbill.xpath('ShortTitle/Title[@language="en"]')[0].text)
    _update(bill, 'short_title_fr', lbill.xpath('ShortTitle/Title[@language="fr"]')[0].text)

    if not bis.sponsor_politician and bill.number[0] == 'C' and lbill.xpath('SponsorAffiliation/@id'):
        # We don't deal with Senate sponsors yet
        pol_id = int(lbill.xpath('SponsorAffiliation/@id')[0])
        try:
            bis.sponsor_politician = Politician.objects.get_by_parl_id(pol_id)
        except Politician.DoesNotExist:
            logger.error("Couldn't find sponsor politician for bill %s, pol ID %s" % (bill.number, pol_id))
        bis._changed = True
        try:
            bis.sponsor_member = ElectedMember.objects.get_by_pol(politician=bis.sponsor_politician,
                                                                   session=session)
        except Exception:
            logger.error("Couldn't find ElectedMember for bill %s, pol %r" %
                         (bill.number, bis.sponsor_politician))
        if not bill.sponsor_politician:
            bill.sponsor_politician = bis.sponsor_politician
            bill.sponsor_member = bis.sponsor_member
            bill._changed = True

    _update(bis, 'introduced', _parse_date(lbill.xpath('BillIntroducedDate')[0].text))
    if not bill.introduced:
        bill.introduced = bis.introduced

    try:
        status_code = lbill.xpath('Events')[0].get('laagCurrentStage')
        if status_code == '':
            status_code = 'Introduced'
        _update(bill, 'status_code', status_code)
        if status_code not in Bill.STATUS_CODES:
            logger.error("Unknown bill status code %s" % status_code)
        #_update(bill, 'status_date', _parse_date(
        #    lbill.xpath('Events/LastMajorStageEvent/Event/@date')[0]))
        status_dates = [_parse_date(d) for d in lbill.xpath('Events/LegislativeEvents/Event/@date')]
        _update(bill, 'status_date', max(status_dates))
    except IndexError:
        # Some older bills don't have status information
        pass

    try:
        _update(bill, 'text_docid', int(
            lbill.xpath('Publications/Publication/@id')[-1]))
    except IndexError:
        pass

    _update(bis, 'legisinfo_id', int(lbill.get('id')))

    if getattr(bill, '_changed', False):
        bill.save()
    if getattr(bis, '_changed', False):
        bis.bill = bis.bill # bizarrely, the django orm makes you do this
        bis.save()        

    for levent in lbill.xpath('Events/LegislativeEvents/Event'):
        source_id = int(levent.get('id'))
        if BillEvent.objects.filter(source_id=source_id).exists():
            continue

        event = BillEvent(
            source_id=source_id,
            bis=bis,
            date=_parse_date(levent.get('date')),
            institution='S' if levent.get('chamber') == 'SEN' else 'C',
            status_en=levent.xpath('Status/Title[@language="en"]/text()')[0],
            status_fr=levent.xpath('Status/Title[@language="fr"]/text()')[0]
        )

        if event.institution == 'C':
            hansard_num = levent.get('meetingNumber')
            try:
                event.debate = Document.debates.get(session=bis.session, number=hansard_num)
            except Document.DoesNotExist:
                logger.info(u"Could not associate BillEvent for %s with Hansard#%s" % (bill, hansard_num))
                continue

            for lcommittee in levent.xpath('Committee'):
                acronym = lcommittee.get('accronym')
                if acronym and acronym != 'WHOL':
                    event.save()
                    try:
                        committee = Committee.objects.get_by_acronym(acronym, bis.session)
                        for number in lcommittee.xpath('CommitteeMeetings/CommitteeMeeting/@number'):
                            event.committee_meetings.add(
                                CommitteeMeeting.objects.get(committee=committee, number=int(number), session=bis.session)
                            )
                    except ObjectDoesNotExist:
                        logger.exception("Could not import committee meetings: %s" % etree.tostring(lcommittee))
                        continue
        event.save()

    if getattr(bill, '_newbill', False) and not session.end:
        bill.save_sponsor_activity()

    if bill.text_docid and not BillText.objects.filter(docid=bill.text_docid).exists():
        try:
            BillText.objects.create(
                bill=bill,
                docid=bill.text_docid,
                text_en=get_plain_bill_text(bill)
            )
            bill.save()  # to trigger search indexing
        except CannotScrapeException:
            logger.warning(u"Could not get bill text for %s" % bill)

    return bill
            
########NEW FILE########
__FILENAME__ = parlvotes
import xml.etree.ElementTree as etree
import urllib2
import datetime

from django.db import transaction

from parliament.bills.models import Bill, VoteQuestion, MemberVote
from parliament.core.models import ElectedMember, Politician, Riding, Session
from parliament.core import parsetools

import logging
logger = logging.getLogger(__name__)

VOTELIST_URL = 'http://www2.parl.gc.ca/HouseChamberBusiness/Chambervotelist.aspx?Language=E&Mode=1&Parl=%(parliamentnum)s&Ses=%(sessnum)s&xml=True&SchemaVersion=1.0'
VOTEDETAIL_URL = 'http://www2.parl.gc.ca/HouseChamberBusiness/Chambervotedetail.aspx?Language=%(lang)s&Mode=1&Parl=%(parliamentnum)s&Ses=%(sessnum)s&FltrParl=%(parliamentnum)s&FltrSes=%(sessnum)s&vote=%(votenum)s&xml=True'

@transaction.commit_on_success
def import_votes(session=None):
    if session is None:
        session = Session.objects.current()
    votelisturl = VOTELIST_URL % {'parliamentnum' : session.parliamentnum, 'sessnum': session.sessnum}
    votelistpage = urllib2.urlopen(votelisturl)
    tree = etree.parse(votelistpage)
    root = tree.getroot()
    votelist = root.findall('Vote')
    votelist.reverse() # We want to process earlier votes first, just for the order they show up in the activity feed
    for vote in votelist:
        votenumber = int(vote.attrib['number'])
        if VoteQuestion.objects.filter(session=session, number=votenumber).count():
            continue
        print "Processing vote #%s" % votenumber
        votequestion = VoteQuestion(
            number=votenumber,
            session=session,
            date=datetime.date(*(int(x) for x in vote.attrib['date'].split('-'))),
            yea_total=int(vote.find('TotalYeas').text),
            nay_total=int(vote.find('TotalNays').text),
            paired_total=int(vote.find('TotalPaired').text))
        if sum((votequestion.yea_total, votequestion.nay_total)) < 100:
            logger.error("Fewer than 100 votes on vote#%s" % votenumber)
        decision = vote.find('Decision').text
        if decision in ('Agreed to', 'Agreed To'):
            votequestion.result = 'Y'
        elif decision == 'Negatived':
            votequestion.result = 'N'
        elif decision == 'Tie':
            votequestion.result = 'T'
        else:
            raise Exception("Couldn't process vote result %s in %s" % (decision, votelisturl))
        if vote.find('RelatedBill') is not None:
            billnumber = vote.find('RelatedBill').attrib['number']
            try:
                votequestion.bill = Bill.objects.get(sessions=session, number=billnumber)
            except Bill.DoesNotExist:
                votequestion.bill = Bill.objects.create_temporary_bill(session=session, number=billnumber)
                logger.warning("Temporary bill %s created for vote %s" % (billnumber, votenumber))

        # Now get the detailed results
        def get_detail(lang):
            votedetailurl = VOTEDETAIL_URL % {
                    'lang': lang,
                    'parliamentnum' : session.parliamentnum,
                    'sessnum': session.sessnum,
                    'votenum': votenumber 
            }
            votedetailpage = urllib2.urlopen(votedetailurl)
            detailtree = etree.parse(votedetailpage)
            detailroot = detailtree.getroot()
            return (detailroot, parsetools.etree_extract_text(detailroot.find('Context')).strip())
        try:
            detailroot_fr, votequestion.description_fr = get_detail('F')
            detailroot, votequestion.description_en = get_detail('E')
        except Exception as e:
            logger.exception("Import error on vote #%s" % votenumber)
            continue
        
        # Okay, save the question, start processing members.
        votequestion.save()
        for voter in detailroot.findall('Participant'):
            name = voter.find('FirstName').text + ' ' + voter.find('LastName').text
            riding = Riding.objects.get_by_name(voter.find('Constituency').text)
            pol = Politician.objects.get_by_name(name=name, session=session, riding=riding)
            member = ElectedMember.objects.get_by_pol(politician=pol, date=votequestion.date)
            rvote = voter.find('RecordedVote')
            if rvote.find('Yea').text == '1':
                ballot = 'Y'
            elif rvote.find('Nay').text == '1':
                ballot = 'N'
            elif rvote.find('Paired').text == '1':
                ballot = 'P'
            else:
                raise Exception("Couldn't parse RecordedVote for %s in vote %s" % (name, votenumber))
            MemberVote(member=member, politician=pol, votequestion=votequestion, vote=ballot).save()
        votequestion.label_absent_members()
        votequestion.label_party_votes()
        for mv in votequestion.membervote_set.all():
            mv.save_activity()
    return True
########NEW FILE########
__FILENAME__ = parl_bio
import re
import urllib2

from BeautifulSoup import BeautifulSoup

from parliament.core.models import Politician, PoliticianInfo

def update_politician_info(pol):
    parlid = pol.info()['parl_id']
    url = 'http://webinfo.parl.gc.ca/MembersOfParliament/ProfileMP.aspx?Key=%s&Language=E' % parlid
    soup = BeautifulSoup(urllib2.urlopen(url))

    def _get_field(fieldname):
        return soup.find(id=re.compile(r'MasterPage_.+_DetailsContent_.+_' + fieldname + '$'))
    
    phonespan = _get_field('lblTelephoneData')
    if phonespan and phonespan.string:
        pol.set_info('phone', phonespan.string.replace('  ', ' '))
        
    faxspan = _get_field('lblFaxData')
    if faxspan and faxspan.string:
        pol.set_info('fax', faxspan.string.replace('  ', ' '))
        
    maillink = _get_field('hlEMail')
    if maillink and maillink.string:
        pol.set_info('email', maillink.string)
        
    weblink = _get_field('hlWebSite')
    if weblink and weblink['href']:
        pol.set_info('web_site', weblink['href'])
    
    constit_div = _get_field('divConstituencyOffices')
    if constit_div: 
        constit = u''
        for row in constit_div.findAll('td'):
            constit += unicode(row.string) if row.string else ''
            constit += "\n"
        pol.set_info('constituency_offices', constit.replace('Telephone:', 'Phone:'))
########NEW FILE########
__FILENAME__ = parl_cmte
import datetime
import logging
import re
import time
import urllib2

from django.db import transaction

from BeautifulSoup import BeautifulSoup
import lxml.html

from parliament.committees.models import (Committee, CommitteeMeeting,
    CommitteeActivity, CommitteeActivityInSession,
    CommitteeReport, CommitteeInSession)
from parliament.core.models import Session
from parliament.hansards.models import Document

logger = logging.getLogger(__name__)

COMMITTEE_LIST_URL = 'http://www2.parl.gc.ca/CommitteeBusiness/CommitteeList.aspx?Language=E&Parl=%d&Ses=%d&Mode=2'
@transaction.commit_on_success
def import_committee_list(session=None):
    if session is None:
        session = Session.objects.current()

    def make_committee(namestring, parent=None):
        #print namestring
        match = re.search(r'^(.+) \(([A-Z0-9]{3,5})\)$', namestring)
        (name, acronym) = match.groups()
        try:
            return Committee.objects.get_by_acronym(acronym, session)
        except Committee.DoesNotExist:
            committee, created = Committee.objects.get_or_create(name_en=name.strip(), parent=parent)
            if created:
                logger.warning(u"Creating committee: %s, %s" % (committee.name_en, committee.slug))
            CommitteeInSession.objects.get_or_create(
                committee=committee, session=session, acronym=acronym)
            return committee
    
    soup = BeautifulSoup(urllib2.urlopen(COMMITTEE_LIST_URL %
        (session.parliamentnum, session.sessnum)))
    for li in soup.findAll('li', 'CommitteeItem'):
        com = make_committee(li.find('a').string)
        for sub in li.findAll('li', 'SubCommitteeItem'):
            make_committee(sub.find('a').string, parent=com)
    
    return True

def _docid_from_url(u):
    return int(re.search(r'DocId=(\d+)&', u).group(1))
    
def _12hr(hour, ampm):
    hour = int(hour)
    hour += 12 * bool('p' in ampm.lower())
    if hour % 12 == 0:
        # noon, midnight
        hour -= 12
    return hour
    
def _parse_date(d):
    """datetime objects from e.g. March 11, 2011"""
    return datetime.date(
        *time.strptime(d, '%B %d, %Y')[:3]
    )


def import_committee_documents(session):
    for comm in Committee.objects.filter(sessions=session).order_by('-parent'):
        # subcommittees last
        import_committee_meetings(comm, session)
        import_committee_reports(comm, session)
        time.sleep(1)

COMMITTEE_MEETINGS_URL = 'http://www2.parl.gc.ca/CommitteeBusiness/CommitteeMeetings.aspx?Cmte=%(acronym)s&Language=E&Parl=%(parliamentnum)d&Ses=%(sessnum)d&Mode=1'
@transaction.commit_on_success
def import_committee_meetings(committee, session):

    acronym = committee.get_acronym(session)
    url = COMMITTEE_MEETINGS_URL % {'acronym': acronym,
        'parliamentnum': session.parliamentnum,
        'sessnum': session.sessnum}
    resp = urllib2.urlopen(url)
    tree = lxml.html.parse(resp)
    root = tree.getroot()
    for mtg_row in root.cssselect('.MeetingTableRow'):
        number = int(re.sub(r'\D', '', mtg_row.cssselect('.MeetingNumber')[0].text))
        assert number > 0
        try:
            meeting = CommitteeMeeting.objects.select_related('evidence').get(
                committee=committee,session=session, number=number)
        except CommitteeMeeting.DoesNotExist:
            meeting = CommitteeMeeting(committee=committee,
                session=session, number=number)
        
        meeting.date = _parse_date(mtg_row.cssselect('.MeetingDate')[0].text)
        
        timestring = mtg_row.cssselect('.MeetingTime')[0].text_content()
        match = re.search(r'(\d\d?):(\d\d) ([ap]\.m\.)(?: - (\d\d?):(\d\d) ([ap]\.m\.))?\s\(',
            timestring, re.UNICODE)
        meeting.start_time = datetime.time(_12hr(match.group(1), match.group(3)), int(match.group(2)))
        if match.group(4):
            meeting.end_time = datetime.time(_12hr(match.group(4), match.group(6)), int(match.group(5)))
        
        notice_link = mtg_row.cssselect('.MeetingPublicationIcon[headers=thNoticeFuture] a')
        if notice_link:
            meeting.notice = _docid_from_url(notice_link[0].get('href'))
        minutes_link = mtg_row.cssselect('.MeetingPublicationIcon[headers=thMinutesPast] a')
        if minutes_link:
            meeting.minutes = _docid_from_url(minutes_link[0].get('href'))
        
        evidence_link = mtg_row.cssselect('.MeetingPublicationIcon[headers=thEvidencePast] a')
        if evidence_link:
            evidence_id = _docid_from_url(evidence_link[0].get('href'))
            if meeting.evidence_id:
                if meeting.evidence.source_id != evidence_id:
                    raise Exception("Evidence docid mismatch for %s %s: %s %s" %
                        (committee.acronym, number, evidence_id, meeting.evidence.source_id))
                else:
                    # Evidence hasn't changed; we don't need to worry about updating
                    continue
            else:
                if Document.objects.filter(source_id=evidence_id).exists():
                    raise Exception("Found evidence source_id %s, but it already exists" % evidence_id)
                meeting.evidence = Document.objects.create(
                    source_id=evidence_id,
                    date=meeting.date,
                    session=session,
                    document_type=Document.EVIDENCE)
        
        meeting.webcast = bool(mtg_row.cssselect('.MeetingStatusIcon img[title=Webcast]'))
        meeting.in_camera = bool(mtg_row.cssselect('.MeetingStatusIcon img[title*="in camera"]'))
        if not meeting.televised:
            meeting.televised = bool(mtg_row.cssselect('.MeetingStatusIcon img[title*="televised"]'))
        if not meeting.travel:
            meeting.travel = bool(mtg_row.cssselect('.MeetingStatusIcon img[title*="travel"]'))
        
        meeting.save()
        
        for study_link in mtg_row.cssselect('.MeetingStudyActivity a'):
            name = study_link.text.strip()
            study = get_activity_by_url(study_link.get('href'))
            meeting.activities.add(study)
    
    return True

COMMITTEE_ACTIVITY_URL = 'http://www.parl.gc.ca/CommitteeBusiness/StudyActivityHome.aspx?Stac=%(activity_id)d&Language=%(language)s&Parl=%(parliamentnum)d&Ses=%(sessnum)d'
def get_activity_by_url(activity_url):
    activity_id = int(re.search(r'Stac=(\d+)', activity_url).group(1))
    session = Session.objects.get_from_parl_url(activity_url)
    try:
        return CommitteeActivityInSession.objects.get(source_id=activity_id).activity
    except CommitteeActivityInSession.DoesNotExist:
        pass

    activity = CommitteeActivity()

    url = COMMITTEE_ACTIVITY_URL % {
        'activity_id': activity_id,
        'language': 'E',
        'parliamentnum': session.parliamentnum,
        'sessnum': session.sessnum
    }
    root = lxml.html.parse(urllib2.urlopen(url)).getroot()

    acronym = re.search(r'\(([A-Z][A-Z0-9]{2,4})\)', root.cssselect('div.HeaderTitle span')[0].text).group(1)

    activity.committee = CommitteeInSession.objects.get(acronym=acronym, session=session).committee

    activity_type = root.cssselect('span.StacTitlePrefix')[0]
    activity.study = 'Study' in activity_type.text
    activity.name_en = activity_type.tail.strip()[:500]

    # See if this already exists for another session
    try:
        activity = CommitteeActivity.objects.get(
            committee=activity.committee,
            study=activity.study,
            name_en=activity.name_en
        )
    except CommitteeActivity.DoesNotExist:
        # Get the French name
        url = COMMITTEE_ACTIVITY_URL % {
            'activity_id': activity_id,
            'language': 'F',
            'parliamentnum': session.parliamentnum,
            'sessnum': session.sessnum
        }
        root = lxml.html.parse(urllib2.urlopen(url)).getroot()
        activity_type = root.cssselect('span.StacTitlePrefix')[0]
        activity.name_fr = activity_type.tail.strip()[:500]

        activity.save()

    if CommitteeActivityInSession.objects.exclude(source_id=activity_id).filter(
            session=session, activity=activity).exists():
        logger.warning("Apparent duplicate activity ID for %s %s %s: %s" %
                     (activity, activity.committee, session, activity_id))
        return activity
    
    CommitteeActivityInSession.objects.create(
        session=session,
        activity=activity,
        source_id=activity_id
    )
    return activity

COMMITTEE_REPORT_URL = 'http://www2.parl.gc.ca/CommitteeBusiness/ReportsResponses.aspx?Cmte=%(acronym)s&Language=E&Mode=1&Parl=%(parliamentnum)d&Ses=%(sessnum)d'
@transaction.commit_on_success
def import_committee_reports(committee, session):
    # FIXME rework to parse out the single all-reports page?
    acronym = committee.get_acronym(session)
    url = COMMITTEE_REPORT_URL % {'acronym': acronym,
        'parliamentnum': session.parliamentnum,
        'sessnum': session.sessnum}
    tree = lxml.html.parse(urllib2.urlopen(url))
    
    def _import_report(report_link, parent=None):
        report_docid = _docid_from_url(report_link.get('href'))
        try:
            report = CommitteeReport.objects.get(committee=committee,
                session=session, source_id=report_docid, parent=parent)
            if report.presented_date:
                # We can consider this report fully parsed
                return report
        except CommitteeReport.DoesNotExist:
            if CommitteeReport.objects.filter(source_id=report_docid).exists():
                if committee.parent and \
                  CommitteeReport.objects.filter(source_id=report_docid, committee=committee.parent).exists():
                    # Reference to parent committee report
                    return None
                else:
                    raise Exception("Duplicate report ID %s on %s" % (report_docid, url))
            report = CommitteeReport(committee=committee,
                session=session, source_id=report_docid, parent=parent)
            report_name = report_link.text.strip()
            match = re.search(r'^Report (\d+) - (.+)', report_name)
            if match:
                report.number = int(match.group(1))
                report.name_en = match.group(2).strip()
            else:
                report.name_en = report_name
            report.government_response = bool(report_link.xpath("../span[contains(., 'Government Response')]"))
        
        match = re.search(r'Adopted by the Committee on ([a-zA-Z0-9, ]+)', report_link.tail)
        if match:
            report.adopted_date = _parse_date(match.group(1))
        match = re.search(r'Presented to the House on ([a-zA-Z0-9, ]+)', report_link.tail)
        if match:
            report.presented_date = _parse_date(match.group(1))
        report.save()
        return report
            
    
    for item in tree.getroot().cssselect('.TocReportItemText'):
        report_link = item.xpath('./a')[0]
        report = _import_report(report_link)
        for response_link in item.cssselect('.TocResponseItemText a'):
            _import_report(response_link, parent=report)
            
    return True
########NEW FILE########
__FILENAME__ = parl_document
"""Parse XML transcripts from parl.gc.ca.

These transcripts are either House Hansards, or House committee evidence.

Most of the heavily-lifting code has been put in a separate module
called alpheus: http://github.com/rhymeswithcycle/alpheus
"""
from difflib import SequenceMatcher
import re
import sys
import urllib2
from xml.sax.saxutils import quoteattr

from django.core import urlresolvers
from django.db import transaction

import alpheus
from BeautifulSoup import BeautifulSoup

from parliament.bills.models import Bill, BillInSession, VoteQuestion
from parliament.core.models import Politician, ElectedMember, Session
from parliament.hansards.models import Statement, Document, OldSequenceMapping

import logging
logger = logging.getLogger(__name__)

@transaction.commit_on_success
def import_document(document, interactive=True, reimport_preserving_sequence=False):
    old_statements = None
    if document.statement_set.all().exists():
        if reimport_preserving_sequence:
            if OldSequenceMapping.objects.filter(document=document).exists():
                logger.error("Sequence mapping already exits for %s" % document)
                return
            old_statements = list(document.statement_set.all())
            document.statement_set.all().delete()
        else:
            if not interactive:
                return
            sys.stderr.write("Statements already exist for %r.\nDelete them? (y/n) " % document)
            if raw_input().strip() != 'y':
                return
            document.statement_set.all().delete()

    document.download()
    xml_en = document.get_cached_xml('en')
    pdoc_en = alpheus.parse_file(xml_en)
    xml_en.close()

    xml_fr = document.get_cached_xml('fr')
    pdoc_fr = alpheus.parse_file(xml_fr)
    xml_fr.close()
    
    if document.date and document.date != pdoc_en.meta['date']:
        # Sometimes they get the date wrong
        if document.date != pdoc_fr.meta['date']:
            logger.error("Date mismatch on document #%s: %s %s" % (
                document.id, document.date, pdoc_en.meta['date']))
    else:
        document.date = pdoc_en.meta['date']
    document.number = pdoc_en.meta['document_number']
    document.public = True

    statements = []

    for pstate in pdoc_en.statements:
        s = Statement(
            document=document,
            sequence=len(statements),
            content_en=pstate.content,
            time=pstate.meta['timestamp'])
        s.source_id = pstate.meta['id']
        s.h1_en = pstate.meta.get('h1', '')
        s.h2_en = pstate.meta.get('h2', '')
        s.h3_en = pstate.meta.get('h3', '')

        if s.h1_en and not s.h2_en:
            s.h2_en = s.h3_en
            s.h3_en = ''

        s.who_en = pstate.meta.get('person_attribution', '')
        s.who_hocid = int(pstate.meta['person_id']) if pstate.meta.get('person_id') else None
        s.who_context_en = pstate.meta.get('person_context', '')

        s.statement_type = pstate.meta.get('intervention_type', '').lower()
        s.written_question = pstate.meta.get('written_question', '').upper()[:1]

        if s.who_hocid and not pstate.meta.get('person_type'):
            # At the moment. person_type is only set if we know the person
            # is a non-politician. This might change...
            try:
                s.politician = Politician.objects.get_by_parl_id(s.who_hocid, session=document.session)
                s.member = ElectedMember.objects.get_by_pol(s.politician, date=document.date)
            except Politician.DoesNotExist:
                logger.info("Could not resolve speaking politician ID %s for %r" % (s.who_hocid, s.who))

        s._related_pols = set()
        s._related_bills = set()
        s.content_en = _process_related_links(s.content_en, s)

        statements.append(s)

    if len(statements) != len(pdoc_fr.statements):
        logger.info("French and English statement counts don't match for %r" % document)

    _r_paragraphs = re.compile(ur'<p[^>]* data-HoCid=.+?</p>')
    _r_paragraph_id = re.compile(ur'<p[^>]* data-HoCid="(?P<id>\d+)"')
    fr_paragraphs = dict()
    fr_statements = dict()

    def _get_paragraph_id(p):
        return int(_r_paragraph_id.match(p).group('id'))

    for st in pdoc_fr.statements:
        if st.meta['id']:
            fr_statements[st.meta['id']] = st
        for p in _r_paragraphs.findall(st.content):
            fr_paragraphs[_get_paragraph_id(p)] = p

    def _substitute_french_content(match):
        try:
            return fr_paragraphs[_get_paragraph_id(match.group(0))]
        except KeyError:
            logger.error("Paragraph ID %s not found in French for %s" % (match.group(0), document))
            return match.group(0)

    for st in statements:
        st.content_fr = _process_related_links(
            _r_paragraphs.sub(_substitute_french_content, st.content_en),
            st
        )
        fr_data = fr_statements.get(st.source_id)
        if fr_data:
            st.h1_fr = fr_data.meta.get('h1', '')
            st.h2_fr = fr_data.meta.get('h2', '')
            st.h3_fr = fr_data.meta.get('h3', '')
            if st.h1_fr and not st.h2_fr:
                st.h2_fr = s.h3_fr
                st.h3_fr = ''
            st.who_fr = fr_data.meta.get('person_attribution', '')
            st.who_context_fr = fr_data.meta.get('person_context', '')


    document.multilingual = True

    Statement.set_slugs(statements)

    if old_statements:
        for mapping in _align_sequences(statements, old_statements):
            OldSequenceMapping.objects.create(
                document=document,
                sequence=mapping[0],
                slug=mapping[1]
            )
        
    for s in statements:
        s.save()

        s.mentioned_politicians.add(*list(s._related_pols))
        s.bills.add(*list(s._related_bills))
        if getattr(s, '_related_vote', False):
            s._related_vote.context_statement = s
            s._related_vote.save()

    document.save()

    return document

def _align_sequences(new_statements, old_statements):
    """Given two list of statements, returns a list of mappings in the form of
    (old_statement_sequence, new_statement_slug)"""

    def build_speaker_dict(states):
        d = {}
        for s in states:
            d.setdefault(s.name_info['display_name'], []).append(s)
        return d

    def get_comparison_sequence(text):
        return re.split(r'\s+', text)

    def calculate_similarity(old, new):
        """Given two statements, return a score between 0 and 1 expressing their similarity"""
        score = 0.8 if old.time == new.time else 0.0
        oldtext, newtext = old.text_plain(), new.text_plain()
        if new in chosen:
            score -= 0.01
        if newtext in oldtext:
            similarity = 1.0
        else:
            similarity = SequenceMatcher(
                None, get_comparison_sequence(oldtext), get_comparison_sequence(newtext)
            ).ratio()
        return (score + similarity) / 1.8

    new_speakers, old_speakers = build_speaker_dict(new_statements), build_speaker_dict(old_statements)
    mappings = []
    chosen = set()

    for speaker, olds in old_speakers.items():
        news = new_speakers.get(speaker, [])
        if speaker and len(olds) == len(news):
            # The easy version: assume we've got the same statements
            for old, new in zip(olds, news):
                score = calculate_similarity(old, new)
                if score < 0.9:
                    logger.warning("Low similarity for easy match %s: %r %r / %r %r"
                        % (score, old, old.text_plain(), new, new.text_plain()))
                mappings.append((old.sequence, new.slug))
        else:
            # Try and pair the most similar statement
            if news:
                logger.info("Count mismatch for %s" % speaker)
                candidates = news
            else:
                logger.warning("No new statements for %s" % speaker)
                candidates = new_statements # Calculate similarity with all possibilities
            for old in olds:
                scores = ( (cand, calculate_similarity(old, cand)) for cand in candidates )
                choice, score = max(scores, key=lambda s: s[1])
                chosen.add(choice)
                if score < 0.75:
                    logger.warning("Low-score similarity match %s: %r %r / %r %r"
                        % (score, old, old.text_plain(), choice, choice.text_plain()))
                mappings.append((old.sequence, choice.slug))

    return mappings

def _process_related_links(content, statement):
    return re.sub(r'<a class="related_link (\w+)" ([^>]+)>(.*?)</a>',
        lambda m: _process_related_link(m, statement),
        content)

def _process_related_link(match, statement):
    (link_type, tagattrs, text) = match.groups()
    params = dict([(m.group(1), m.group(2)) for m in re.finditer(r'data-([\w-]+)="([^"]+)"', tagattrs)])
    hocid = int(params['HoCid'])
    if link_type == 'politician':
        try:
            pol = Politician.objects.get_by_parl_id(hocid)
        except Politician.DoesNotExist:
            logger.error("Could not resolve related politician #%s, %r" % (hocid, text))
            return text
        url = pol.get_absolute_url()
        title = pol.name
        statement._related_pols.add(pol)
    elif link_type == 'legislation':
        try:
            bis = BillInSession.objects.get_by_legisinfo_id(hocid)
            bill = bis.bill
            url = bis.get_absolute_url()
        except Bill.DoesNotExist:
            match = re.search(r'\b[CS]\-\d+[A-E]?\b', text)
            if not match:
                logger.error("Invalid bill link %s" % text)
                return text
            bill = Bill.objects.create_temporary_bill(legisinfo_id=hocid,
                number=match.group(0), session=statement.document.session)
            url = bill.get_absolute_url()
        title = bill.name
        statement._related_bills.add(bill)
    elif link_type == 'vote':
        try:
            vote = VoteQuestion.objects.get(session=statement.document.session,
                number=int(params['number']))
            url = vote.get_absolute_url()
            title = vote.description
            statement._related_vote = vote
        except VoteQuestion.DoesNotExist:
            # We'll just operate on faith that the vote will soon
            # be created
            url = urlresolvers.reverse('parliament.bills.views.vote',
                kwargs={'session_id': statement.document.session_id, 'number': params['number']})
            title = None
    else:
        raise Exception("Unknown link type %s" % link_type)

    attrs = {
        'href': url,
        'data-HoCid': hocid
    }
    if title:
        attrs['title'] = title
    return _build_tag(u'a', attrs) + text + u'</a>'

def _build_tag(name, attrs):
    return u'<%s%s>' % (
        name,
        u''.join([u" %s=%s" % (k, quoteattr(unicode(v))) for k,v in sorted(attrs.items())])
    )

def _docid_from_url(u):
    return int(re.search(r'DocId=(\d+)', u).group(1))

def fetch_latest_debates(session=None):
    if not session:
        session = Session.objects.current()

    url = 'http://www2.parl.gc.ca/housechamberbusiness/chambersittings.aspx?View=H&Parl=%d&Ses=%d&Language=E&Mode=2' % (
        session.parliamentnum, session.sessnum)
    soup = BeautifulSoup(urllib2.urlopen(url))

    cal = soup.find('div', id='ctl00_PageContent_calTextCalendar')
    for link in cal.findAll('a', href=True):
        source_id = _docid_from_url(link['href'])
        if not Document.objects.filter(source_id=source_id).exists():
            Document.objects.create(
                document_type=Document.DEBATE,
                session=session,
                source_id=source_id
            )




        


########NEW FILE########
__FILENAME__ = politwitter
import re
import urllib2

from django.conf import settings

from lxml import etree, objectify
import twitter

from parliament.core.models import Politician, PoliticianInfo, Session

import logging
logger = logging.getLogger(__name__)

def import_twitter_ids():
    source = urllib2.urlopen('http://politwitter.ca/api.php?format=xml&call=listmp')
    # politwitter XML sometimes includes invalid entities
    parser = objectify.makeparser(recover=True)
    tree = objectify.parse(source, parser)
    current_session = Session.objects.current()
    for member in tree.xpath('//member'):
        try:
            pol = Politician.objects.get_by_name(unicode(member.name), session=current_session)
        except Politician.DoesNotExist:
            print "Could not find politician %r" % member.name
        current = pol.info().get('twitter')
        new = str(member.twitter_username)
        if new and str(current).lower() != new.lower():
            logger.error(u"Twitter username change for %s: %s -> %s"
                % (pol, current, new))
            if not current:
                try:
                    pol.set_info('twitter_id', get_id_from_screen_name(new))
                    pol.set_info('twitter', new)
                except Exception as e:
                    print repr(e)
                
def update_twitter_list():
    from twitter import twitter_globals
    twitter_globals.POST_ACTIONS.append('create_all')
    t = twitter.Twitter(auth=twitter.OAuth(**settings.TWITTER_OAUTH), domain='api.twitter.com/1')
    current_names = set(PoliticianInfo.objects.exclude(value='').filter(schema='twitter').values_list('value', flat=True))
    list_names= set()
    cursor = -1
    while cursor:
        result = t.user.listname.members(
          user=settings.TWITTER_USERNAME, listname=settings.TWITTER_LIST_NAME,
          cursor=cursor)
        for u in result['users']:
            list_names.add(u['screen_name'])
        cursor = result['next_cursor']
    not_in_db = (list_names - current_names)
    if not_in_db:
        logger.error("Users on list, not in DB: %r" % not_in_db)
    
    not_on_list = (current_names - list_names)
    t.user.listname.members.create_all(user=settings.TWITTER_USERNAME, listname=settings.TWITTER_LIST_NAME,
        screen_name=','.join(not_on_list))
    logger.warning("Users added to Twitter list: %r" % not_on_list)
    
def get_id_from_screen_name(screen_name):
    t = twitter.Twitter(auth=twitter.OAuth(**settings.TWITTER_OAUTH), domain='api.twitter.com/1.1')
    return t.users.show(screen_name=screen_name)['id']
    
def get_ids_from_screen_names():
    for p in Politician.objects.current():
        if 'twitter' in p.info() and 'twitter_id' not in p.info():
            try:
                p.set_info('twitter_id', get_id_from_screen_name(p.info()['twitter']))
            except Exception:
                logger.exception(u"Couldn't get twitter ID for %s" % p.name)
        

########NEW FILE########
__FILENAME__ = jobs
import time

from django.db import transaction, models
from django.conf import settings

from parliament.politicians import twit
from parliament.politicians import googlenews as gnews
from parliament.imports import parlvotes, legisinfo, parl_document, parl_cmte
from parliament.core.models import Politician, Session
from parliament.hansards.models import Document
from parliament.activity import utils as activityutils
from parliament.activity.models import Activity
from parliament.text_analysis import corpora

import logging
logger = logging.getLogger(__name__)

@transaction.commit_on_success
def twitter():
    twit.save_tweets()
    return True
    
def twitter_ids():
    from parliament.imports import politwitter
    politwitter.import_twitter_ids()
    
def googlenews():
    for pol in Politician.objects.current():
        gnews.save_politician_news(pol)
        #time.sleep(1)
        
def votes():
    parlvotes.import_votes()
    
def bills():
    legisinfo.import_bills(Session.objects.current())

@transaction.commit_on_success
def prune_activities():
    for pol in Politician.objects.current():
        activityutils.prune(Activity.public.filter(politician=pol))
    return True

def committee_evidence():
    for document in Document.evidence\
      .annotate(scount=models.Count('statement'))\
      .exclude(scount__gt=0).exclude(skip_parsing=True).order_by('date').iterator():
        print document
        parl_document.import_document(document, interactive=False)
        if document.statement_set.all().count():
            document.save_activity()
    
def committees(sess=None):
    if sess is None:
        sess = Session.objects.current()
    parl_cmte.import_committee_list(session=sess)
    parl_cmte.import_committee_documents(sess)

def committees_full():
    committees()
    committee_evidence()
    
@transaction.commit_on_success
def hansards_load():
    parl_document.fetch_latest_debates()
    return True
        
@transaction.commit_manually
def hansards_parse():
    for hansard in Document.objects.filter(document_type=Document.DEBATE)\
      .annotate(scount=models.Count('statement'))\
      .exclude(scount__gt=0).exclude(skip_parsing=True).order_by('date').iterator():
        try:
            parl_document.import_document(hansard, interactive=False)
        except Exception, e:
            transaction.rollback()
            logger.error("Hansard parse failure on #%s: %r" % (hansard.id, e))
            continue
        else:
            transaction.commit()
        # now reload the Hansard to get the date
        hansard = Document.objects.get(pk=hansard.id)
        try:
            hansard.save_activity()
        except Exception, e:
            transaction.rollback()
            raise e
        else:
            transaction.commit()
    transaction.commit()
            
def hansards():
    hansards_load()
    hansards_parse()
    
def corpus_for_debates():
    corpora.generate_for_debates()

def corpus_for_committees():
    corpora.generate_for_committees()    
########NEW FILE########
__FILENAME__ = legacy_urls
from django.conf.urls import patterns, include, url

from parliament.core.utils import redir_view

urlpatterns = patterns('parliament.hansards.redirect_views',
    (r'^hansards/$', redir_view('parliament.hansards.views.index')),
    (r'^hansards/year/(?P<year>\d{4})/$', redir_view('parliament.hansards.views.by_year')),
    url(r'^hansards/(?P<hansard_id>\d+)/$', 'hansard_redirect'),
    url(r'^hansards/(?P<hansard_date>[0-9-]+)/$', 'hansard_redirect'),
    url(r'^hansards/(?P<hansard_id>\d+)/(?P<sequence>\d+)/$', 'hansard_redirect'),
    url(r'^hansards/(?P<hansard_date>[0-9-]+)/(?P<sequence>\d+)/$', 'hansard_redirect'),
    url(r'^hansards/(?P<hansard_id>\d+)/(?P<sequence>\d+)/(?P<only>only|permalink)/$', 'hansard_redirect'),
    url(r'^hansards/(?P<hansard_date>[0-9-]+)/(?P<sequence>\d+)/(?P<only>only|permalink)/$', 'hansard_redirect'),
)
########NEW FILE########
__FILENAME__ = googlenews
import feedparser
import datetime
import hashlib

from django.utils.http import urlquote
from BeautifulSoup import BeautifulSoup
from django.utils.html import strip_tags

from parliament.activity import utils as activity

import logging

logger = logging.getLogger(__name__)

GOOGLE_NEWS_URL = 'http://news.google.ca/news?pz=1&cf=all&ned=ca&hl=en&as_maxm=3&q=%s&as_qdr=a&as_drrb=q&as_mind=25&as_minm=2&cf=all&as_maxd=27&scoring=n&output=rss'
def get_feed(pol):
    return feedparser.parse(GOOGLE_NEWS_URL % urlquote(get_query_string(pol)))
    
def get_query_string(pol):
    if 'googlenews_query' in pol.info():
        return pol.info()['googlenews_query']
    names = pol.alternate_names()
    if len(names) > 1:
        q = '( ' + ' OR '.join(['"%s"' % name for name in names]) + ')'
    else:
        q = '"%s"' % pol.name
    q += ' AND ("MP" OR "Member of Parliament") location:canada'
    return q
    
def news_items_for_pol(pol):
    feed = get_feed(pol)
    items = []
    for i in feed['entries'][:10]:
        item = {'url': i.link}
        title_elements = i.title.split('-')
        item['source'] = title_elements.pop().strip()
        item['title'] = '-'.join(title_elements).strip()
        item['date'] = datetime.date(*i.updated_parsed[:3])
        h = hashlib.md5()
        h.update(i.id)
        item['guid'] = 'gnews_%s_%s' % (pol.id, h.hexdigest())
        soup = BeautifulSoup(i.summary)
        try:
            item['summary'] = strip_tags(unicode(soup.findAll('font', size='-1')[1]))
        except Exception as e:
            logger.exception("Error getting news for %s" % pol.slug)
            continue
        if pol.name not in item['summary']:
            continue
        items.append(item)
    return items
    
def save_politician_news(pol):
    items = news_items_for_pol(pol)
    for item in items:
        activity.save_activity(item, politician=pol, date=item['date'], guid=item['guid'], variety='gnews')
########NEW FILE########
__FILENAME__ = models
# Politician models are actually in core/models.py
########NEW FILE########
__FILENAME__ = tests
from django.test import TestCase

from parliament.core.models import Politician

class SmokeTests(TestCase):
    
    fixtures = ['parties', 'ridings', 'sessions', 'politicians']
    
    def test_pages(self):
        
        self.assertContains(self.client.get('/politicians/'), 'Current MPs')
        
        assert self.client.get('/politicians/former/').status_code == 200
        
        self.assertContains(self.client.get('/politicians/hedy-fry/'), 'Vancouver Centre')
        
        assert self.client.get('/politicians/frank-mckenna/').status_code == 404
        
        rona = Politician.objects.get_by_name('Rona Ambrose')
        
        self.assertContains(self.client.get('/politicians/%s/rss/statements/' % rona.id), 'Rona ')
        self.assertContains(self.client.get('/politicians/%s/rss/activity/' % rona.id), 'Rona ')
########NEW FILE########
__FILENAME__ = twit
import email
import datetime
import re

from django.conf import settings
import twitter

from parliament.core.models import Politician, PoliticianInfo
from parliament.activity import utils as activity

import logging
logger = logging.getLogger(__name__)

def save_tweets():
    twitter_to_pol = dict([(int(i.value), i.politician) for i in PoliticianInfo.objects.filter(schema='twitter_id').select_related('politician')])
    screen_names = set(PoliticianInfo.objects.filter(schema='twitter').values_list('value', flat=True))
    twit = twitter.Twitter(
        auth=twitter.OAuth(**settings.TWITTER_OAUTH), domain='api.twitter.com/1.1')

    statuses = twit.lists.statuses(slug='mps', owner_screen_name='openparlca', include_rts=False, count=200)
    statuses.reverse()
    for status in statuses:
        try:
            pol = twitter_to_pol[status['user']['id']]
        except KeyError:
            logger.error("Can't find twitter ID %s (name %s)" 
                % (status['user']['id'], status['user']['screen_name']))
            continue
        if status['user']['screen_name'] not in screen_names:
            # Changed screen name
            pol.set_info('twitter', status['user']['screen_name'])
        date = datetime.date.fromtimestamp(
            email.utils.mktime_tz(
                email.utils.parsedate_tz(status['created_at'])
            )
        ) # fuck you, time formats
        guid = 'twit_%s' % status['id']
        # Twitter apparently escapes < > but not & " 
        # so I'm clunkily unescaping lt and gt then reescaping in the template
        text = status['text'].replace('&lt;', '<').replace('&gt;', '>')
        activity.save_activity({'text': status['text']}, politician=pol,
            date=date, guid=guid, variety='twitter')
            

        
    

########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import *
from parliament.politicians.views import *

urlpatterns = patterns('parliament.politicians.views',
    url(r'^(?P<pol_id>\d+)/rss/statements/$', 'politician_statement_feed', name="politician_statement_feed"),
    url(r'^(?P<pol_id>\d+)/rss/activity/$', PoliticianActivityFeed(), name="politician_activity_feed"),
    url(r'^$', 'current_mps', name='politicians'),
    (r'^former/$', 'former_mps'),
    (r'^autocomplete/$', 'politician_autocomplete'),
    url(r'^memberships/$', PoliticianMembershipListView.as_view(), name='politician_membership_list'),
    url(r'^memberships/(?P<member_id>\d+)/$', PoliticianMembershipView.as_view(), name='politician_membership'),
    (r'^(?P<pol_slug>[a-z-]+)/$', 'politician'),
    (r'^(?P<pol_id>\d+)/$', 'politician'),
    (r'^(?P<pol_slug>[a-z-]+)/contact/$', 'contact'),
    (r'^(?P<pol_id>\d+)/contact/$', 'contact'),
    (r'^(?P<pol_slug>[a-z-]+)/text-analysis/$', 'analysis'),
    (r'^(?P<pol_id>\d+)/text-analysis/$', 'analysis'),
    (r'^internal/hide_activity/$', 'hide_activity'),
)
########NEW FILE########
__FILENAME__ = views
import datetime
import itertools
import re
from urllib import urlencode

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.core import urlresolvers
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.template import loader, RequestContext
from django.views.decorators.vary import vary_on_headers

from parliament.activity.models import Activity
from parliament.activity import utils as activity
from parliament.core.api import ModelListView, ModelDetailView, APIFilters
from parliament.core.models import Politician, ElectedMember
from parliament.core.utils import feed_wrapper
from parliament.hansards.models import Statement, Document
from parliament.text_analysis.models import TextAnalysis
from parliament.text_analysis.views import TextAnalysisView
from parliament.utils.views import JSONView


class CurrentMPView(ModelListView):

    resource_name = 'Politicians'

    default_limit = 308

    filters = {
        'name': APIFilters.dbfield(help='e.g. Stephen Harper'),
        'family_name': APIFilters.dbfield('name_family', help='e.g. Harper'),
        'given_name': APIFilters.dbfield('name_given', help='e.g. Stephen'),
        'include': APIFilters.noop(help="'former' to show former MPs (since 94), 'all' for current and former")
    }

    def get_qs(self, request):
        if request.GET.get('include') == 'former':
            qs = Politician.objects.elected_but_not_current()
        elif request.GET.get('include') == 'all':
            qs = Politician.objects.elected()
        else:
            qs = Politician.objects.current()
        return qs.order_by('name_family')

    def get_html(self, request):
        t = loader.get_template('politicians/electedmember_list.html')
        c = RequestContext(request, {
            'object_list': ElectedMember.objects.current().order_by(
                'riding__province', 'politician__name_family').select_related('politician', 'riding', 'party'),
            'title': 'Current Members of Parliament'
        })
        return HttpResponse(t.render(c))
current_mps = CurrentMPView.as_view()


class FormerMPView(ModelListView):

    resource_name = 'Politicians'

    def get_json(self, request):
        return HttpResponsePermanentRedirect(urlresolvers.reverse('politicians') + '?include=former')

    def get_html(self, request):
        former_members = ElectedMember.objects.exclude(end_date__isnull=True)\
            .order_by('riding__province', 'politician__name_family', '-start_date')\
            .select_related('politician', 'riding', 'party')
        seen = set()
        object_list = []
        for member in former_members:
            if member.politician_id not in seen:
                object_list.append(member)
                seen.add(member.politician_id)

        c = RequestContext(request, {
            'object_list': object_list,
            'title': 'Former MPs (since 1994)'
        })
        t = loader.get_template("politicians/former_electedmember_list.html")
        return HttpResponse(t.render(c))
former_mps = FormerMPView.as_view()


class PoliticianView(ModelDetailView):

    resource_name = 'Politician'

    api_notes = """The other_info field is a direct copy of an internal catchall key-value store;
        beware that its structure may change frequently."""

    def get_object(self, request, pol_id=None, pol_slug=None):
        if pol_slug:
            return get_object_or_404(Politician, slug=pol_slug)
        else:
            return get_object_or_404(Politician, pk=pol_id)

    def get_related_resources(self, request, obj, result):
        pol_query = '?' + urlencode({'politician': obj.identifier})
        return {
            'speeches_url': urlresolvers.reverse('speeches') + pol_query,
            'ballots_url': urlresolvers.reverse('vote_ballots') + pol_query,
            'sponsored_bills_url': urlresolvers.reverse('bills') + '?' +
                urlencode({'sponsor_politician': obj.identifier}),
            'activity_rss_url': urlresolvers.reverse('politician_activity_feed', kwargs={'pol_id': obj.id})
        }

    def get_html(self, request, pol_id=None, pol_slug=None):
        pol = self.get_object(request, pol_id, pol_slug)
        if pol.slug and not pol_slug:
            return HttpResponsePermanentRedirect(pol.get_absolute_url())

        show_statements = bool('page' in request.GET or
            (pol.latest_member and not pol.latest_member.current))

        if show_statements:
            STATEMENTS_PER_PAGE = 10
            statements = pol.statement_set.filter(
                procedural=False, document__document_type=Document.DEBATE).order_by('-time', '-sequence')
            paginator = Paginator(statements, STATEMENTS_PER_PAGE)
            try:
                pagenum = int(request.GET.get('page', '1'))
            except ValueError:
                pagenum = 1
            try:
                statement_page = paginator.page(pagenum)
            except (EmptyPage, InvalidPage):
                statement_page = paginator.page(paginator.num_pages)
        else:
            statement_page = None

        c = RequestContext(request, {
            'pol': pol,
            'member': pol.latest_member,
            'candidacies': pol.candidacy_set.all().order_by('-election__date'),
            'electedmembers': pol.electedmember_set.all().order_by('-start_date'),
            'page': statement_page,
            'statements_politician_view': True,
            'show_statements': show_statements,
            'activities': activity.iter_recent(Activity.public.filter(politician=pol)),
            'search_placeholder': u"Search %s in Parliament" % pol.name,
            'wordcloud_js': TextAnalysis.objects.get_wordcloud_js(
                key=pol.get_absolute_url() + 'text-analysis/')
        })
        if request.is_ajax():
            t = loader.get_template("hansards/statement_page_politician_view.inc")
        else:
            t = loader.get_template("politicians/politician.html")
        return HttpResponse(t.render(c))
politician = vary_on_headers('X-Requested-With')(PoliticianView.as_view())


def contact(request, pol_id=None, pol_slug=None):
    if pol_slug:
        pol = get_object_or_404(Politician, slug=pol_slug)
    else:
        pol = get_object_or_404(Politician, pk=pol_id)

    if not pol.current_member:
        raise Http404

    c = RequestContext(request, {
        'pol': pol,
        'info': pol.info(),
        'title': u'Contact %s' % pol.name
    })
    t = loader.get_template("politicians/contact.html")
    return HttpResponse(t.render(c))


def hide_activity(request):
    if not request.user.is_authenticated() and request.user.is_staff:
        raise PermissionDenied

    activity = Activity.objects.get(pk=request.POST['activity_id'])
    activity.active = False
    activity.save()
    return HttpResponse('OK')


class PoliticianAutocompleteView(JSONView):

    def get(self, request):

        q = request.GET.get('q', '').lower()

        if not hasattr(self, 'politician_list'):
            self.politician_list = list(Politician.objects.elected().values(
                'name', 'name_family', 'slug', 'id').order_by('name_family'))

        results = (
            {'value': p['slug'] if p['slug'] else unicode(p['id']), 'label': p['name']}
            for p in self.politician_list
            if p['name'].lower().startswith(q) or p['name_family'].lower().startswith(q)
        )
        return list(itertools.islice(results, 15))
politician_autocomplete = PoliticianAutocompleteView.as_view()


class PoliticianMembershipView(ModelDetailView):

    resource_name = 'Politician membership'

    def get_object(self, request, member_id):
        return ElectedMember.objects.select_related(depth=1).get(id=member_id)


class PoliticianMembershipListView(ModelListView):

    resource_name = 'Politician memberships'

    def get_qs(self, request):
        return ElectedMember.objects.all().select_related(depth=1)


class PoliticianStatementFeed(Feed):

    def get_object(self, request, pol_id):
        self.language = request.GET.get('language', settings.LANGUAGE_CODE)
        return get_object_or_404(Politician, pk=pol_id)

    def title(self, pol):
        return "%s in the House of Commons" % pol.name

    def link(self, pol):
        return "http://openparliament.ca" + pol.get_absolute_url()

    def description(self, pol):
        return "Statements by %s in the House of Commons, from openparliament.ca." % pol.name

    def items(self, pol):
        return Statement.objects.filter(
            member__politician=pol, document__document_type=Document.DEBATE).order_by('-time')[:12]

    def item_title(self, statement):
        return statement.topic

    def item_link(self, statement):
        return statement.get_absolute_url()

    def item_description(self, statement):
        return statement.text_html(language=self.language)

    def item_pubdate(self, statement):
        return statement.time

politician_statement_feed = feed_wrapper(PoliticianStatementFeed)

r_title = re.compile(r'<span class="tag.+?>(.+?)</span>')
r_link = re.compile(r'<a [^>]*?href="(.+?)"')
r_excerpt = re.compile(r'<span class="excerpt">')


class PoliticianActivityFeed(Feed):

    def get_object(self, request, pol_id):
        return get_object_or_404(Politician, pk=pol_id)

    def title(self, pol):
        return pol.name

    def link(self, pol):
        return "http://openparliament.ca" + pol.get_absolute_url()

    def description(self, pol):
        return "Recent news about %s, from openparliament.ca." % pol.name

    def items(self, pol):
        return activity.iter_recent(Activity.objects.filter(politician=pol))

    def item_title(self, activity):
        # FIXME wrap in try
        return r_title.search(activity.payload).group(1)

    def item_link(self, activity):
        match = r_link.search(activity.payload)
        if match:
            return match.group(1)
        else:
            # FIXME include links in activity model?
            return ''

    def item_guid(self, activity):
        return activity.guid

    def item_description(self, activity):
        payload = r_excerpt.sub('<br><span style="display: block; border-left: 1px dotted #AAAAAA; margin-left: 2em; padding-left: 1em; font-style: italic; margin-top: 5px;">', activity.payload_wrapped())
        payload = r_title.sub('', payload)
        return payload

    def item_pubdate(self, activity):
        return datetime.datetime(activity.date.year, activity.date.month, activity.date.day)

class PoliticianTextAnalysisView(TextAnalysisView):

    expiry_days = 14

    def get_qs(self, request, pol_id=None, pol_slug=None):
        if pol_slug:
            pol = get_object_or_404(Politician, slug=pol_slug)
        else:
            pol = get_object_or_404(Politician, pk=pol_id)
        request.pol = pol
        return pol.get_text_analysis_qs()

    def get_analysis(self, request, **kwargs):
        analysis = super(PoliticianTextAnalysisView, self).get_analysis(request, **kwargs)
        word = analysis.top_word
        if word and word != request.pol.info().get('favourite_word'):
            request.pol.set_info('favourite_word', word)
        return analysis

analysis = PoliticianTextAnalysisView.as_view()   

########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin

from parliament.search.models import *

class IndexingTaskAdmin(admin.ModelAdmin):

    list_display = ['action', 'identifier', 'timestamp', ] #'content_object']
    list_filter = ['action', 'timestamp']

admin.site.register(IndexingTask, IndexingTaskAdmin)
########NEW FILE########
__FILENAME__ = index
from django.conf import settings
from django.db.models import signals

from haystack import indexes
from haystack.utils import get_identifier

class QueuedSearchIndex(indexes.SearchIndex):

    def _setup_save(self, model):
        signals.post_save.connect(self.enqueue_save, sender=model)

    def _setup_delete(self, model):
        signals.post_delete.connect(self.enqueue_delete, sender=model)

    def _teardown_save(self, model):
        signals.post_save.disconnect(self.enqueue_save, sender=model)

    def _teardown_delete(self, model):
        signals.post_delete.disconnect(self.enqueue_delete, sender=model)

    def enqueue_save(self, instance, **kwargs):
        return self.enqueue('update', instance)

    def enqueue_delete(self, instance, **kwargs):
        return self.enqueue('delete', instance)

    def enqueue(self, action, instance):
        from parliament.search.models import IndexingTask
        it = IndexingTask(
            action=action,
            identifier=get_identifier(instance)
        )
        if action == 'update':
            it.content_object = instance

        it.save()

if getattr(settings, 'PARLIAMENT_AUTOUPDATE_SEARCH_INDEXES', False):
    SearchIndex = indexes.RealTimeSearchIndex
elif getattr(settings, 'PARLIAMENT_QUEUE_SEARCH_INDEXING', False):
    SearchIndex = QueuedSearchIndex
else:
    SearchIndex = indexes.SearchIndex
########NEW FILE########
__FILENAME__ = consume_indexing_queue
import itertools
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from haystack import site
import pysolr

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs any queued-up search indexing tasks."

    def handle(self, **options):

        from parliament.search.models import IndexingTask

        delete_tasks = list(
            IndexingTask.objects.filter(action='delete')
        )

        update_tasks = list(
            IndexingTask.objects.filter(action='update').prefetch_related('content_object')
        )

        solr = pysolr.Solr(settings.HAYSTACK_SOLR_URL, timeout=600)

        if update_tasks:
            update_objs = [t.content_object for t in update_tasks if t.content_object]

            update_objs.sort(key=lambda o: o.__class__.__name__)
            for cls, objs in itertools.groupby(update_objs, lambda o: o.__class__):
                logger.debug("Indexing %s" % cls)
                index = site.get_index(cls)
                prepared_objs = [index.prepare(o) for o in objs]
                solr.add(prepared_objs)

            IndexingTask.objects.filter(id__in=[t.id for t in update_tasks]).delete()

        if delete_tasks:
            for dt in delete_tasks:
                print "Deleting %s" % dt.identifier
                solr.delete(id=dt.identifier, commit=False)
            solr.commit()

            IndexingTask.objects.filter(id__in=[t.id for t in delete_tasks]).delete()





########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'IndexingTask'
        db.create_table('search_indexingtask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
        ))
        db.send_create_signal('search', ['IndexingTask'])


    def backwards(self, orm):
        
        # Deleting model 'IndexingTask'
        db.delete_table('search_indexingtask')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'search.indexingtask': {
            'Meta': {'object_name': 'IndexingTask'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        }
    }

    complete_apps = ['search']

########NEW FILE########
__FILENAME__ = models
import datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

class IndexingTask(models.Model):

    action = models.CharField(max_length=10)
    identifier = models.CharField(max_length=100)

    timestamp = models.DateTimeField(default=datetime.datetime.now)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.CharField(max_length=20, blank=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u'%s %s' % (self.action, self.identifier)
########NEW FILE########
__FILENAME__ = solr
"""Search tools that interface with Solr."""

import datetime
import re

from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

import pysolr

from parliament.core.utils import memoize_property
from parliament.search.utils import BaseSearchQuery

r_hl = re.compile(r'~(/?)hl~')
def autohighlight(results):
    """Puts in <em> for highlighted snippets."""
    if not hasattr(results, 'highlighting'):
        return results
    for doc in results.docs:
        for datefield in ('date', 'time'):
            if datefield in doc:
                doc[datefield] = datetime.datetime.strptime(
                    doc[datefield], "%Y-%m-%dT%H:%M:%SZ")
        if doc['id'] in results.highlighting:
            for (field, val) in results.highlighting[doc['id']].items():
                if 'politician' not in doc['id']:
                    # GIANT HACK: in the current search schema, politician results are pre-escaped
                    val = escape(val[0])
                else:
                    val = val[0]
                if doc.get(field):
                    # If the text field is already there for the document, rename it full_text
                    doc['full_' + field] = doc[field]
                doc[field] = mark_safe(r_hl.sub(r'<\1em>', val))
    return results

solr = pysolr.Solr(settings.HAYSTACK_SOLR_URL)


class SearchQuery(BaseSearchQuery):
    """Converts a user search query into Solr's language, and
    gets the results from Solr."""

    ALLOWABLE_OPTIONS = {
        'sort': ['score desc', 'date asc', 'date desc'],
    }

    ALLOWABLE_FILTERS = {
        'Party': 'party',
        'Province': 'province',
        'Person': 'politician',
        'MP': 'politician_id',
        'Witness': 'who_hocid',
        'Committee': 'committee_slug',
        'Date': 'date',
        'Type': 'type',
        'Document': 'doc_url'
    }

    def __init__(self, query, start=0, limit=15, user_params={},
            facet=False, full_text=False, solr_params={}):
        super(SearchQuery, self).__init__(query)
        self.start = start  # What offset to start from
        self.limit = limit  # How many results to return
        self.user_params = user_params  # request.GET, basically
        self.facet = facet  # Enable faceting?
        self.full_text = full_text
        self.extra_solr_params = solr_params

    def get_solr_query(self):
        searchparams = {
            'start': self.start,
            'rows': self.limit
        }
        if self.facet:
            searchparams['facet'] = 'true'
        if self.full_text:
            searchparams['fl'] = '*'

        solr_filters = []
        filter_types = set()

        for filter_name, filter_value in self.filters.items():
            filter_name = self.ALLOWABLE_FILTERS[filter_name]

            if filter_name == 'date':
                match = re.search(r'^(\d{4})-(\d\d?) to (\d{4})-(\d\d?)', filter_value)
                if not match:
                    return ''
                (fromyear, frommonth, toyear, tomonth) = [int(x) for x in match.groups()]
                tomonth += 1
                if tomonth == 13:
                    tomonth = 1
                    toyear += 1
                filter_value = '[{0:02}-{1:02}-01T00:01:01.000Z TO {2:02}-{3:02}-01T00:01:01.000Z]'.format(fromyear, frommonth, toyear, tomonth)

            elif filter_name == 'type':
                filter_name = 'doctype'

            if ' ' in filter_value and filter_name != 'date':
                filter_value = u'"%s"' % filter_value

            filter_value = filter_value.replace('/', r'\/')

            if filter_name in ['who_hocid', 'politician_id', 'politician']:
                filter_tag = 'fperson'
            elif filter_name == 'doc_url':
                filter_tag = 'fdate'
            else:
                filter_tag = 'f' + filter_name

            filter_types.add(filter_name)
            solr_filters.append(u'{!tag=%s}%s:%s' % (filter_tag, filter_name, filter_value))

        if solr_filters and not self.bare_query:
            solr_query = '*:*'
        else:
            solr_query = self.bare_query

        if solr_filters:
            searchparams['fq'] = solr_filters

        self.committees_only = 'Committee' in self.filters or self.filters.get('Type') == 'committee'
        self.committees_maybe = 'Type' not in self.filters or self.committees_only

        if self.facet:
            if self.committees_only:
                searchparams['facet.range.start'] = '2006-01-01T00:00:00.000Z'
            else:
                searchparams['facet.range.start'] = '1994-01-01T00:00:00.000Z'

        searchparams.update(self.validated_user_params)
        searchparams.update(self.extra_solr_params)

        # Our version of pysolr doesn't like Unicode
        if searchparams.get('fq'):
            searchparams['fq'] = map(lambda f: f.encode('utf-8'), searchparams['fq'])

        return (solr_query, searchparams)

    @property
    @memoize_property
    def validated_user_params(self):
        p = {}
        for opt in self.ALLOWABLE_OPTIONS:
            if opt in self.user_params and self.user_params[opt] in self.ALLOWABLE_OPTIONS[opt]:
                p[opt] = self.user_params[opt]
        return p

    @property
    def solr_results(self):
        if not getattr(self, '_results', None):
            bare_query, searchparams = self.get_solr_query()
            self._results = autohighlight(solr.search(bare_query, **searchparams))
        return self._results

    @property
    def hits(self):
        return self.solr_results.hits

    @property
    def facet_fields(self):
        return self.solr_results.facets.get('facet_fields')

    @property
    def documents(self):
        return self.solr_results.docs

    @property
    @memoize_property
    def date_counts(self):
        counts = []
        if self.facet and 'facet_ranges' in self.solr_results.facets:
            datefacets = self.solr_results.facets['facet_ranges']['date']['counts']
            counts = [
                (int(datefacets[i][:4]), datefacets[i+1])
                for i in range(0, len(datefacets), 2)
            ]

            if self.committees_only:
                # If we're searching only committees, we by definition won't have
                # results before 1994, so let's take them off of the graph.
                counts = filter(lambda c: c[0] >= 2006, counts)
        return counts

    @property
    def discontinuity(self):
        if self.solr_results and self.committees_maybe and not self.committees_only:
            return 2006
        return None

########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import patterns, include, url

from parliament.search.views import SearchFeed

urlpatterns = patterns('parliament.search.views',
    url(r'^$', 'search', name='search'),
    url(r'^feed/$', SearchFeed(), name='search_feed'),
)
########NEW FILE########
__FILENAME__ = utils
from collections import namedtuple
import math
import re
import urllib

from django.utils.safestring import mark_safe

_FakePaginator = namedtuple('FakePaginator', 'num_pages count')

class SearchPaginator(object):
    """A dumb imitation of the Django Paginator."""

    def __init__(self, object_list, hits, pagenum, perpage):
        self.object_list = object_list
        self.hits = hits
        self.num_pages = int(math.ceil(float(self.hits) / float(perpage)))
        self.number = pagenum
        self.start_index = ((pagenum - 1) * perpage) + 1
        self.end_index = self.start_index + perpage - 1
        if self.end_index > self.hits:
            self.end_index = self.hits

    @property
    def paginator(self):
        return _FakePaginator(self.num_pages, self.hits)

    def has_previous(self):
        return self.number > 1

    def has_next(self):
        return self.number < self.num_pages

    def previous_page_number(self):
        return self.number - 1

    def next_page_number(self):
        return self.number + 1


class BaseSearchQuery(object):

    ALLOWABLE_FILTERS = {}

    def __init__(self, query):
        self.raw_query = query
        self.filters = {}

        def extract_filter(match):
            self.filters[match.group(1)] = match.group(2)
            return ''

        self.bare_query = re.sub(r'(%s): "([^"]+)"' % '|'.join(self.ALLOWABLE_FILTERS),
            extract_filter, self.raw_query)
        self.bare_query = re.sub(r'\s\s+', ' ', self.bare_query).strip()

    @property
    def normalized_query(self):
        q = (self.bare_query
            + (' ' if self.bare_query and self.filters else '')
            + ' '.join((
                u'%s: "%s"' % (key, self.filters[key])
                for key in sorted(self.filters.keys())
        )))
        return q.strip()

########NEW FILE########
__FILENAME__ = views
#coding: utf-8

import re
import urllib

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template import loader, RequestContext
from django.utils.safestring import mark_safe
from django.views.decorators.vary import vary_on_headers

from parliament.core.models import Politician, Session, ElectedMember, Riding, InternalXref
from parliament.core.utils import postcode_to_edid
from parliament.core.views import closed, flatpage_response
from parliament.search.solr import SearchQuery
from parliament.search.utils import SearchPaginator
from parliament.utils.views import adaptive_redirect

PER_PAGE = getattr(settings, 'SEARCH_RESULTS_PER_PAGE', 15)


@vary_on_headers('X-Requested-With')
def search(request):
    if getattr(settings, 'PARLIAMENT_SEARCH_CLOSED', False):
        return closed(request, message=settings.PARLIAMENT_SEARCH_CLOSED)

    if 'q' in request.GET and request.GET['q']:
        if not 'page' in request.GET:
            resp = try_postcode_first(request)
            if resp: return resp
            if not request.is_ajax():
                resp = try_politician_first(request)
                if resp: return resp

        query = request.GET['q'].strip()
        if request.GET.get('prepend'):
            query = request.GET['prepend'] + u' ' + query
        if 'page' in request.GET:
            try:
                pagenum = int(request.GET['page'])
            except ValueError:
                pagenum = 1
        else:
            pagenum = 1
        startfrom = (pagenum - 1) * PER_PAGE

        query_obj = SearchQuery(query,
            start=startfrom,
            limit=PER_PAGE,
            user_params=request.GET,
            facet=True)

        ctx = dict(
            query=query,
            pagenum=pagenum,
            discontinuity=query_obj.discontinuity,
            chart_years=[c[0] for c in query_obj.date_counts],
            chart_values=[c[1] for c in query_obj.date_counts],
            facet_fields=query_obj.facet_fields,
            page=SearchPaginator(query_obj.documents, query_obj.hits,
                pagenum, PER_PAGE)
        )

        ctx.update(query_obj.validated_user_params)

    else:
        ctx = {
            'query': '',
            'page': None,
        }
    c = RequestContext(request, ctx)
    if request.is_ajax():
        t = loader.get_template("search/search_results.inc")
    else:
        t = loader.get_template("search/search.html")
    return HttpResponse(t.render(c))


r_postcode = re.compile(r'^\s*([A-Z][0-9][A-Z])\s*([0-9][A-Z][0-9])\s*$')
def try_postcode_first(request):
    match = r_postcode.search(request.GET['q'].upper())
    if match:
        postcode = match.group(1) + " " + match.group(2)
        try:
            x = InternalXref.objects.filter(schema='edid_postcode', text_value=postcode)[0]
            edid = x.target_id
        except IndexError:
            edid = postcode_to_edid(postcode)
            if edid:
                InternalXref.objects.get_or_create(schema='edid_postcode', text_value=postcode, target_id=edid)
        if edid:
            try:
                member = ElectedMember.objects.get(end_date__isnull=True, riding__edid=edid)
                return adaptive_redirect(request, member.politician.get_absolute_url())
            except ElectedMember.DoesNotExist:
                return flatpage_response(request, u"Ain’t nobody lookin’ out for you",
                    mark_safe(u"""It looks like that postal code is in the riding of %s. There is no current
                    Member of Parliament for that riding. By law, a byelection must be called within
                    180 days of a resignation causing a vacancy. (If you think we’ve got our facts
                    wrong about your riding or MP, please send an <a class='maillink'>e-mail</a>.)"""
                    % Riding.objects.get(edid=edid).dashed_name))
            except ElectedMember.MultipleObjectsReturned:
                raise Exception("Too many MPs for postcode %s" % postcode)
    return False


def try_politician_first(request):
    try:
        pol = Politician.objects.get_by_name(request.GET['q'].strip(), session=Session.objects.current(), saveAlternate=False, strictMatch=True)
        if pol:
            return HttpResponseRedirect(pol.get_absolute_url())
    except:
        return None


class SearchFeed(Feed):

    def get_object(self, request):
        if 'q' not in request.GET:
            raise Http404
        return request.GET['q']

    def title(self, query):
        return '"%s" | openparliament.ca' % query

    def link(self, query):
        return "http://openparliament.ca/search/?" + urllib.urlencode({'q': query.encode('utf8'), 'sort': 'date desc'})

    def description(self, query):
        return "From openparliament.ca, search results for '%s'" % query

    def items(self, query):
        query_obj = SearchQuery(query, user_params={'sort': 'date desc'})
        return filter(lambda item: item['django_ct'] == 'hansards.statement',
            query_obj.documents)

    def item_title(self, item):
        return "%s / %s" % (item['topic'], item['politician'])

    def item_link(self, item):
        return item['url']

    def item_description(self, item):
        return item['text']

    def item_pubdate(self, item):
        return item['date']

########NEW FILE########
__FILENAME__ = search_sites
import haystack
haystack.autodiscover()

########NEW FILE########
__FILENAME__ = admin
from django.contrib import admin
from parliament.text_analysis.models import TextAnalysis

admin.site.register(TextAnalysis)
########NEW FILE########
__FILENAME__ = analyze
from parliament.text_analysis.corpora import load_background_model
from parliament.text_analysis.frequencymodel import FrequencyModel, STOPWORDS

def analyze_statements(statements, corpus_name):
    results = []
    ngram_lengths = [
        {
            'length': 3,
            'max_count': 3,
        },
        {
            'length': 2,
            'max_count': 8,
        },
        {
            'length': 1,
            'max_count': 20,
        }
    ]
    if sum(s.wordcount for s in statements) < 1000:
        return None
    seen = set(STOPWORDS)
    for opts in ngram_lengths:
        bg = load_background_model(corpus_name, opts['length'])
        model = FrequencyModel.from_statement_qs(statements, opts['length']).diff(bg)
        top = iter(model.most_common(50))
        count = 0
        for item in top:
            if count >= opts['max_count']:
                continue
            words = item[0].split(' ')
            #if sum(word in seen for word in words) / float(len(words)) < 0.6:
            if words[0] not in seen and words[-1] not in seen:
                seen.update(words)
                results.append({
                    "text": item[0],
                    "score": item[1] * 1000
                    #"size": _log_scale(item[1], opts['range'])
                })
    #results.sort(key=lambda r: r['size'], reverse=True)
    return results;


########NEW FILE########
__FILENAME__ = corpora
import datetime
import os.path
import cPickle as pickle
import re

from django.conf import settings

from parliament.text_analysis.frequencymodel import FrequencyModel

def _get_background_model_path(corpus_name, n):
    # Sanitize corpus_name, since it might be user input
    corpus_name = re.sub(r'[^a-z0-9-]', '', corpus_name) 
    return os.path.join(settings.PARLIAMENT_LANGUAGE_MODEL_PATH, '%s.%dgram' % (corpus_name, n))

def load_background_model(corpus_name, n):
    with open(_get_background_model_path(corpus_name, n), 'rb') as f:
        return pickle.load(f)

def generate_background_models(corpus_name, statements, ngram_lengths=[1,2,3]):
    for n in ngram_lengths:
        bg = FrequencyModel.from_statement_qs(statements, ngram=n, min_count=5 if n < 3 else 3)
        with open(_get_background_model_path(corpus_name, n), 'wb') as f:
            pickle.dump(bg, f, pickle.HIGHEST_PROTOCOL)

def generate_for_debates():
    from parliament.hansards.models import Statement
    since = datetime.datetime.now() - datetime.timedelta(days=365)
    qs = Statement.objects.filter(document__document_type='D', time__gte=since)
    generate_background_models('debates', qs)
    qs = Statement.objects.filter(time__gte=since)
    generate_background_models('default', qs)

def generate_for_old_debates():
    from parliament.hansards.models import Statement
    for year in range(1994, datetime.date.today().year):
        qs = Statement.objects.filter(document__document_type='D', time__year=year)
        generate_background_models('debates-%d' % year, qs)

def generate_for_committees():
    from parliament.hansards.models import Statement
    from parliament.committees.models import Committee, CommitteeMeeting
    from parliament.core.models import Session
    for committee in Committee.objects.filter(sessions=Session.objects.current()):
        since = datetime.date.today() - datetime.timedelta(days=365 * 3)
        document_ids = CommitteeMeeting.objects.filter(committee=committee, date__gte=since).values_list(
            'evidence_id', flat=True)
        qs = Statement.objects.filter(document__in=document_ids)
        generate_background_models(committee.slug, qs)

def generate_all():
    generate_for_debates()
    generate_for_committees()
    generate_for_old_debates()

########NEW FILE########
__FILENAME__ = frequencymodel
#coding: utf-8

from collections import defaultdict
from heapq import nlargest
import itertools
from operator import itemgetter
import re

STOPWORDS = frozenset(["i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these",
    "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can",
    "will", "just", "don", "should", "now", # this is the nltk stopwords list
    "it's", "we're", "we'll", "they're", "can't", "won't", "isn't", "don't", "he's",
    "she's", "i'm", "aren't", "government", "house", 'committee', 'would', 'speaker',
    'motion', 'mr', 'mrs', 'ms', 'member', 'minister', 'canada', 'members', 'time',
    'prime', 'one', 'parliament', 'us', 'bill', 'act', 'like', 'canadians', 'people',
    'said', 'want', 'could', 'issue', 'today', 'hon', 'order', 'party', 'canadian',
    'think', 'also', 'new', 'get', 'many', 'say', 'look', 'country', 'legislation',
    'law', 'department', 'two', 'one', 'day', 'days', 'madam', 'must', "that's", "okay",
    "thank", "really", "much", "there's", 'yes', 'no'
])


r_punctuation = re.compile(r"[^\s\w0-9'’—-]", re.UNICODE)
r_whitespace = re.compile(r'[\s—]+')

def text_token_iterator(text):
    text = r_punctuation.sub('', text.lower())
    for word in r_whitespace.split(text):
        yield word

def statements_token_iterator(statements, statement_separator=None):
    for statement in statements:
        for x in text_token_iterator(statement.text_plain()):
            yield x
        if statement_separator is not None:
            yield statement_separator

def ngram_iterator(tokens, n=2):
    sub_iterators = itertools.tee(tokens, n)
    for i, iterator in enumerate(sub_iterators[1:]):
        for x in xrange(i + 1):
            # Advance the iterator i+1 times
            next(iterator, None)
    for words in itertools.izip(*sub_iterators):
        yield ' '.join(words)


class FrequencyModel(dict):
    """
    Given an iterable of strings, constructs an object mapping each string
    to the probability that a randomly chosen string will be it (that is, 
    # of occurences of string / # total number of items).
    """

    def __init__(self, items, min_count=1):
        counts = defaultdict(int)
        total_count = 0;
        for item in items:
            if len(item) > 2 and '/' not in item:
                counts[item] += 1
                total_count += 1
        self.count = total_count
        total_count = float(total_count)
        self.update(
            (k, v / total_count) for k, v in counts.iteritems() if v >= min_count
        )

    def __missing__(self, key):
        return float()

    def diff(self, other):
        """
        Given another FrequencyModel, returns a FrequencyDiffResult containing the difference
        between the probability of a given word appears in this FrequencyModel vs the other
        background model.
        """
        r = FrequencyDiffResult()
        for k, v in self.iteritems():
            if k not in STOPWORDS:
                r[k] = self[k] - other[k]
        return r

    def most_common(self, n=None):    
        if n is None:
            return sorted(self.iteritems(), key=itemgetter(1), reverse=True)
        return nlargest(n, self.iteritems(), key=itemgetter(1))

    @classmethod
    def from_statement_qs(cls, qs, ngram=1, min_count=1):
        it = statements_token_iterator(qs, statement_separator='/')
        if ngram > 1:
            it = ngram_iterator(it, ngram)
        return cls(it, min_count=min_count)

class FrequencyDiffResult(dict):

    def __missing__(self, key):
        return float()

    def most_common(self, n=10):
        return nlargest(n, self.iteritems(), key=itemgetter(1))

class WordCounter(dict):
    
    def __init__(self, stopwords=STOPWORDS):
        self.stopwords = stopwords
        super(WordCounter, self).__init__(self)
    
    def __missing__(self, key):
        return 0
        
    def __setitem__(self, key, value):
        if key not in self.stopwords:
            super(WordCounter, self).__setitem__(key, value)

    def most_common(self, n=None):    
        if n is None:
            return sorted(self.iteritems(), key=itemgetter(1), reverse=True)
        return nlargest(n, self.iteritems(), key=itemgetter(1))
        
class WordAndAttributeCounter(object):
    
    def __init__(self, stopwords=STOPWORDS):
        self.counter = defaultdict(WordAttributeCount)
        self.stopwords = stopwords
        
    def add(self, word, attribute):
        if word not in self.stopwords and len(word) > 2:
            self.counter[word].add(attribute)
        
    def most_common(self, n=None):    
        if n is None:
            return sorted(self.counter.iteritems(), key=lambda x: x[1].count, reverse=True)
        return nlargest(n, self.counter.iteritems(), key=lambda x: x[1].count)
        
class WordAttributeCount(object):
    
    __slots__ = ('count', 'attributes')
    
    def __init__(self):
        self.attributes = defaultdict(int)
        self.count = 0
        
    def add(self, attribute):
        self.attributes[attribute] += 1
        self.count += 1
        
    def winning_attribute(self):
        return nlargest(1, self.attributes.iteritems(), key=itemgetter(1))[0][0]


########NEW FILE########
__FILENAME__ = 0001_initial
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'TextAnalysis'
        db.create_table(u'text_analysis_textanalysis', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=150, db_index=True)),
            ('lang', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('expires', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('probability_data_json', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'text_analysis', ['TextAnalysis'])

        # Adding unique constraint on 'TextAnalysis', fields ['key', 'lang']
        db.create_unique(u'text_analysis_textanalysis', ['key', 'lang'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TextAnalysis', fields ['key', 'lang']
        db.delete_unique(u'text_analysis_textanalysis', ['key', 'lang'])

        # Deleting model 'TextAnalysis'
        db.delete_table(u'text_analysis_textanalysis')


    models = {
        u'text_analysis.textanalysis': {
            'Meta': {'unique_together': "[('key', 'lang')]", 'object_name': 'TextAnalysis'},
            'expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_index': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'probability_data_json': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        }
    }

    complete_apps = ['text_analysis']

########NEW FILE########
__FILENAME__ = models
import datetime
import json
from operator import itemgetter

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.template.defaultfilters import escapejs
from django.utils.safestring import mark_safe

from parliament.text_analysis.analyze import analyze_statements

class TextAnalysisManager(models.Manager):

    def get_or_create_from_statements(self, key, qs, corpus_name,
            lang=settings.LANGUAGE_CODE, always_update=False, expiry_days=None):
        try:
            analysis = self.get(key=key, lang=lang)
            if analysis.expired:
                analysis.delete()
                analysis = TextAnalysis(key=key, lang=lang)
        except ObjectDoesNotExist:
            analysis = TextAnalysis(key=key, lang=lang)
        if always_update or not analysis.probability_data_json:
            # Set a cache value so we don't have multiple server process trying
            # to do the same calculations at the same time
            cache_key = 'text_analysis:' + key
            if (not cache.get(cache_key)) and qs.exists():
                cache.set(cache_key, True, 60)
                analysis.probability_data_json = json.dumps(analyze_statements(qs, corpus_name))
                if expiry_days:
                    analysis.expires = datetime.datetime.now() + datetime.timedelta(days=expiry_days)
                analysis.save()
        return analysis

    def create_from_statements(self, key, qs, corpus_name, lang=settings.LANGUAGE_CODE):
        return self.get_or_create_from_statements(key, qs, corpus_name, lang, always_update=True)

    def get_wordcloud_js(self, key, lang=settings.LANGUAGE_CODE):
        if getattr(settings, 'PARLIAMENT_DISABLE_WORDCLOUD', False): return ''
        data = self.filter(key=key, lang=lang).values_list('probability_data_json', 'expires')
        if data and (data[0][1] is None or data[0][1] > datetime.datetime.now()):
            js = 'OP.wordcloud.drawSVG(%s, wordcloud_opts);' % data[0][0];
        else:
            js = '$.getJSON("%s", function(data) { if (data) OP.wordcloud.drawSVG(data, wordcloud_opts); });' % escapejs(key)
        return mark_safe(js)

class TextAnalysis(models.Model):

    key = models.CharField(max_length=150, db_index=True, help_text="A URL to a view that calculates this object")
    lang = models.CharField(max_length=2)

    updated = models.DateTimeField(default=datetime.datetime.now)
    expires = models.DateTimeField(blank=True, null=True)

    probability_data_json = models.TextField()

    objects = TextAnalysisManager()

    class Meta:
        unique_together = [('key', 'lang')]
        verbose_name_plural = 'Text analyses'

    def __unicode__(self):
        return "%s (%s)" % (self.key, self.lang)

    @property
    def expired(self):
        return self.expires and self.expires < datetime.datetime.now()

    @property
    def probability_data(self):
        return json.loads(self.probability_data_json) if self.probability_data_json else None

    @property
    def top_word(self):
        d = self.probability_data
        if d is None: return
        onegrams = (w for w in d if w['text'].count(' ') == 0)
        return max(onegrams, key=itemgetter('score'))['text']

########NEW FILE########
__FILENAME__ = views
from django.http import HttpResponse, Http404
from django.views.generic import View

from parliament.text_analysis.models import TextAnalysis

class TextAnalysisView(View):
    """Returns JSON text analysis data. Subclasses must define get_qs."""

    corpus_name = 'default'
    expiry_days = None

    def get(self, request, **kwargs):
        try:
            analysis = self.get_analysis(request, **kwargs)
        except IOError:
            raise Http404
        return HttpResponse(analysis.probability_data_json, content_type='application/json')

    def get_key(self, request, **kwargs):
        return request.path

    def get_qs(self, request, **kwargs):
        raise NotImplementedError

    def get_corpus_name(self, request, **kwargs):
        return self.corpus_name

    def get_analysis(self, request, **kwargs):
        return TextAnalysis.objects.get_or_create_from_statements(
            key=self.get_key(request, **kwargs),
            qs=self.get_qs(request, **kwargs),
            corpus_name=self.get_corpus_name(request, **kwargs),
            expiry_days=self.expiry_days
        )
########NEW FILE########
__FILENAME__ = urls
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

from parliament.core.sitemap import sitemaps
from parliament.core.views import SiteNewsFeed

urlpatterns = patterns('',
    (r'^search/', include('parliament.search.urls')),
    (r'^debates/', include('parliament.hansards.urls')),
    url(r'^documents/(?P<document_id>\d+)/$', 'parliament.hansards.views.document_redirect', name='document_redirect'),
    url(r'^documents/(?P<document_id>\d+)/(?P<slug>[a-zA-Z0-9-]+)/$', 'parliament.hansards.views.document_redirect', name='document_redirect'),
    (r'^politicians/', include('parliament.politicians.urls')),
    (r'^bills/', include('parliament.bills.urls')),
    (r'^votes/', include('parliament.bills.vote_urls')),
    (r'^alerts/', include('parliament.alerts.urls')),
    (r'^committees/', include('parliament.committees.urls')),
    url(r'^speeches/', 'parliament.hansards.views.speeches', name='speeches'),
    #url(r'^about/$', 'django.views.generic.simple.direct_to_template', {'template': 'about/about.html'}, name='about'),
    url(r'^api/$', 'parliament.core.api.docs'),
    (r'^api/', include('parliament.api.urls')),
    (r'^accounts/', include('parliament.accounts.urls')),
    (r'^$', 'parliament.core.views.home'),
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    url(r'^sitenews/rss/$', SiteNewsFeed(), name='sitenews_feed'),
    (r'^robots\.txt$', 'parliament.core.api.no_robots'),
    (r'', include('parliament.legacy_urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^admin/', include(admin.site.urls)),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': settings.MEDIA_ROOT}),
    )

if getattr(settings, 'ADMIN_URL', False):
    urlpatterns += patterns('',
        (settings.ADMIN_URL, include(admin.site.urls)),
        (r'^memcached-status/$', 'parliament.core.maint.memcached_status'),
    )
    
if getattr(settings, 'PARLIAMENT_SITE_CLOSED', False):
    urlpatterns = patterns('',
        (r'.*', 'parliament.core.views.closed')
    ) + urlpatterns
    
if getattr(settings, 'EXTRA_URLS', False):
    urlpatterns += patterns('', *settings.EXTRA_URLS)
    
handler500 = 'parliament.core.errors.server_error'
########NEW FILE########
__FILENAME__ = views
import json
import re

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View


class JSONView(View):
    """Base view that serializes responses as JSON."""

    # Subclasses: set this to True to allow JSONP (cross-domain) requests
    allow_jsonp = False

    wrap = True

    def __init__(self):
        super(JSONView, self).__init__()
        self.content_type = 'application/json'

    def dispatch(self, request, *args, **kwargs):
        result = super(JSONView, self).dispatch(request, *args, **kwargs)
        indent_response = 4 if request.GET.get('indent') else None

        if isinstance(result, HttpResponse):
            return result
        resp = HttpResponse(content_type=self.content_type)
        callback = ''
        if self.allow_jsonp and 'callback' in request.GET:
            callback = re.sub(r'[^a-zA-Z0-9_]', '', request.GET['callback'])
            resp.write(callback + '(')
        if self.wrap:
            result = {'status': 'ok', 'content': result}
        json.dump(result, resp, indent=indent_response)
        if callback:
            resp.write(');')

        return resp

    def redirect(self, url):
        return AjaxRedirectResponse(url)


class AjaxRedirectResponse(HttpResponse):

    def __init__(self, url, status_code=403):
        super(AjaxRedirectResponse, self).__init__(
            '<script>window.location.href = "%s";</script>' % url,
            content_type='text/html'
        )
        self.status_code = status_code
        self['X-OP-Redirect'] = url


def adaptive_redirect(request, url):
    if request.is_ajax():
        return AjaxRedirectResponse(url)
    return HttpResponseRedirect(url)

########NEW FILE########
__FILENAME__ = wsgi
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parliament.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)

########NEW FILE########