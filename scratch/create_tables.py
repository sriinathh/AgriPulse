import app
from backend.app.database.session import get_engine
from backend.app.models import Base
engine = get_engine()
Base.metadata.create_all(bind=engine)
print('Tables created')
