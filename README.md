# PyWinIoT

PyWinIoT is a solution made on Python to monitor and control a Windows machine via MQTT integrated with Home Assistant.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the libraries needed to run PyWinIoT.

```bash
pip install -r requirements.txt
```

## Usage
- Open your firewall on 1883/TCP port for incoming connections
- Create a copy of change-example.yaml and rename it to config.yaml
- Open your new config.yaml file and edit the settings there as you wish (explanation - TBD)

After this changes, just run mqtt-agent.py

```bash
python mqtt-agent.py
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
