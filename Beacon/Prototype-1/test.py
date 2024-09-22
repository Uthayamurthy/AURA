import btmgmt

def conv_to_hex(data):
    return ''.join('{:02x}'.format(ord(c)) for c in data)

def prep_payload(data): # Prepare payload for broadcast

    hex_data = conv_to_hex(data)
    uuid_type = "16" # Corresponds to 16-bit (2 Bytes !!) UUID
    uuid = "feaa" # The 16-Bit UUID of Eddystone registered by Google
    payload = f'{uuid_type}{uuid}{conv_to_hex(data)}'
    length = len(payload)//2
    payload = f'{length:02x}{payload}'
    print(f'Payload : {payload}\nLength: {length} Bytes')
    return payload

print('Welcome to Bright Sky Beacon Broadcaster !')


cmd = input('Enter Command (B: Start Broadcast, S: Stop Broadcast) : ')


if cmd.lower() == 'b':    
    data = input('Enter data to broadcast : ')

    response = btmgmt.command('add-adv', '-u', 'FEAA', '-d', prep_payload(data),  '-g',  '1')

    print(f'Received Response : {response}')
    print('Done Broadcasting !!')

else:
    print('Stopping Broadcast ...')
    response = btmgmt.command('clr-adv')
    print(f'Received Response : {response}')
    print('Done Stopping !!')