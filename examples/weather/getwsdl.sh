test -f weather.wsdl || wget -O weather.wsdl 'http://ws.cdyne.com/WeatherWS/Weather.asmx?WSDL'
wget -O 85711.xml 'http://ws.cdyne.com/WeatherWS/Weather.asmx/GetCityForecastByZIP?ZIP=85711'
PYTHONPATH=../.. python gensvcbind.py
PYTHONPATH=../.. python client.py

