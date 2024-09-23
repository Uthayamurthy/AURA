# Prototype 2
## BeaconMgr Module 

> Note : Uses -> https://github.com/BOJIT/btmgmt Library. The library is a wrapper around the bluez development c library. Updated 3 years ago ... But works for our purpose !!

### How to test ?

- Install Dependencies mentioned in btmgmt readme page ...
- Create a Virtual Environment :
```
sudo python3 -m venv bs_env
```
> Everything sudo, because it requires elevated permissions to run !!
- Run the script !
```
sudo bs_env/bin/python example.py
```

> Refer to **example.py** for usage. 

### Features:
- Payload in both "unicode-text" and "raw" hexadecimal bytes. "unicode-text" is automatically converted to hexadecimal bytes
- A Temporary Data buffer to which data can be added as many times as necessary until broadcast.
- No specific protocol
- Automatic Length checking ... If length is more than the maximum broacastable bytes, will throw error.
- Bells and Whistles like optional Debug Messages, Error Handling and lots of docstrings

