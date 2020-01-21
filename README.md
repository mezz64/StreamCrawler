# StreamCrawler

### Description
This is a simple script, developed on linux for python 3, to crawl through a m3u playlist file and run ffmpeg on each of the discovered streams for the purpose of capturing the stream characteristics (Video: Resolution, FPS, Bitrate - Audio: Type, Channels, Bitrate).

This is a work in progress and may break easily.  Watch the log to see what's going on.

### Requirements
* Python 3+ (No special libraries required)
* FFMPEG
* FFPROBE

### Usage
Basic, evaluate each stream in playlist for 60 seconds.
`python3 ./stream_crawl.py -i http://path_to_m3u -t 60 -o output.csv`

Groups, output unique groups in playlist.
`python3 ./stream_crawl.py -i http://path_to_m3u -g`

Filter, evaluate each stream in playlist that matches specified group for 60 seconds.
`python3 ./stream_crawl.py -i http://path_to_m3u -t 60 -o output.csv -f "Special Group"`


### Flags
* `-i` - Define path to input playlist (only works for web links at the moment)
* `-o` - Define output csv file path (ex. output.csv)
* `-t` - Duration to evaluate each stream in the playlist in seconds (ex. 60)
* `-g` - Parse unique groups in supplied playlist and output to the terminal.  This command does not analyze any streams.
* `-f` - Filter analyzed streams to those that match the specified group name. (ex. NEWS)
