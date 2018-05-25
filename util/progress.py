import sys
import logging

def write(count, total, suffix='', done=False):

        bar_len = 70
        if total > 0:
            filled_len = int(round(bar_len * count / float(total)))
        else:
            filled_len = 0

        if total > 0:
            percents = round(100.0 * count / float(total), 1)
        else:
            percents = 0

        bar = '#' * filled_len + '-' * (bar_len - filled_len)

        sys.stdout.write('[%s] %s%s (%s/%s) ...%s\r' % (bar, percents if total > 0 else "-", '%', count, total if total > 0 else "-", suffix))
        sys.stdout.flush()

        if done:
            print()
            logging.info('[%s] %s%s (%s/%s) ...%s\r' % (bar, percents if total > 0 else "-", '%', count, total if total > 0 else "-", suffix))
