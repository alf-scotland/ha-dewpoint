# Home Assistant Dew Point Sensor

A custom sensor to calculate the
[dew point](https://en.wikipedia.org/wiki/Dew_point) from temperature and
humidity. It is adapted from Home Assistant's
[Mold Indicator](https://www.home-assistant.io/integrations/mold_indicator/)
sensor allowing to use dew points without the need of external references.

## Installation

Use [hacs](https://custom-components.github.io/hacs/) with this repository URL
https://github.com/alf-scotland/ha-dewpoint.git or copy `custom_components/`
to your HA configuration.

## Configuration

To use the Dew Point sensor in your installation, add the following to your
`configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: dewpoint
    temperature_sensor: sensor.temperature
    humidity_sensor: sensor.humidity
```

{% configuration %}
name:
  description: The name of the sensor.
  required: false
  type: string
temperature_sensor:
  description: The entity ID of the temperature sensor.
  required: true
  type: string
humidity_sensor:
  description: The entity ID of the humidity sensor.
  required: true
  type: string
{% endconfiguration %}
