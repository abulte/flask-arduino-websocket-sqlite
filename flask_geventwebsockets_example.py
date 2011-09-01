(tawlk)lrvick@melchiz> ls                                                                                                                ~/Envs/tawlk
bin/  gevent/  gevent-websocket/  include/  lib/  lib64@  tawlk/
from geventwebsocket.handler import WebSocketHandler                             
from gevent.pywsgi import WSGIServer                                             
from flask import Flask, request                                                 
                                                                                 
app = Flask(__name__)                                                            
                                                                                 
# This could just as easily be render_template(index.html) however it works      
# for a simple one-file example.                                                 
index = """ # This could just as easily be render_template(index.html) but i wanted a simple one-file example.
<html>                                                                           
<head>                                                                           
    <title>Sample test</title>                                                   
    <script type="text/javascript" src="http://code.jquery.com/jquery-1.4.2.min.js"></script>
    <script type="text/javascript" charset="utf-8">                              
        $(document).ready(function(){                                            
            $('form').submit(function(event){                                    
                ws.send($('#data').val())                                        
                return false;                                                    
            });                                                                  
            if ("WebSocket" in window) {                                         
                ws = new WebSocket("ws://udderweb.com:5000/api");                
                ws.onmessage = function (evt) {                                  
                    $("#log").append("<p>"+evt.data+"</p>")                      
                };                                                               
            } else {                                                             
                alert("WebSocket not supported");                                
            }                                                                    
        });                                                                      
    </script>                                                                    
</head>                                                                          
<body>                                                                           
    <h1>Send:</h1>                                                               
    <form method='POST' action='#'>                                              
        <textarea name='data' id="data"></textarea>                              
        <div><input type='submit'></div>                                         
    </form>                                                                      
    <h1>Receive:</h1>                                                            
    <div id="log"></div>                                                         
</body>                                                                          
</html>                                                                          
"""                                                                              
                                                                                 
@app.route('/', methods=['POST','GET'])                                          
def home():                                                                      
    return index                                                                 
                                                                                 
@app.route('/api')                                                               
def api():                                                                       
    if request.environ.get('wsgi.w:ebsocket'):                                                                                                        
        ws = request.environ['wsgi.websocket']                                   
        while True:                                                              
            message = ws.wait()                                                  
            ws.send(message)                                                     
    return                                                                       
                                                                                 
if __name__ == '__main__':                                                       
    http_server = WSGIServer(('',5000), app, handler_class=WebSocketHandler)     
    http_server.serve_forever()