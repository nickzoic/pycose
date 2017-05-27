import pycose
import pycose.http
import machine
import network

w = network.WLAN()
w.active(True)
w.connect('CCHS-WiFI', 'hackmelb')

tasks = [
    pycose.http.web_server(pycose.http.static_file_handler("/flash/www"))
]

pycose.loop(tasks)
