import logging

class TagSupportFilter(logging.Filter):
    """ This filter makes sure tags can be omitted in log messages """
    def filter(self, record):
        if hasattr(record, 'tag'):
            return True
        record.tag = ''
        return True
