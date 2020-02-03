# StreamCrawler

### Description
By popular demand, you can find a pre-built windows exe in this folder.  It was made with pyinstaller and tested on Windows 10.

This is a work in progress and may break easily.  Watch the log to see what's going on.

### Requirements
* FFMPEG.exe in the same directory as stream_crawl.exe
* FFPROBE in the same directory as stream_crawl.exe

### Usage
Basic, evaluate each stream in playlist for 60 seconds.
`stream_crawl.exe -i http://path_to_m3u -t 60 -o output.csv`

Groups, output unique groups in playlist.
`stream_crawl.exe -i http://path_to_m3u -g`

Filter, evaluate each stream in playlist that matches specified group for 60 seconds.
`stream_crawl.exe -i http://path_to_m3u -t 60 -o output.csv -f "Special Group"`
