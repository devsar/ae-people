import logging
import datetime

from appengine_django.models import BaseModel
from google.appengine.ext import db

from users.models import Developer
from google.appengine.ext.deferred import deferred

class DeveloperStats(BaseModel):
    """
        Developer stats snapshot.
        Should be build one daily
    """
    timestamp = db.DateTimeProperty(auto_now_add=True)
    
    total = db.IntegerProperty(default=0)
    python = db.IntegerProperty(default=0)
    java = db.IntegerProperty(default=0)
    
    @classmethod
    def update_real(cls, timestamp, cursor=None, stats=None):
        """
            Real update
        """
        
        query = Developer.all()
        if cursor:
            query.with_cursor(cursor)
        
        if stats is None:
            stats = {
                'total': 0,
                'tags': {},
                'python': 0,
                'java': 0
            }
        
        devs = query.fetch(100)
        
        stats['total'] += len(devs)
        
        for dev in devs:
            if dev.python_sdk:
                stats['python'] += 1
            
            if dev.java_sdk:
                stats['java'] += 1
                
            for tag in dev.tags:
                stats['tags'][tag] = stats['tags'].get(tag, 0) + 1
            
        if len(devs) == 100:
            #continue
            deferred.defer(cls.update, timestamp=timestamp, cursor=query.cursor(), stats=stats)
        else:
            dev_stats = DeveloperStats(timestamp=timestamp,
                                        total = stats['total'],
                                        python = stats['python'],
                                        java = stats['java'])
            dev_stats.put()
            
            #Track the Top 100 tags
            tags = sorted(stats['tags'].iteritems(), key=lambda t: t[1], reverse=True)[:100]
            batch = [TagStats(developer_stats=dev_stats,
                              timestamp=timestamp, name=k, total=v, 
                              popularity=float(v)/stats['total']) 
                     for k, v in tags]
            db.put(batch)
        
        return None

    @classmethod
    def update(cls, timestamp=None, cursor=None, stats=None):
        """
        Make deferred call to update Developer stats
        """
        
        if timestamp is None:
            timestamp = datetime.datetime.now()
        deferred.defer(cls.update_real, timestamp, cursor, stats)


class TagStats(BaseModel):
    """
        Tag stats snapshot.
    """
    developer_stats = db.ReferenceProperty(DeveloperStats)
    timestamp = db.DateTimeProperty(auto_now_add=True)
    name = db.StringProperty()
    total = db.IntegerProperty(default=0)
    popularity = db.FloatProperty(default=0)

