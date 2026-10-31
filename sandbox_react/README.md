# React Sandbox — Webpack 4

An independent **React 16** training sandbox from the [WebDev course](../README.md). The code uses Webpack 4, Babel 7, Sass and React, with legacy Jest/Enzyme development dependencies.

## Run locally

Use a compatible Node.js/Yarn toolchain; current Node/npm versions may not work with all pinned historical packages.

```bash
git clone https://github.com/cal2020/webdev.git
cd webdev/sandbox_react
yarn install
yarn start        # development server; see its printed URL (historically port 8000)
```

Edit `src/index.js` and the related React components. `yarn build` creates the configured browser bundle. The package's `yarn test` script is a **placeholder**, even though some Jest/Enzyme dependencies are present; do not claim the exercise has a passing test suite without adding one.

There is no external dataset, model/API credential, procurement connector, hosted demo or verified screenshot gallery. Treat this as archival learning code; upgrade dependencies before public deployment.
