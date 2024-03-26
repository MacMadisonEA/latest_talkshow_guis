from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import asyncio
from pythonosc.udp_client import SimpleUDPClient
import json
from kivy.uix.label import Label
import requests
from registry_url import REGISTRY_URL



async def get_robot_server_data():
        response = requests.get(f'{REGISTRY_URL}/servers/producer_server')
        return response.json()


class OSCServer:
    def __init__(self, robot_data=None):

        self.robot_ip = robot_data["ip_address"]
        self.robot_port = robot_data["port"]
    
        self.client = SimpleUDPClient(self.robot_ip, self.robot_port)
        

    # SEND TO TRITIUM OSC ############################################################
    
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


# GUI ###################################################################################################################

class OSCApp(App):
    def __init__(self, osc_server=None, **kwargs):
        super().__init__(**kwargs)
        self.osc_server = osc_server
        

    def build(self):

        self.main_layout = BoxLayout(orientation='horizontal')
        self.column3 = BoxLayout(orientation='vertical', spacing=5, width=1000)
        self.column3.add_widget(Label(text='Interjections', size_hint_y=None, height=30))
        self.main_layout.add_widget(self.column3)
        self.add_column3_buttons()
       
        return self.main_layout

    
    def add_column3_buttons(self):
        
        self.column3.add_widget(Button(text="Ask about this", on_press=self.show_ask_about_popup))
        self.column3.add_widget(Button(text="Stop talking about", on_press=self.show_stop_talking_popup))
        self.column3.add_widget(Button(text="Stay on topic", on_press=self.osc_server.send_stay_on_topic))
        self.column3.add_widget(Button(text="Say this", on_press=self.show_say_this_popup))
        self.column3.add_widget(Button(text="Add information", on_press=self.show_add_information_popup))
        self.column3.add_widget(Button(text="Transition", on_press=self.show_transition_popup))
        self.column3.add_widget(Button(text="Wrap up", on_press=lambda instance: self.osc_server.send_wrap_up("Wrap up")))
        self.column3.add_widget(Button(text="Continue Segment", on_press=lambda instance: self.osc_server.send_continue("Continue")))


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