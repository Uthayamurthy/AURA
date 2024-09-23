'''
Example Usage of Beacon Manager.
Eddybeacon Style Beacon but with custom text !
'''

from BeaconMgr import Beacon
from time import sleep

t = int(input('Enter Broadcast Duration (in seconds) : '))

uuid = 'feaa'
mybeacon = Beacon('feaa', debug=True)
mybeacon.add_data('16feaa', 'raw') # Add eddybeacon common header
text = input('Enter text to broadcast : ')
mybeacon.add_data(text, 'unicode-text')
mybeacon.broadcast()
sleep(t)
mybeacon.stop_broadcast()