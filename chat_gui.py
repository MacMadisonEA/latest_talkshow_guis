from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
import asyncio
from pythonosc.udp_client import SimpleUDPClient
from kivy.uix.label import Label
import requests
from registry_url import REGISTRY_URL



async def get_robot_server_data():
        response = requests.get(f'{REGISTRY_URL}/servers/chat_server')
        return response.json()


class OSCServer:
    def __init__(self, robot_data=None):

        self.robot_ip = robot_data["ip_address"]
        self.robot_port = robot_data["port"]
        self.client = SimpleUDPClient(self.robot_ip, self.robot_port)
     

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


# GUI ###################################################################################################################

class OSCApp(App):
    def __init__(self, osc_server=None, **kwargs):
        super().__init__(**kwargs)
        self.osc_server = osc_server
        if self.osc_server:
            self.osc_server.send_stop_chat_controller("")
        self.chat_controller_active = False  
        self.manual_listen_enabled = False

    def build(self):

        self.main_layout = BoxLayout(orientation='horizontal')
 
        self.column1 = BoxLayout(orientation='vertical', width=400)
        self.column2 = BoxLayout(orientation='vertical', width=400)


        self.column1.add_widget(Label(text='Chat', size_hint_y=None, height=30))
        self.column2.add_widget(Label(text='Segments', size_hint_y=None, height=30))

        self.main_layout.add_widget(self.column1)
        self.main_layout.add_widget(self.column2)
    
  
        self.add_column1_buttons()
        self.add_column2_buttons()
  
        return self.main_layout

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


async def main():
    try:
        robot_server_data = await get_robot_server_data()

        server = OSCServer(robot_data=robot_server_data)
        
        osc_app = OSCApp(osc_server=server)
        await osc_app.async_run(async_lib='asyncio') 
    
    except KeyboardInterrupt:
        server.client.send_message("/stop_chat_controller", [])
        print("Server closed manually.")

if __name__ == "__main__":
    asyncio.run(main())