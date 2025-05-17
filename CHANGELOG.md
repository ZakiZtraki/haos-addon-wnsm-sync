# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [1.2.17](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.16...v1.2.17) (2025-05-17)

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

### [1.2.8](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.7...v1.2.8) (2025-05-16)

### [1.2.7](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.6...v1.2.7) (2025-05-16)


### Bug Fixes

* update date handling in bewegungsdaten retrieval ([b1d073b](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/b1d073baad151674fab1dbe686f79e603c615130))

### [1.2.6](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.5...v1.2.6) (2025-05-16)


### Bug Fixes

* improve handling of missing environment variables in sync script ([89f09be](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/89f09bee69c3b222717f6795cf7a78fd0996e8cd))

### [1.2.5](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.4...v1.2.5) (2025-05-16)


### Bug Fixes

* improve error handling for missing environment variables in sync script ([74820bd](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/74820bdaab25a25f3006371999877670da7df25a))

### [1.2.4](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.3...v1.2.4) (2025-05-16)


### Bug Fixes

* dynamically build form data for login in Smartmeter client ([dac7c74](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/dac7c746161c4998793276b3033959acf0f9e092))
* enhance environment variable handling and debug output in sync script ([2ba8544](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/2ba8544f386803f2f49b87faba18d0249846b7ab))

### [1.2.3](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.2...v1.2.3) (2025-05-16)


### Bug Fixes

* corrected syntax error in debug output for password length ([933f502](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/933f502c9da12a29d12c7ba2e18f8a9c75902d43))

### [1.2.2](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.1...v1.2.2) (2025-05-16)


### Bug Fixes

* removed env var exports for home assistant ([0176385](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/0176385e24436039bae89c66543c9cef3748b6e5))

### [1.2.1](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.2.0...v1.2.1) (2025-05-16)


### Bug Fixes

* corected env var notation for home assistant ([96edf2c](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/96edf2cb0fc156ce571b919a0f033d8917a76e98))

## [1.2.0](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.1.6...v1.2.0) (2025-05-16)


### Features

* enhance run.sh with environment variable exports and debugging information ([9de4157](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/9de4157c089e0b891307ed83c88ca6e21643e4b2))

### [1.1.6](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.1.5...v1.1.6) (2025-05-16)

### [1.1.5](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.1.4...v1.1.5) (2025-05-16)


### Bug Fixes

* correct 'map' field with named environment bindings ([7b69fcb](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/7b69fcb0db9b79e11f5ee4428d1988aac37dbaaf))

### [1.1.4](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.1.3...v1.1.4) (2025-05-16)


### Bug Fixes

* correct map format for Supervisor env injection ([8395c52](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/8395c527fe248fa472c971ebe6f556b58b876a11))

### [1.1.3](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.1.2...v1.1.3) (2025-05-16)


### Bug Fixes

* inject HA options into environment with map directive ([e32a7e2](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/e32a7e23d28e87cb118dcd92c1477275527c3b72))

### [1.1.2](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.1.1...v1.1.2) (2025-05-16)

### [1.1.1](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.1.0...v1.1.1) (2025-05-16)


### Bug Fixes

* map HA config options to container environment variables ([c489d9d](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/c489d9d2716633db89e5dabf1edb95c62ae0999a))

## [1.1.0](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.0.3...v1.1.0) (2025-05-16)


### Features

* add debug output for environment variables in run.sh ([f5d1477](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/f5d14770555a3e3ab5b3b6ff71332450579a649e))

### [1.0.2](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/compare/v1.0.1...v1.0.2) (2025-05-14)

### 1.0.1 (2025-05-14)


### Bug Fixes

* add login debug output for Smartmeter client ([2527c0b](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/2527c0bbe0fdc639f8c2cd4580cb3ff500f35aba))
* add startup logging to trace silent failures ([9b06a84](https://github.com/ZakiZtraki/homeassistant-addon-wnsm-sync/commit/9b06a848852b554bf496fcf33a4a6a323c40eb3f))

### 1.0.1 (2025-05-14)

### 1.0.1 (2025-05-14)