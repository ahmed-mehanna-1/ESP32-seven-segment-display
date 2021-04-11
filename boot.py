from machine import Pin
import usocket as socket

import json

import network
import _thread as thread






import gc
gc.collect()

from time import sleep



ssid = 'MicroPython-AP'
password = '123456789'

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password)

while ap.active() == False:
  pass

print('Connection successful')
print(ap.ifconfig())



class Segment:
    def __init__(self,**kwargs):
        self.lis={}
        for key,value in kwargs.items():
            self.lis[key] = Pin(value,Pin.OUT)
        self.numbers = [
            ["a","b","c","d","e","f"],
            ["b","c"],
            ["a","b","g","e","d"],
            ["a","b","g","c","d"],
            ["f","g","b","c"],
            ["a","f","g","c","d"],
            ["a","f","g","c","d","e"],
            ["a","b","c"],
            ["a","b","f","g","c","e","d"],
            ["a","b","f","g","c","d"],
        ]

    def clear(self):
        for i in self.lis:
            self.lis[i].value(1)

    def display(self,number):
        self.clear()
        for letter in self.numbers[number]:
            self.lis[letter].value(0)
    


class Button:
    def __init__(self,button,name):
        self.button = Pin(button, Pin.IN,Pin.PULL_UP)
        self.name=name
        self.last_button_value = 1
    
    def read_button(self):
        cur = self.button.value()
        if(cur == self.last_button_value):
            return 0;
        self.last_button_value = cur
        if(cur==0):
            reset_global()
            global_vars[self.name]=1
            return 1
        return 0 


global_vars={
    "cur_num":0,
    "increase":0,
    "decrease":0,
    "reset":0,
};



def reset_global():
    global_vars['increase']=0
    global_vars['decrease']=0
    global_vars['reset']=0

    


segment = Segment(a=33,b=27,c=32,d=12,e=13,f=25,g=26)
segment.display(global_vars['cur_num'])







def web_page(cur_num):    
    html = """
<html>
   <head>
      <title>ESP Web Server</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="icon" href="data:,">
      <style>
            html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
            h1{color: #0F3376; padding: 2vh;}
            p{font-size: 1.5rem;}
            button{display: inline-block; background-color: #4286f4; border: none; 
            border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
            .button2{background-color: #e7bd3b;}
            .clicked_button{
                background-color: red;
                color:black;
            }
      </style>
   </head>
   <body>
      <h1>ESP Web Server</h1>
      <p>Current Number: <strong id="num">""" + str(cur_num) + """</strong></p>
      <p><button id="increase" onclick="increase()" class="button">increase</button></p>
      <p><button id="decrease" onclick="decrease()" class="button">decrease</button></p>
      <p><button id="reset" onclick="reset()" class="button">reset</button></p>
   </body>

   
   <script>
       get_data = (url) => {
        fetch("http://192.168.4.1/"+url)
        .then(response => response.json())
        .then(data => {
            document.getElementById('num').innerHTML = data['cur_num']
            document.getElementById('increase').className = data['increase'] ? "clicked_button" : ""
            document.getElementById('decrease').className = data['decrease'] ? "clicked_button" : ""
            document.getElementById('reset').className = data['reset'] ? "clicked_button" : "" 
            
        });
       }

       increase = () => get_data('?action=increase')
       decrease = () => get_data('?action=decrease')
       reset = () => get_data('?action=reset')


       setInterval(function(){ 
            get_data('?action=load');   
        }, 500);
   </script>
</html>
"""
    return html




def web_page_thread():
    #gc.collect()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)
    while True:
        try:
            conn, addr = s.accept()
            print('Got a connection from %s' % str(addr))
            request = conn.recv(1024)
            request = str(request)
            cur_num=global_vars['cur_num']
            
            increase = request.find('/?action=increase')
            decrease = request.find('/?action=decrease')
            reset = request.find('/?action=reset')
            load = request.find('/?action=load')

            if increase == 6:
                cur_num = (cur_num+1)%10
                reset_global()
            elif decrease == 6:
                cur_num = (cur_num+9)%10
                reset_global()
            elif reset == 6:
                cur_num = 0
                reset_global()
            elif load == 6 :
                print("loading")
            else:
                print("current number ",cur_num)
                segment.display(cur_num)
                response = web_page(cur_num)
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: text/html\n')
                conn.send('Connection: close\n\n')
                conn.sendall(response)
                conn.close()
        
        
            global_vars['cur_num']=cur_num
            segment.display(cur_num)
            data = json.dumps(global_vars)
            conn.sendall(data)
            
            
            conn.close()
        
        
            
        except:
            conn.close()
            print("web fail")



def circuit_thread():
    add_button = Button(4,name="increase")
    decrease_button = Button(18,name="decrease")
    reset_button = Button(19,name="reset")

    while True:
        try:            
            cur_num=global_vars['cur_num']
            add = add_button.read_button()
            decrease = decrease_button.read_button()
            reset = reset_button.read_button()
            if(add):
                cur_num = (cur_num+1)%10
                global_vars['cur_num'] = cur_num
            elif (decrease):
                cur_num = (cur_num+9)%10
                global_vars['cur_num'] = cur_num
            elif (reset):
                cur_num=0
                global_vars['cur_num']=cur_num
            
            segment.display(global_vars['cur_num'])
            sleep(0.1)
        except:
            print("failed inside circuit")


thread.start_new_thread(circuit_thread, ())
thread.start_new_thread(web_page_thread, ())




