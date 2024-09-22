# Prototype 1

> Note : Uses -> https://github.com/BOJIT/btmgmt Library. The library is a wrapper around the bluez development c library. Updated 3 years ago ... But works for our purpose !!

## How to run ?

- Install Dependencies mentioned in btmgmt readme page ...
- Create a Virtual Environment :
```
sudo python3 -m venv bs_env
```
> Everything sudo, because it requires elevated permissions to run !!
- Run the script !
```
sudo bs_env/bin/python test.py
```

## Features 
- Can both start and stop a broadcast !
- Can broadcast payload of any arbitary length !!

> From experimentation, Max payload length is 23 bytes ... 20 bytes for our data alone ... which means just 20 characters :( ... Anything more than that it doesn't broadcast anything at all ... Strangely no errors !

### Next Prototype Goal:
A more general module for broadcasts ...