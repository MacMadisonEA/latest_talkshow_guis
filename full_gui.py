from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import asyncio
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
import json
from kivy.uix.label import Label
import requests
import socket
from kivy.core.window import Window
from registry_url import REGISTRY_URL

SERVER_NAME = "full_gui"
BIND_PORT = 54321
SERVER_IP = None


async def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(ip)
        return ip


async def get_robot_server_data():
        response = requests.get(f'{REGISTRY_URL}/servers/full_server')
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

    def send_client_data(self):
        data = {
            'ip': self.IP,
            'port': self.BIND_PORT
        }
        json_data = json.dumps(data)
        self.client.send_message("/full_client_data", json_data)
    
    # SEND TO TRITIUM OSC ############################################################
    
    # CHAT
    def send_start_chat_controller(self, test):
        self.client.send_message("/start_chat_controller", [])

    def send_stop_chat_controller(self, test):
        self.client.send_message("/stop_chat_controller", [])


    # MANUAL LISTEN
    def send_enable_listen(self, test):
        self.client.send_message("/enable_manual_listen_mode", [])

    def send_disable_listen(self, test):
        self.client.send_message("/disable_manual_listen_mode", [])

    def send_stop_listen(self, test):
        self.client.send_message("/stop_listening", [])

    # SEGMENTS
    def send_start_monologue(self, test):
        self.client.send_message("/start_monologue", [])

    def send_start_interview(self, test):
        self.client.send_message("/start_interview", [])

    def send_start_game(self, test):
        self.client.send_message("/start_game", [])

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



    # INJECTIONS
    
    def send_ask_about(self, topic):
        json_data = json.dumps(topic)
        self.client.send_message("/ask_about_this", [json_data])

    def send_stop_talking(self, topic):
        json_data = json.dumps(topic)
        self.client.send_message("/stop_talking_about_x", [json_data])

    def send_stay_on_topic(self, topic):
        self.client.send_message("/stay_on_topic", [])


    def send_add_info(self, info):
        json_data = json.dumps(info)
        self.client.send_message("/add_information", [json_data])


    def send_transition(self, info):
        json_data = json.dumps(info)
        self.client.send_message("/transition_next_segment", [json_data])

    def send_wrap_up(self, info):
        json_data = json.dumps(info)
        self.client.send_message("/wrap_up", [json_data])

    def send_continue(self, info):
        json_data = json.dumps(info)
        self.client.send_message("/continue_segment", [json_data])

    def send_say_this(self, text):
        json_data = json.dumps(text)
        self.client.send_message("/say_this", [json_data])


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
        if self.osc_server:
            self.osc_server.send_stop_chat_controller("")

        Window.bind(on_request_close=self.on_request_close)
        self.chat_controller_active = False  
        self.manual_listen_enabled = False

    def build(self):

        self.main_layout = BoxLayout(orientation='horizontal')
 
        self.column1 = BoxLayout(orientation='vertical', width=200)
        self.column2 = BoxLayout(orientation='vertical', width=200)
        self.column3 = BoxLayout(orientation='vertical', width=200)
        self.column4 = BoxLayout(orientation='vertical', width=200)
        


        self.column1.add_widget(Label(text='Chat', size_hint_y=None, height=30))
        self.column2.add_widget(Label(text='Segments', size_hint_y=None, height=30))
        self.column3.add_widget(Label(text='Injections', size_hint_y=None, height=30))


        self.main_layout.add_widget(self.column1)
        self.main_layout.add_widget(self.column2)
        self.main_layout.add_widget(self.column3)
        self.main_layout.add_widget(self.column4)
        
  
        self.add_column1_buttons()
        self.add_column2_buttons()
        self.add_column3_buttons()
       
        
        return self.main_layout
    
    def on_request_close(self, *args, **kwargs):

        self.stop_asyncio_loop()
        return False  

    def stop_asyncio_loop(self):
        loop = asyncio.get_event_loop()
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.stop()

    def add_column1_buttons(self):
        
        start_chat_btn = Button(text="Start Chat Controller", on_press=self.toggle_chat_controller)
        self.column1.add_widget(start_chat_btn)

    
    def toggle_chat_controller(self, instance):
        self.chat_controller_active = not self.chat_controller_active
        
        self.column1.clear_widgets()
        self.column1.add_widget(Label(text='Chat', size_hint_y=None, height=30))
        
        if self.chat_controller_active:
            self.osc_server.send_start_chat_controller("")
            btn = Button(text="Stop Chat Controller", on_press=self.toggle_chat_controller)
            self.column1.add_widget(btn)
           
            self.add_enable_manual_listen_button()
        
        else:
            self.osc_server.send_stop_chat_controller("")
            btn = Button(text="Start Chat Controller", on_press=self.toggle_chat_controller)
            self.column1.add_widget(btn)
            self.manual_listen_enabled = False 


    def add_enable_manual_listen_button(self):
    
        enable_listen_btn = Button(text="Enable Manual Listen", on_press=self.toggle_manual_listen)
        self.column1.add_widget(enable_listen_btn)

    def toggle_manual_listen(self, instance):
        self.manual_listen_enabled = not self.manual_listen_enabled
        
        self.update_manual_listen_buttons()


    def update_manual_listen_buttons(self):
       
        self.column1.clear_widgets()
        self.column1.add_widget(Label(text='Chat', size_hint_y=None, height=30))
        if self.chat_controller_active:
            self.column1.add_widget(Button(text="Stop Chat Controller", on_press=self.toggle_chat_controller))
        else:
            self.column1.add_widget(Button(text="Start Chat Controller", on_press=self.toggle_chat_controller))
        
       
        if self.manual_listen_enabled:
            self.column1.add_widget(Button(text="Disable Manual Listen", on_press=self.toggle_manual_listen))
            self.column1.add_widget(Button(text="Stop Listening", on_press=self.osc_server.send_stop_listen))
            self.osc_server.send_enable_listen(None)  
        else:
            self.add_enable_manual_listen_button()
            self.osc_server.send_disable_listen(None) 



    def add_column2_buttons(self):
        
        self.column2.add_widget(Button(text="Start Monologue", on_press=self.osc_server.send_start_monologue))
        self.column2.add_widget(Button(text="Start Interview", on_press=self.osc_server.send_start_interview))
        self.column2.add_widget(Button(text="Start Game", on_press=self.osc_server.send_start_game))

    def add_column3_buttons(self):
        
        self.column3.add_widget(Button(text="Ask about this", on_press=self.show_ask_about_popup))
        self.column3.add_widget(Button(text="Stop talking about", on_press=self.show_stop_talking_popup))
        self.column3.add_widget(Button(text="Stay on topic", on_press=self.osc_server.send_stay_on_topic))
        self.column3.add_widget(Button(text="Say this", on_press=self.show_say_this_popup))
        self.column3.add_widget(Button(text="Add information", on_press=self.show_add_information_popup))
        self.column3.add_widget(Button(text="Transition", on_press=self.show_transition_popup))
        self.column3.add_widget(Button(text="Wrap up", on_press=lambda instance: self.osc_server.send_wrap_up("Wrap up")))
        self.column3.add_widget(Button(text="Continue Segment", on_press=lambda instance: self.osc_server.send_continue("Continue")))

    def add_column4_buttons(self):

        self.column4.add_widget(Label(text='Camera Targets', size_hint_y=None, height=30))
        self.column4.add_widget(Button(text="Create new camera target", on_press=self.initiate_new_target_creation))
        self.column4.add_widget(Button(text="Look around", on_press=self.osc_server.send_look_around))
      

    def update_buttons(self, targets):
      
        self.column4.clear_widgets()  
        self.add_column4_buttons()  
        
        for target in targets:
            
            target_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44)
            
            
            target_btn = Button(text=target, size_hint_x=0.5)
            target_btn.bind(on_press=lambda instance, t=target: self.osc_server.send_look_at_camera_target(t))
            
         
            delete_btn = Button(text="Del", size_hint_x=0.25)
            delete_btn.bind(on_press=lambda instance, t=target: self.delete_target(t))
            
           
            look_around_btn = Button(text="Look", size_hint_x=0.25)
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
    
    def show_ask_about_popup(self, instance):
        self.show_input_popup("Ask About This", "Enter topic to ask about", self.osc_server.send_ask_about)

    def show_stop_talking_popup(self, instance):
        self.show_input_popup("Stop Talking About", "Enter topic to stop talking about", self.osc_server.send_stop_talking)

    def show_add_information_popup(self, instance):
        self.show_input_popup("Add Information", "Enter information to add", self.osc_server.send_add_info)

    def show_transition_popup(self, instance):
        self.show_input_popup("Transition", "Enter next segment name", self.osc_server.send_transition)

    def show_say_this_popup(self, instance):
        self.show_input_popup("Say This", "Enter text to say", self.osc_server.send_say_this)

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
        server.client.send_message("/stop_chat_controller", [])
        print("Server closed manually.")

if __name__ == "__main__":
    asyncio.run(main())