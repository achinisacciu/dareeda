import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
from api.models.database import engine
from api.models import orm
from sqlalchemy import inspect
insp = inspect(engine)
if not insp.has_table('report_jobs'):
    orm.Base.metadata.create_all(bind=engine)
    print('Tabella report_jobs creata.')
else:
    print('Tabella report_jobs gia presente.')
