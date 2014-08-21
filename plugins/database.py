import psycopg2
import sys

DEFAULT_USER = 'infobot'
DEFAULT_DBNAME = 'infobot'

class Database(object):
    def __init__(self, **kwargs):
        for i in ['user', 'dbname']:
            if i not in kwargs.keys():
                kwargs[i] = getattr(sys.modules[__name__], "DEFAULT_" + i.upper())

        self.conn = psycopg2.connect(keepalives_idle=60, **kwargs)
        self.cursor = self.conn.cursor()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def execute(self, string, *args, commit=True):
        try:
            self.cursor.execute(string, *args)
        except:
            self.conn.rollback()
        else:
            if commit:
                self.conn.commit()
        return self

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

