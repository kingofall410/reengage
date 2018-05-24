import sys
import logging

def write(count, total, suffix='', done=False):
    if total > 0:
        bar_len = 70
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 1)
        bar = '#' * filled_len + '-' * (bar_len - filled_len)

        sys.stdout.write('[%s] %s%s (%s/%s) ...%s\r' % (bar, percents, '%', count, total, suffix))
        sys.stdout.flush()

        if done:
            print()
            logging.info('[%s] %s%s (%s/%s) ...%s\r' % (bar, percents, '%', count, total, suffix))
