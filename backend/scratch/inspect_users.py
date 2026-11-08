import sqlalchemy as sa
from app.database.session import engine

def main():
    with engine.connect() as conn:
        rows = conn.execute(sa.text('SELECT id,email,hashed_password FROM users')).fetchall()
        print(rows)

if __name__ == '__main__':
    main()
