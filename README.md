# Home Assistant Dew Point Sensor

A custom sensor to calculate the
[dew point](https://en.wikipedia.org/wiki/Dew_point) from temperature and
humidity. It is adapted from Home Assistant's
[Mold Indicator](https://www.home-assistant.io/integrations/mold_indicator/)
sensor allowing to use dew points without the need of external temperature references.

## Installation

Use [hacs](https://custom-components.github.io/hacs/) with this repository URL
https://github.com/alf-scotland/ha-dewpoint.git or copy `custom_components/`
to your HA configuration.

## Example

To use the Dew Point sensor in your installation, add the following to your
`configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: dewpoint
    temperature_sensor: sensor.temperature
    humidity_sensor: sensor.humidity
```

## Configuration

key | required | type | description
--- | --- | --- | ---
`name` | No | string | The name of the sensor
`temperature_sensor` | Yes | string | The entity ID of the temperature sensor
`humidity_sensor` | Yes | string | The entity ID of the humidity sensor
