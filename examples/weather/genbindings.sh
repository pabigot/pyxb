pyxbgen \
   --wsdl-location="http://ws.cdyne.com/WeatherWS/Weather.asmx?wsdl" --module=weather \
   --write-for-customization \
 || ( echo "Failed to generate bindings" ; exit 1 )
