# RMDb — React Movie Database Exercise

A legacy Create React App **React 17** tutorial project that reads movie records from a local `json-server` fixture API. The exercises live under `exercises/`; the application source lives under `src/`.

## Run the complete local exercise

Requires Node.js/Yarn compatible with the older `react-scripts@4`, `json-server@0.16` and `node-sass@5` dependencies. Use an isolated legacy environment rather than deploying this stack unchanged.

```bash
git clone https://github.com/cal2020/webdev.git
cd webdev/projects/rmdb
yarn install
yarn db            # terminal 1: local JSON API on port 3001
yarn start         # terminal 2: React app on port 3000
```

The `db` script loads `src/db.json` and includes `server/chaosMonkeySlowdown.js` to demonstrate network delays. `yarn db-slow` enables a slower fixture server. `yarn test` starts the Create React App test runner. **No external movie-service subscription or API key is required.**

## How to add data

Edit `src/db.json` and the supplemental `src/extraMovies.json` fixtures. Keep stable movie IDs and ensure poster/image links are valid. These records are training data, not an authoritative commercial movie catalog; respect data and image rights if republishing.

For production, replace the local JSON fixture service with an authenticated backend and verify data licenses. No checked-in screenshot gallery or production deployment is provided. This exercise belongs to the [WebDev course archive](../../README.md).
