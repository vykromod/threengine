"""Bowlivion game PoC
python asyncio websockets module for dispatching events between bowlivion host and clients
if certificate isn't set properly socket server will fallback to localahost port 8001
you can assign you local area network address host and enjoy ping 0 game
don't forget to set proper websock addresses wsaddr in JS module in game's HTML file
self signed certificates should also work, tested with let's encrypt certificate
"""
import asyncio
import websockets
import json
import ssl, pathlib


#web socket server settings
fullchain_pem = '/path to your site certs/fullchain.pem'
cert_key = '/path to your site certs/privkey.pem'
host = '192.168.1.103'#'192.168.1.103'
port = 8001





wsocks = {}
wsocksrev = {}
clients = {}
ticker = 0.05
msg_count = 0
host_wsock = None
clinames = []

emulated_lag = 0#.07

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
try:
    ssl_context.load_cert_chain(fullchain_pem, cert_key)
except Exception as errinst:
    print(errinst)
    print('Certificate could not be loaded, falling back to localhost 127.0.0.1 :', port)
    ssl_context = None

def register_client(wsock, name="WSSclient"):
    global clients, clinames
    counter = 0
    new_name = name
    while new_name in clients.keys():
        new_name = '%s-%i' % (name, counter)
        counter += 1
    clinames.append(new_name)
    clients[new_name] = wsock
    return new_name
    

last_wolrd_data = None

async def handler(websocket):
    global wsocks, host_wsock, clinames
    while True:
        try:
            message = await websocket.recv()
        except websockets.exceptions.ConnectionClosedError as exc_inst:
            break
        except websockets.exceptions.ConnectionClosedOK:
            break
        #print(dir(websocket))
        #print(websocket.origin)
        #print(websocket.remote_address)
        #print(websocket.latency)
        #print(wsocks)
        #print(message)
        if message == 'host':
            if not host_wsock:
                host_wsock = websocket
                print('host set', websocket)
            else:
                print('host request ignored', websocket)
                await websocket.send('>host websocket already registered')
            continue
        if websocket != host_wsock:
            if emulated_lag:
                await asyncio.sleep(emulated_lag)
            if not websocket.remote_address in wsocks.keys():
                wsocks[websocket.remote_address] = websocket
                wsocksrev[websocket] = websocket.remote_address
                #websocket._raddr = webdocket.remote_address
                print('websocket added %s:%i' % websocket.remote_address)
                if message == 'client':
                    cli_data = {}
                    name = register_client(websocket, name="WSSclient")
                    cli_data['name'] = name
                    print('clients: %i' % len(wsocks.keys()))
                    websocket.cliName = name
                    
                    await host_wsock.send('%s %s' % (message, name))
                                    #websocket.remote_address[0],
                                    #websocket.remote_address[1]))
                    print('client registered %s %s:%i' % (websocket.cliName,
                                websocket.remote_address[0],
                                websocket.remote_address[1],
                        ))
                    
                    await websocket.send('>%s' % json.dumps(cli_data))
                    continue
            await host_wsock.send('>%s %s' % (websocket.cliName, message))
                                                #websocket.remote_address[0],
                                                #websocket.remote_address[1],
                                                # message))
        else:
            await process_host_data(message)#json.loads(message))

async def process_host_data(data):
    global last_world_data
    last_world_data = data
    await asyncio.sleep(0.00001)


async def broadcast():
    global wsocks, msg_count, last_world_data
    while True:
        #print('broadcast')
        await asyncio.sleep(ticker)
        #print(len(wsocks.values()))
        #msg_count += 1
        if len(wsocks.values()):
            #[await wsocket.send('message:%i'%msg_count) for wsocket in wsocks.values()]
            if last_world_data:
                data = last_world_data
                last_world_data = None
                #print('sending world data')
            else:
                #print('no world data')
                continue
            to_remove = []
            if emulated_lag:
                await asyncio.sleep(emulated_lag)
            for wsocket in wsocks.values():
                try:
                    await wsocket.send(data)
                except websockets.exceptions.ConnectionClosedError as exc_inst:
                    to_remove.append(wsocksrev[wsocket])#._raddr)#remote_address)
                except websockets.exceptions.ConnectionClosedOK:
                    to_remove.append(wsocksrev[wsocket])#wsocket._raddr)#remote_address)
            if (len(to_remove)):
                [print('websocket removed %s:%i, closed' % addr) for addr in to_remove]
                for addr in to_remove:
                    await host_wsock.send('>%s remove' % wsocks[addr].cliName)
                [wsocks.__delitem__(addr) for addr in to_remove]
                
                

async def main():
    event_loop = asyncio.get_event_loop()#.run_until_complete(broadcast)
    asyncio.ensure_future(broadcast(), loop = event_loop)
    async with websockets.serve(handler, host, port):
        #await broadcast()
        await asyncio.Future()  # run forever


                            

           # pathlib.Path(__file__).with_name('localhost.pem'))
async def main_ssl():
    event_loop = asyncio.get_event_loop()#.run_until_complete(broadcast)
    asyncio.ensure_future(broadcast(), loop = event_loop)

    #start_server = websockets.serve(
    #        handler, host, port, ssl=ssl_context)
    if ssl_context:
        async with websockets.serve(
                handler, host, port, ssl=ssl_context):#start_server:
            await asyncio.Future()
    else:
        async with websockets.serve(
                handler, '127.0.0.1', port):
            await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main_ssl())
