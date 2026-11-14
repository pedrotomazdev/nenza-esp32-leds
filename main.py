import network
import secrets
import select
import socket
from time import ticks_add, ticks_diff, ticks_ms
from machine import Pin

DATA = Pin(23, Pin.OUT)
CLOCK = Pin(18, Pin.OUT)
LATCH = Pin(19, Pin.OUT)

led1 = Pin(5, Pin.OUT)
led2 = Pin(21, Pin.OUT)

WIFI_SSID = secrets.WIFI_SSID
WIFI_PASSWORD = secrets.WIFI_PASSWORD

def enviar(valor):
    LATCH.off()

    for i in range(7, -1, -1):
        CLOCK.off()
        DATA.value((valor >> i) & 1)
        CLOCK.on()

    LATCH.on()

def acender(indice):
    led1.off()
    led2.off()

    if indice == 0:
        enviar(0)
        led1.on()
    elif indice == 1:
        enviar(0)
        led2.on()
    elif 2 <= indice < 10:
        enviar(1 << (9 - indice))

def acender_todos():
    enviar(0xFF)
    led1.on()
    led2.on()

def apagar():
    led1.off()
    led2.off()
    enviar(0)

apagar()

# Cada quadro contém os índices acesos e sua duração em milissegundos.
EFEITOS = {
    "varredura": tuple(((i,), 120) for i in range(10))
    + tuple(((i,), 120) for i in range(8, -1, -1)),
    "pulso-azul": (((6, 7, 8, 9), 350), ((), 250)) * 4,
    "celebracao": (
        ((0, 1), 220), ((2, 3), 220), ((4, 5), 220), ((6, 7, 8, 9), 220),
        ((), 150), (tuple(range(10)), 250), ((), 150), (tuple(range(10)), 250),
    ),
}


def mostrar_quadro(indices):
    valor = 0
    for indice in indices:
        if indice >= 2:
            valor |= 1 << (9 - indice)
    enviar(valor)
    led1.value(0 in indices)
    led2.value(1 in indices)

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

while not wifi.isconnected():
    pass

ip = wifi.ifconfig()[0]
print("ESP32 conectado:", ip)

servidor = socket.socket()
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(("0.0.0.0", 80))
servidor.listen(2)
poll = select.poll()
poll.register(servidor, select.POLLIN)
quadros = None
proximo_quadro = 0
prazo = 0

while True:
    espera = -1
    if quadros is not None:
        agora = ticks_ms()
        if ticks_diff(agora, prazo) >= 0:
            if proximo_quadro == len(quadros):
                quadros = None
                apagar()
            else:
                indices, duracao = quadros[proximo_quadro]
                mostrar_quadro(indices)
                proximo_quadro += 1
                prazo = ticks_add(agora, duracao)
        if quadros is not None:
            espera = max(0, ticks_diff(prazo, ticks_ms()))

    if not poll.poll(espera):
        continue
    cliente, endereco = servidor.accept()

    try:
        cliente.settimeout(3)
        requisicao = cliente.recv(1024).decode()
        caminho = requisicao.split(" ")[1]

        if caminho.startswith("/led/") and caminho != "/led/todos":
            indice = int(caminho.split("/")[2])

            if 0 <= indice < 10:
                quadros = None
                acender(indice)
                resposta = '{"status":"ok"}'
            else:
                resposta = '{"erro":"LED invalido"}'

        elif caminho == "/led/todos":
            quadros = None
            acender_todos()
            resposta = '{"status":"todos_acesos"}'

        elif caminho in ("/apagar", "/efeito/parar"):
            quadros = None
            apagar()
            resposta = '{"status":"apagado"}'

        elif caminho.startswith("/efeito/"):
            nome = caminho[len("/efeito/"):]
            if nome in EFEITOS:
                quadros = EFEITOS[nome]
                proximo_quadro = 0
                prazo = ticks_ms()
                resposta = '{"status":"efeito_iniciado"}'
            else:
                resposta = '{"erro":"Efeito invalido"}'

        else:
            resposta = '{"status":"online"}'

        cliente.send(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Connection: close\r\n\r\n"
        )
        cliente.send(resposta.encode())

    except Exception as erro:
        print("Erro:", erro)

    finally:
        cliente.close()
