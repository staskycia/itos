from app.extensions import db, cache

class Setting(db.Model):
    __tablename__ = "settings"
    
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Boolean, nullable=False)
    
    @classmethod
    def _cache_key(cls, key):
        return f"setting:{key}"
    
    @classmethod
    def get(cls, key, default=False):
        cache_key = cls._cache_key(key)
        
        value = cache.get(cache_key)
        if value is not None:
            return value
        
        setting = cls.query.get(key)
        value = setting.value if setting else default
        
        cache.set(cache_key, value)
        return value
    
from sqlalchemy import event   
 
@event.listens_for(Setting, "after_insert")
@event.listens_for(Setting, "after_update")
@event.listens_for(Setting, "after_delete")
def invalidate_setting_cache(mapper, connection, target):
    cache.delete(f"setting:{target.key}")   