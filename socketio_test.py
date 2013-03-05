from socketio import socketio_manage
from flask import Flask, request, render_template, Response
from socketio.namespace import BaseNamespace
from socketio.server import SocketIOServer
from gevent import monkey

import time

monkey.patch_all()

app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
    return render_template('socketio.html')

class SerialNamespace(BaseNamespace):
    def on_get_serial(self):
        self.emit('results', 'start')
        i = 0
        while i < 60:
            self.emit('results', str(i))
            time.sleep(1)
            i += 1
        self.emit('results', 'end')

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        socketio_manage(request.environ, {'/serial': SerialNamespace}, request)
    except:
        app.logger.error("Exception while handling socketio connection",
                         exc_info=True)
    return Response()

if __name__ == '__main__':
    ws = SocketIOServer(('0.0.0.0', 80), app, resource="socket.io", policy_server=False)
    try:
        ws.serve_forever()
    except KeyboardInterrupt:
        ws.stop()
        print 'Bye'