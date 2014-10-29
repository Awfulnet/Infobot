import psycopg2
import sys
import traceback

DEFAULT_USER = 'infobot'
DEFAULT_DBNAME = 'infobot'

class Database(object):
    def __init__(self, **kwargs):
        for i in ['user', 'dbname']:
            if i not in kwargs.keys():
                kwargs[i] = getattr(sys.modules[__name__], "DEFAULT_" + i.upper())

        self.conn = psycopg2.connect(keepalives_idle=60, **kwargs)
        self.cursor = self.conn.cursor()
        self.rowcount = 0

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def execute(self, string, *args, commit=True):
        
        if args and type(args[0]) != tuple:
            args = list(args)
            args[0] = [args[0]]
        try:
            self.cursor.execute(string, *tuple(args))
        except psycopg2.IntegrityError:
            self.rowcount = 0
            self.conn.rollback()
        except:
            traceback.print_exc()
            self.rowcount = self.cursor.rowcount
            self.conn.rollback()
        else:
            self.rowcount = self.cursor.rowcount
            if commit:
                self.conn.commit()
        return self

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

