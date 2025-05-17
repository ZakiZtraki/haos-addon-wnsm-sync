# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [1.2.16](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.15...v1.2.16) (2025-05-17)

### [1.2.15](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.14...v1.2.15) (2025-05-17)


### Bug Fixes

* validate HA_URL and STATISTIC_ID before POST to prevent silent 404 error ([38a86ee](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/38a86ee296331f033ce73f49d68cd79deab9968b))

### [1.2.14](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.13...v1.2.14) (2025-05-17)


### Bug Fixes

* align sync logic with updated Smartmeter API response structure ('values', 'zeitpunktVon', 'wert') ([d0cce26](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/d0cce262e03093d0917fcb89d65339d9f50bd514))

### [1.2.13](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.8...v1.2.13) (2025-05-17)


### Bug Fixes

* corrected aggregat parameter ([18c6bcc](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/18c6bccd8ace51604f990e355abba136cd02b6a1))
* prevent crash when 'descriptor' key is missing in bewegungsdaten response; add debug print for raw data ([3be1702](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/3be1702437e8d2cc5e26235da23e9ad3134c1c3a))
* replace invalid aggregat value 'V002' with 'NONE' in bewegungsdaten API call ([92277bb](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/92277bb8a05fd3e4cc152788824f05a81d8723be))

### [1.2.12](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.8...v1.2.12) (2025-05-17)


### Bug Fixes

* prevent crash when 'descriptor' key is missing in bewegungsdaten response; add debug print for raw data ([3be1702](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/3be1702437e8d2cc5e26235da23e9ad3134c1c3a))
* replace invalid aggregat value 'V002' with 'NONE' in bewegungsdaten API call ([92277bb](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/92277bb8a05fd3e4cc152788824f05a81d8723be))
