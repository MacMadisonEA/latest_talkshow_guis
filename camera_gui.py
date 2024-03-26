from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import asyncio
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
from kivy.uix.label import Label
from kivy.core.window import Window
import requests
import socket
import json
from registry_url import REGISTRY_URL

SERVER_NAME = "camera_gui"
BIND_PORT = 54322
SERVER_IP = None


async def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(ip)
        return ip


async def get_robot_server_data():
        response = requests.get(f'{REGISTRY_URL}/servers/camera_server')
        return response.json()

class OSCServer:
    def __init__(self, IP, robot_data=None):

        self.IP = IP
        self.BIND_PORT = BIND_PORT
        self.robot_ip = robot_data["ip_address"]
        self.robot_port = robot_data["port"]
    
        self.client = SimpleUDPClient(self.robot_ip, self.robot_port)
        self.targets = [] 
     

    def default_handler(self, addr, *args):
        print(f"OSC Message {addr!r}", repr(args))
        if addr == "/send_camera_targets":
            print("Recieved targets")
            self.targets = list(args)
            App.get_running_app().update_buttons(self.targets)


    # SEND TO TRITIUM OSC ############################################################
    
    def send_client_data(self):
        data = {
            'ip': self.IP,
            'port': self.BIND_PORT
        }
        json_data = json.dumps(data)
        self.client.send_message("/camera_client_data", json_data)
    
    # GAZE 
    def send_create_new_camera_target(self):
        self.client.send_message("/new_camera_target_mode", [])

    def send_get_saved_camera_targets(self):
        self.client.send_message("/get_camera_targets", [])

    def send_record_camera_target(self, name):
        self.client.send_message("/record_camera_target", [name])

    def send_look_at_camera_target(self, name):
        self.client.send_message("/look_at_camera_target", name)

    def load_targets(self):
        self.targets = self.send_get_saved_camera_targets()

    def send_look_around(self, test):
        self.client.send_message("/look_around", [])
    
    def send_look_around_camera_target(self, target):
        self.client.send_message("/look_around_camera_target", target)

    def send_delete_camera_target(self, name):
        self.client.send_message("/delete_camera_target", [name])


    # RUN SERVER #############################################################
    
    async def run_server(self):
    
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self.default_handler)
        server = AsyncIOOSCUDPServer((self.IP, self.BIND_PORT), dispatcher, asyncio.get_event_loop())
        _, _ = await server.create_serve_endpoint()
        self.send_client_data()
        osc_app = OSCApp(osc_server=self)
        asyncio.ensure_future(osc_app.async_run(async_lib='asyncio'))
        self.send_get_saved_camera_targets()
        print("Server started successfully. Waiting for messages...")

        await asyncio.get_event_loop().create_future()


# GUI ###################################################################################################################

class OSCApp(App):
    def __init__(self, osc_server=None, **kwargs):
        super().__init__(**kwargs)
        self.osc_server = osc_server
        Window.bind(on_request_close=self.on_request_close)

    def build(self):

        self.main_layout = BoxLayout(orientation='horizontal')
 
        self.column4 = BoxLayout(orientation='vertical', width=600)

        self.main_layout.add_widget(self.column4)
        
        return self.main_layout
    
    def on_request_close(self, *args, **kwargs):
 
        self.stop_asyncio_loop()
        return False  

    def stop_asyncio_loop(self):
        loop = asyncio.get_event_loop()
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.stop()


    def add_column4_buttons(self):

        self.column4.add_widget(Label(text='Camera Targets', size_hint_y=None, height=30))
        self.column4.add_widget(Button(text="Create new camera target", on_press=self.initiate_new_target_creation))
        self.column4.add_widget(Button(text="Look around", on_press=self.osc_server.send_look_around))
      

    def update_buttons(self, targets):
      
        self.column4.clear_widgets()  
        self.add_column4_buttons()  
        
        for target in targets:
            
            target_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=200)
        
            target_btn = Button(text=target, size_hint_x=0.5)
            target_btn.bind(on_press=lambda instance, t=target: self.osc_server.send_look_at_camera_target(t))
        
            delete_btn = Button(text="Delete", size_hint_x=0.25)
            delete_btn.bind(on_press=lambda instance, t=target: self.delete_target(t))
           
            look_around_btn = Button(text="Relative Look Around", size_hint_x=0.25)
            look_around_btn.bind(on_press=lambda instance, t=target: self.osc_server.send_look_around_camera_target(t))  
         
            target_layout.add_widget(target_btn)
            target_layout.add_widget(delete_btn)
            target_layout.add_widget(look_around_btn)
            
      
            self.column4.add_widget(target_layout)

    def delete_target(self, target):
        self.osc_server.send_delete_camera_target(target)

        if target in self.osc_server.targets:
            self.osc_server.targets.remove(target)
        self.update_buttons(self.osc_server.targets)


    def show_input_popup(self, title, hint_text, send_method):
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_field = TextInput(hint_text=hint_text, size_hint_y=None, height=44)
        send_btn = Button(text='Send', size_hint_y=None, height=50)
        popup_layout.add_widget(input_field)
        popup_layout.add_widget(send_btn)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.75, 0.4))
        send_btn.bind(on_press=lambda instance: self.send_input_data(input_field.text, send_method, popup))
        popup.open()

 
    def send_input_data(self, input_data, send_method, popup):
        if input_data.strip(): 
            send_method(input_data)
            popup.dismiss()

    def initiate_new_target_creation(self, instance):
        self.osc_server.send_create_new_camera_target()  
        self.show_input_popup("Create New Camera Target", "Enter target name", self.osc_server.send_record_camera_target)

async def main():
    try:
        robot_server_data = await get_robot_server_data()
        SERVER_IP = await get_ip()
        server = OSCServer(SERVER_IP, robot_data=robot_server_data)
        await server.run_server()  
    
    except KeyboardInterrupt:
        print("Server closed manually.")

if __name__ == "__main__":
    asyncio.run(main())