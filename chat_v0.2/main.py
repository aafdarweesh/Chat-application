from bottle import request, Bottle, abort, static_file, template, redirect
app = Bottle()

all_wsocks = []

room_counter = 0

#Room class and its functions
class Room(object):

    def __init__(self):
        self.users = []
        self.messages = ""
        self.all_sockets = []

    def subscribe(self, user, wsock):
        self.users.append(user)
        self.all_sockets.append(wsock)

    def add(self, message):
        self.messages += message + "<br>"

    def get_sockets(self):
    	return self.all_sockets

    def get_messages(self):
    	return self.messages

    def get_username(self,wsock):
    	counter = 0
    	for x in self.all_sockets:
    		if x == wsock:
    			return self.users[counter]
    		counter += 1


users = []
#by default there will be one room in the array and you can create the other rooms
rooms = {
	'defualt' : Room()
}

#this code I took it from internet, the template will redirect to the route('/user')
#firstly choose a user
@app.route('/')
def choose_a_user():
	return template('choose')

#then secondly choose a room, from here the user can either choose a room or create his/her room
@app.route('/<user>')
def choose_a_room(user):
	'''
	global users
	test = 0
	for x in  users:
		if x == user:
			test = 1
			break
	if test == 1:
		print("This id is already exist")
		redirect('/')
	else :
		users.append(user)
	'''
	#users.append(user)
	global rooms
	return template('room', user = user, rooms = rooms.keys())


#here is create room : which will create a new room depending on the
@app.route('/<user>/create')
def create_chatroom(user):
	global rooms, room_counter
	new_one = str(room_counter) + user + '_chatroom'
	rooms.update({ new_one : Room()})
	room_counter += 1
	redirect('/'+user)

#here is the chat room 
@app.route('/<room>/<user>/index')
def handle_websocket(room, user):


    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    #delete later as there is no need for it
    all_wsocks.append(wsock)

    #add the this new socket (the new_user) to the chat room
    global rooms
    rooms[room].subscribe(user, wsock)
    wsock.send(rooms[room].get_messages())

    print('New websocket connected and added to the list')

    while True:
        try:
            message = wsock.receive()

            if message is not None: # if a client disconnects, message becomes None, so skip it
                for ws in rooms[room].all_sockets:
                    if (wsock == ws):
                    	ws.send('You : ' + message)
                    else :
                    	ws.send(user + ':' + message)
                #here it adds the message to the history of messages for this chat room
                rooms[room].add(user + ':' + message)

        except WebSocketError:
        	#delete later
        	re = rooms[room].get_username(wsock)
        	rooms[room].all_sockets.remove(wsock)
        	all_wsocks.remove(wsock)
        	#users.remove(re)
        	rooms[room].users.remove(re)
        	for x in rooms[room].all_sockets:
        		x.send(re + ':' + 'is disconnected')
        	rooms[room].add(re + ':' + 'is disconnected')
        	print('Websocket disconnected and removed from the list')
        	break


@app.route('/<room>/<user>/<filename:path>')
def send_html(room, user,filename):
	return template(filename, room = room, user = user)
    #return static_file(filename, root='./', mimetype='text/html')



from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
server = WSGIServer(("0.0.0.0", 7575), app,
                    handler_class=WebSocketHandler)
print "access @ http://0.0.0.0:7575/"

server.serve_forever()
