import btmgmt

class Beacon:
    def __init__(self, uuid, max_payload_length=23, debug=False):
        self.uuid = uuid
        self.max_payload_length = max_payload_length
        self.debug = debug
        self.data_buffer = '' # Save Data Temporarily till Broadcast
    
    def debug_msg(self, msg):
        '''
        Prints msg only if debug is enabled !
        '''
        if self.debug:
            print(msg)

    def broadcast(self):
        '''
        Broadcasts the data in buffer after prepending the length, uuid type and uuid of the broadcast.
        '''
        self.debug_msg('Starting Broadcast ...')
        length = len(self.data_buffer)//2 # Length in Bytes (Every two character in hex takes up a byte !!)
        payload = f'{length:02x}{self.data_buffer}' # Prepend the Length to payload
        self.debug_msg(f'Payload : {payload}\nLength: {length} Bytes')
        response = btmgmt.command_str('add-adv', '-u', 'FEAA', '-d', payload,  '-g',  '1')
        self.debug_msg(f'Broadcast Response : {response}')

    def stop_broadcast(self):
        '''
        Clears Broadcast and resets the data buffer
        '''
        self.debug_msg('Stopping Broadcast ...')
        self.data_buffer = ''
        response = btmgmt.command_str('clr-adv')
        self.debug_msg(f'Stop Broadcast Response : {response}')

    def add_data(self, data, type='unicode-text'):
        '''
        Adds data to the data buffer based on type.

        Parameters
        ----------
        data : str
            The data to be added to the buffer

        type : str
            The type of data to be added to the buffer. Default is 'unicode-text'
            Supported Values : 'unicode-text', 'raw'
        '''

        supported_types = ('unicode-text', 'raw')

        if type not in supported_types:
            raise ValueError(f'Unsupported Type: Type must be : {supported_types}')

        if self.max_payload_length > ((len(self.data_buffer) + len(data)) // 2):
            if type == 'unicode-text':
                self.data_buffer += self.hexify(data)
            elif type == 'raw':
                self.data_buffer += data
            self.debug_msg(f'Added Data ! Buffer is now : {self.data_buffer}')
        else:
            raise ValueError(f'Payload Length Exceeded Set Limit : {self.max_payload_length}')

    def hexify(self, data):
        '''
        Converts the data to unicode and then hex.

        Parameters
        ----------
        data : str
            The data to be converted to hex
        '''
        return ''.join('{:02x}'.format(ord(c)) for c in data)