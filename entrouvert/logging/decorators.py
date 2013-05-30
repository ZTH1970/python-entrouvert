import logging
import time
from functools import wraps

__all__ = [ 'timing' ]

class TimingDecorator(object):
    def __init__(self, *args_to_report, **kwargs):
        if kwargs.get('logger'):
            self.logger = logging.getLogger(kwargs.get('logger'))
        else:
            self.logger = logging.getLogger(__name__)
        self.args_to_report = args_to_report

    def __call__(self, func):
        if hasattr(func, '__module__'): # functions
            name = '{0}.{1}'.format(func.__name__, func.__module__)
        else: # methods
            name = '{0}.{1}.{2}'.format(func.__name__,
                    func.__objclass__.__name__, func.__objclass__.__module__)
        @wraps(func)
        def f(*args, **kwargs):
            print 'coin'
            a = []
            for i in self.args_to_report:
                a.append(args[i])
            a = unicode(a)
            entry = time.time()
            self.logger.debug('%(name)s args: %(args)s entry: %(entry)s', dict(
                name=name, args=a, entry=entry))
            try:
                result = func(*args, **kwargs)
            finally:
                exit = time.time()
                duration = exit - entry
                self.logger.debug('%(name)s args: %(args)s exit: %(exit)s duration: %(duration)s', dict(
                    name=name, args=a, exit=exit, duration=duration))
            return result
        return f

timing = TimingDecorator
