# ESP32 e SN74HC595

O firmware MicroPython expõe uma API HTTP na rede local para acender dez LEDs e executar efeitos. O NenzaBot usa essa API para controlar a montagem pelo Discord.

## Montagem

| LEDs | Cor | Controle |
| --- | --- | --- |
| 0 | Vermelho | GPIO 5 |
| 1 | Vermelho | GPIO 21 |
| 2 e 3 | Amarelo | SN74HC595 |
| 4 e 5 | Verde | SN74HC595 |
| 6 a 9 | Azul | SN74HC595 |

O SN74HC595 recebe dados no GPIO 23, clock no GPIO 18 e latch no GPIO 19.

## Configuração

1. Crie um arquivo local `secrets.py` com as credenciais da rede Wi-Fi.

   ```python
   WIFI_SSID = "nome-da-rede"
   WIFI_PASSWORD = "senha-da-rede"
   ```

2. Envie `main.py` e `secrets.py` para a ESP32 e reinicie a placa.
3. Confira o IP no console serial. A integração atual usa `192.168.15.2` na porta 80. A máquina que roda o NenzaBrain precisa alcançar esse endereço na rede local.

## API HTTP

| Rota GET | Ação | Status esperado |
| --- | --- | --- |
| `/` | Verifica se a placa responde | `online` |
| `/led/<indice>` | Acende um LED de 0 a 9 e apaga os demais | `ok` |
| `/led/todos` | Acende os dez LEDs | `todos_acesos` |
| `/apagar` | Interrompe a animação e apaga todos os LEDs | `apagado` |
| `/efeito/varredura` | Percorre os LEDs do 0 ao 9 e volta | `efeito_iniciado` |
| `/efeito/pulso-azul` | Pisca os quatro LEDs azuis juntos | `efeito_iniciado` |
| `/efeito/celebracao` | Passa pelas quatro cores e pisca todos os LEDs | `efeito_iniciado` |
| `/efeito/parar` | Interrompe a animação e apaga todos os LEDs | `apagado` |

As respostas usam JSON. Cada efeito roda uma vez e apaga os LEDs ao terminar. O status `efeito_iniciado` confirma o início da animação.

## Integração com o NenzaBot

1. O usuário pede no Discord, por exemplo, “Roda a celebração”.
2. O agente, em `NenzaBrain/brain/agent.py`, chama `esp32_iniciar_efeito("celebracao")`.
3. A ferramenta, em `NenzaBrain/tools/esp32.py`, envia `GET /efeito/celebracao` e valida o status da resposta. A ESP32 executa a sequência localmente.

O agente também registra `esp32_status`, `esp32_acender_led`, `esp32_acender_todos`, `esp32_apagar_leds` e `esp32_parar_efeito`. Se o IP da placa mudar, ajuste `_HOST` em `NenzaBrain/tools/esp32.py` e reinicie o NenzaBrain.

Para testar a conexão a partir da máquina do bot, execute:

```powershell
curl.exe http://192.168.15.2/
```

A resposta esperada é `{"status":"online"}`.
