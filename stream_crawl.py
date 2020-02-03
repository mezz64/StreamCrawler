"""
M3U Playlist Stream Crawler
"""
import os
import subprocess
import logging
import json
import sys
import getopt
import csv
import uuid
import requests
import time


_LOGGER = logging.getLogger(__name__)
logging.getLogger('chardet.charsetprober').setLevel(logging.INFO)
logging.basicConfig(filename='output.log', filemode='a', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


CONNECT_TIMEOUT = 30
STREAM_TIMEOUT = 15
FFMPEG_PATH = '/usr/bin/ffmpeg'
FFPROBE_PATH = '/usr/bin/ffprobe'

CSV_COLUMNS = ['Name', 'Group', 'Resolution', 'FPS',
               'Bitrate', 'Audio Type', 'Audio Channels',
               'Audio Bitrate', 'URL']

CHANSTATS = {}


def parse_playlist(url, gfilter):
    """Parse playlist url"""
    _LOGGER.info('Fetching playlist from: %s', url)
    try:
        response = requests.get(url, timeout=CONNECT_TIMEOUT)
    except (requests.exceptions.RequestException,
            requests.exceptions.ConnectionError) as err:
        _LOGGER.error('Unable to fetch playlist, error: %s', err)
        return

    if response.status_code != requests.codes.ok:
        # If we didn't receive 200, abort
        _LOGGER.debug('Unable to fetch playlist, error: %s', response.status_code)
        return

    response.content.decode('ISO-8859-1')
    playlist = response.text
    streams = playlist.split('#EXTINF')

    for strm in streams:
        try:
            name = strm.split('tvg-name', 1)[1].split('"')[1]
            path = strm.splitlines()[1]
            try:
                group = strm.split('group-title', 1)[1].split('"')[1]
            except IndexError:
                # No group indentified in list
                group = ""

            if gfilter is None:
                CHANSTATS[name] = {'path': path,
                                   'group': group}
            elif gfilter == group:
                CHANSTATS[name] = {'path': path,
                                   'group': group}
        except IndexError:
            pass


def capture_sample(url, length):
    """Capture sample of stream"""
    file_path = '{}.mp4'.format(str(uuid.uuid4()))

    cmd = ('{} -i {} '
           '-acodec copy -vcodec copy '
           '-user_agent "VLC/3.0.1" '
           '-t {} {}').format(FFMPEG_PATH, url, str(length), file_path)
    try:
        _LOGGER.info("Starting capture for: %s", file_path)
        result = subprocess.call(cmd, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 timeout=length+STREAM_TIMEOUT, shell=True)
    except subprocess.TimeoutExpired:
        result = -1

    if result == 0:
        _LOGGER.info("Stream captured for: " + url)

        cmd2 = [FFPROBE_PATH,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                file_path]

        result = subprocess.check_output(cmd2)
        try:
            json_out = json.loads(result.decode('UTF-8'))
        except TypeError:
            _LOGGER.error("Unable to parse ffprobe output: " + result)
            json_out = None
    else:
        _LOGGER.info("Stream unavailable for: " + url)
        json_out = None

    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except (OSError, PermissionError):
            time.sleep(1)
            try:
                os.remove(file_path)
            except (OSError, PermissionError) as err:
                _LOGGER.error("File removal error: " + str(err))

    return json_out


def write_to_csv(filename, chan):
    """Write current CHANSTATS to CSV"""
    stats = CHANSTATS[chan]
    with open(filename, mode='a', newline='') as channel_stats:
        chan_writer = csv.writer(channel_stats)
        try:
            chan_writer.writerow([chan,
                                  stats['group'],
                                  stats['resolution'],
                                  stats['fps'],
                                  stats['bitrate'],
                                  stats['atype'],
                                  stats['achan'],
                                  stats['abitrate'],
                                  stats['path']])
        except KeyError:
            chan_writer.writerow([chan,
                                  stats['group'],
                                  "N/A",
                                  "N/A",
                                  "N/A",
                                  "N/A",
                                  "N/A",
                                  "N/A",
                                  stats['path']])


def populate_stream_dict(chan, data):
    """Update stream dict with quality data"""
    video = False
    audio = False
    try:
        for strm in data['streams']:
            if strm['codec_type'] == 'video':
                video = True
                resolution = '{}x{}'.format(strm['width'], strm['height'])
                fps = strm['avg_frame_rate'].split('/')
                fps = round(float(fps[0]) / float(fps[1]), 2)
                bitrate = round(float(strm['bit_rate']) / 1000, 2)
                CHANSTATS[chan]['resolution'] = resolution
                CHANSTATS[chan]['fps'] = fps
                CHANSTATS[chan]['bitrate'] = bitrate

            elif strm['codec_type'] == 'audio':
                audio = True
                atype = strm['codec_name']
                achan = strm['channels']
                abitrate = round(float(strm['bit_rate']) / 1000, 2)
                CHANSTATS[chan]['atype'] = atype
                CHANSTATS[chan]['achan'] = achan
                CHANSTATS[chan]['abitrate'] = abitrate

        if video and audio:
            _LOGGER.info("Chan: %s - V: %s, %s, %s - A: %s, %s, %s",
                         chan, resolution, fps, bitrate, atype, achan, abitrate)
        return 0
    except (TypeError, KeyError):
        _LOGGER.info("Chan: %s - Not Available", chan)
        return 1


def unique_groups():
    """Identify unique groups in supplied playlist."""
    ugroup = []
    for chan, stats in CHANSTATS.items():
        if not stats['group'] in ugroup:
            ugroup.append(stats['group'])

    return ugroup


def main(argv):
    """Main function."""
    input_path = ''
    sample_length = 0
    output_csv = None
    groups_out = False
    group_filter = None

    # Handle inputs
    try:
        opts, args = getopt.getopt(argv, "hi:t:o:gf:")
    except getopt.GetoptError:
        print('stream_crawl.py -i <input_path> -t <sample_time> -o <output_csv>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('Some help should be written here...')
            sys.exit()
        elif opt in ("-i"):
            input_path = arg
        elif opt in ("-t"):
            sample_length = int(arg)
        elif opt in ("-o"):
            output_csv = arg
        elif opt == '-g':
            groups_out = True
        elif opt in ("-f"):
            group_filter = arg

    _LOGGER.info("Parsing %s with %s sec stream samples to %s.",
                 input_path, sample_length, output_csv)

    parse_playlist(input_path, group_filter)

    print('Ready to analyze {} streams.'.format(len(CHANSTATS)))

    if groups_out:
        print(unique_groups())
        sys.exit()

    if sample_length > 0:
        # Initialize CSV with column headers
        if output_csv:
            with open(output_csv, mode='w', newline='') as channel_stats:
                chan_writer = csv.writer(channel_stats)
                chan_writer.writerow(CSV_COLUMNS)

        for chan, stats in CHANSTATS.items():
            print('Initializing capture for ', chan)
            data = capture_sample(stats['path'], sample_length)
            upd = populate_stream_dict(chan, data)
            write_to_csv(output_csv, chan)

            if upd == 0:
                print('Stats captured for ', chan)
            else:
                print('Error capturing stats for ', chan)


if __name__ == '__main__':
    main(sys.argv[1:])
