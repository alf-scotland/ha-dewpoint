"""Calculates the dew point from temperature and humidity."""
import logging
import math

import voluptuous as vol

from homeassistant import util
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME,
    EVENT_HOMEASSISTANT_START,
    PERCENTAGE,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)

CONF_HUMIDITY = "humidity_sensor"
CONF_TEMPERATURE = "temperature_sensor"

DEFAULT_NAME = "Dew Point"

MAGNUS_K2 = 17.62
MAGNUS_K3 = 243.12

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TEMPERATURE): cv.entity_id,
        vol.Required(CONF_HUMIDITY): cv.entity_id,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up DewPoint sensor."""
    name = config.get(CONF_NAME, DEFAULT_NAME)
    temperature_sensor = config.get(CONF_TEMPERATURE)
    humidity_sensor = config.get(CONF_HUMIDITY)

    async_add_entities(
        [
            DewPoint(
                name,
                hass.config.units.is_metric,
                temperature_sensor,
                humidity_sensor,
            )
        ],
        False,
    )


class DewPoint(SensorEntity):
    """Represents a DewPoint sensor."""

    def __init__(
        self,
        name,
        is_metric,
        temperature_sensor,
        humidity_sensor,
    ):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._temperature_sensor = temperature_sensor
        self._humidity_sensor = humidity_sensor
        self._is_metric = is_metric
        self._available = False
        self._entities = {
            self._temperature_sensor,
            self._humidity_sensor,
        }

        self._temperature = None
        self._humidity = None

    async def async_added_to_hass(self):
        """Register callbacks."""

        @callback
        def dew_point_sensors_state_listener(event):
            """Handle for state changes for dependent sensors."""
            new_state = event.data.get("new_state")
            old_state = event.data.get("old_state")
            entity = event.data.get("entity_id")
            _LOGGER.debug(
                "Sensor state change for %s that had old state %s and new state %s",
                entity,
                old_state,
                new_state,
            )

            if self._update_sensor(entity, old_state, new_state):
                self.async_schedule_update_ha_state(True)

        @callback
        def dew_point_startup(event):
            """Add listeners and get 1st state."""
            _LOGGER.debug("Startup for %s", self.entity_id)

            async_track_state_change_event(
                self.hass, list(self._entities), dew_point_sensors_state_listener
            )

            # Read initial state
            temperature = self.hass.states.get(self._temperature_sensor)
            humidity = self.hass.states.get(self._humidity_sensor)

            schedule_update = self._update_sensor(
                self._temperature_sensor, None, temperature
            )

            schedule_update = (
                False
                if not self._update_sensor(
                    self._humidity_sensor, None, humidity
                )
                else schedule_update
            )

            if schedule_update:
                self.async_schedule_update_ha_state(True)

        self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_START, dew_point_startup
        )

    def _update_sensor(self, entity, old_state, new_state):
        """Update information based on new sensor states."""
        _LOGGER.debug("Sensor update for %s", entity)
        if new_state is None:
            return False

        # If old_state is not set and new state is unknown then it means
        # that the sensor just started up
        if old_state is None and new_state.state == STATE_UNKNOWN:
            return False

        if entity == self._temperature_sensor:
            self._temperature = DewPoint._update_temp_sensor(new_state)
        elif entity == self._humidity_sensor:
            self._humidity = DewPoint._update_hum_sensor(new_state)

        return True

    @staticmethod
    def _update_temp_sensor(state):
        """Parse temperature sensor value."""
        _LOGGER.debug("Updating temp sensor with value %s", state.state)

        # Return an error if the sensor change its state to Unknown.
        if state.state == STATE_UNKNOWN:
            _LOGGER.error(
                "Unable to parse temperature sensor %s with state: %s",
                state.entity_id,
                state.state,
            )
            return None

        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        temp = util.convert(state.state, float)

        if temp is None:
            _LOGGER.error(
                "Unable to parse temperature sensor %s with state: %s",
                state.entity_id,
                state.state,
            )
            return None

        # convert to celsius if necessary
        if unit == TEMP_FAHRENHEIT:
            return util.temperature.fahrenheit_to_celsius(temp)
        if unit == TEMP_CELSIUS:
            return temp
        _LOGGER.error(
            "Temp sensor %s has unsupported unit: %s (allowed: %s, %s)",
            state.entity_id,
            unit,
            TEMP_CELSIUS,
            TEMP_FAHRENHEIT,
        )

        return None

    @staticmethod
    def _update_hum_sensor(state):
        """Parse humidity sensor value."""
        _LOGGER.debug("Updating humidity sensor with value %s", state.state)

        # Return an error if the sensor change its state to Unknown.
        if state.state == STATE_UNKNOWN:
            _LOGGER.error(
                "Unable to parse humidity sensor %s, state: %s",
                state.entity_id,
                state.state,
            )
            return None

        if (hum := util.convert(state.state, float)) is None:
            _LOGGER.error(
                "Unable to parse humidity sensor %s, state: %s",
                state.entity_id,
                state.state,
            )
            return None

        if (unit := state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)) != PERCENTAGE:
            _LOGGER.error(
                "Humidity sensor %s has unsupported unit: %s %s",
                state.entity_id,
                unit,
                " (allowed: %)",
            )
            return None

        if hum > 100 or hum < 0:
            _LOGGER.error(
                "Humidity sensor %s is out of range: %s %s",
                state.entity_id,
                hum,
                "(allowed: 0-100%)",
            )
            return None

        return hum

    async def async_update(self):
        """Calculate latest state."""
        _LOGGER.debug("Update state for %s", self.entity_id)
        # check all sensors
        if None in (self._temperature, self._humidity):
            self._available = False
            self._state = None
            return

        # re-calculate dew point
        self._calc_dewpoint()
        self._available = self._state is not None

    def _calc_dewpoint(self):
        """Calculate the dew point for the indoor air."""
        # Use magnus approximation to calculate the dew point
        alpha = MAGNUS_K2 * self._temperature / (MAGNUS_K3 + self._temperature)
        beta = MAGNUS_K2 * MAGNUS_K3 / (MAGNUS_K3 + self._temperature)

        if self._humidity == 0:
            dew_point = -50  # not defined, set very low
        else:
            dew_point = (
                MAGNUS_K3
                * (alpha + math.log(self._humidity / 100.0))
                / (beta - math.log(self._humidity / 100.0))
            )
        
        dew_point = round(dew_point, 1)
        self._state = (
            dew_point 
            if self._is_metric 
            else util.temperature.celsius_to_fahrenheit(dew_point)
        )
        _LOGGER.debug(
            "Dew point: %f %s", self._state, self.native_unit_of_measurement
        )

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS if self._is_metric else TEMP_FAHRENHEIT

    @property
    def native_value(self):
        """Return the state of the entity."""
        return self._state

    @property
    def available(self):
        """Return the availability of this sensor."""
        return self._available
