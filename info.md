# Dew Point Sensor

A custom sensor to calculate the
[dew point](https://en.wikipedia.org/wiki/Dew_point) from temperature and
humidity. It is adapted from Home Assistant's
[Mold Indicator](https://www.home-assistant.io/integrations/mold_indicator/)
sensor allowing to use dew points without the need of external references.

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