#!/usr/bin/env python

import sys
import time
from datetime import datetime, timedelta
import MythTV

soon_default = timedelta(seconds = 600)
date_fmt_default = "%d/%m %H:%M"


def recordstate(backend = None):
    be = backend or MythTV.MythBE()

    recording = sorted(
        (recording
         for recording in [be.getCurrentRecording(recorder)
                           for recorder in 
                           set(be.getRecorderList()) \
                               - set(be.getFreeRecorderList())
                           ]
         if recording and recording['title']),
        key = lambda x: x['endtime'],
        reverse = True)
    upcoming = sorted(
        be.getUpcomingRecordings(),
        key = lambda x: x['starttime'])
    return (recording, upcoming)

def rtcwake(t):
    wakealarm = "/sys/class/rtc/rtc0/wakealarm"
    with open(wakealarm, "w") as out:
        out.write('0\n')
        out.flush()
        out.write(str(time.mktime(datetime.utctimetuple(t))))
        out.write('\n')
        out.flush()
def nowake(t):
    pass

def act((recordings, upcoming), soon_limit, setwake = None, date_fmt = None):
    if date_fmt is None:
        date_fmt = date_fmt_default
    if recordings:
        print ("REC  {recordings[0][endtime]:" 
               + date_fmt 
               + "}\n{recordings[0][title]}").format(**locals())
        return 1
    elif upcoming:
        nxt = upcoming[0]
        nxt_start = nxt['starttime']
        wake = nxt_start - soon_limit
        if setwake:
            setwake(wake)
        soon = nxt_start < datetime.now() + soon_limit
        cat = soon and "SOON" or "NEXT"
        print (
            "{cat}" + " "
            + "{upcoming[0].starttime:" + date_fmt +"}\n"
            + "{upcoming[0].title:s}").format(**locals())
        return soon and 2 or 0
    else:
        print "NO\nSCHEDULE"
        return 0

wake_methods = dict(
    (tag, { 'tag': tag, 'help': hlp, 'f': f })
    for tag, hlp, f in
    [
        ('none', '''Do set any wakeup''', nowake),
        ('rtc', '''Use /sys/class/rtc/rtc0/wakealarm''', rtcwake)
        ])

def main(args = None):
    import argparse
    parser = argparse.ArgumentParser(
        description='set wakeup for myth and print recording status',
    epilog = '''
wakemyth exits with values: 0: no recording soon, 1: currently recording, 2: will soon be recording
'''
    )
    parser.add_argument(
        '--wake', 
        help = 'set the wakemethod to use (default: %(default)s)',
        default = 'rtc',
        choices = wake_methods.keys()
        )
    parser.add_argument(
        '--soon-seconds',
        help = 'how many minutes away is "soon" (default: %(default)s)',
        default = soon_default.total_seconds())
    parser.add_argument(
        '--date-format',
        help = 'date format for recordings (default: %(default)s)',
        default = date_fmt_default)
    parsed = parser.parse_args(args)
    soon = timedelta(seconds = float(parsed.soon_seconds))
    state = recordstate()
    date_fmt = parsed.date_format
    return act(state, 
               soon_limit = soon, 
               setwake = wake_methods[parsed.wake]['f'],
               date_fmt = date_fmt)

if __name__ == '__main__':
    main()
