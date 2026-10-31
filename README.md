# WebDev: Web Development Course

This is the source code and training content for Web Development courses taught by [Andrew Smith](https://github.com/andrewsouthpaw/).

## Repository origin, course data and compatibility

This is a **fork/archival copy** of the web-development teaching materials attributed to [Andrew Southpaw](https://github.com/AndrewSouthpaw/webdev). Its folders contain **independent exercises**, not a single production application. The original README's upstream links and instructor voice refer to the upstream course, not necessarily to changes maintained in this fork.

### Where to start

```bash
git clone https://github.com/cal2020/webdev.git
cd webdev
# Browse src/www/ for HTML/CSS/JavaScript examples
# Browse projects/rmdb/ for a React movie-database exercise
```

Some exercises are standalone HTML and can be viewed using `python3 -m http.server 8000`. Node-based examples each have their own dependency manifest—run `npm install` or `yarn install` **inside the specific project**, not blindly in the repository root. The historic course targets older Node/Yarn and web libraries; an up-to-date installation may require version isolation or dependency updates.

### Data and external services

The React movie-database assignment includes exercise instructions and fixture JSON under `projects/rmdb/src/`. Other training files are included as checked-in assets. There is no general paid dataset or AI service to procure for the course. If a specific exercise calls an external API, follow that exercise's own README and obtain a legitimate key before running it. Never commit personal or commercial content from external sites.

### Screenshots and maintenance

Illustrations or example webpage images are course assets, **not proof of a modern live deployment**. Many nested READMEs originate from third-party instructional/vendor content; keep them in sync with upstream and preserve attribution and licensing rather than rewriting them as first-party applications.

## Before you begin

If you're familiar with git, I recommend forking the repo before cloning, so you can keep track of your work.

You can also [download a `.zip` of the repo](https://i.imgur.com/muHwvo2.png) if you're not familiar with git.

<details><summary>For people who have worked with git before</summary>

Start by forking and cloning the repo. If you don't clone the repo, then you won't be able to save your work on exercises to your own cloned repo. Choose to not fork at your own risk.

Once you've cloned the repo, set this repo as the `upstream`

```
$ git remote add upstream https://github.com/AndrewSouthpaw/webdev.git
```

When I update the repo and you want to pull the recent changes in upstream:

```
$ git checkout master
$ git pull upstream master
```

You're encouraged to work on a branch during the course, so you can easily re-play your changes on top of any updates I make by running a little helper script:

```
$ bin/branchupdate
``` 

</details>

## Setup

We're going to walk through installation of the following:

- nvm
- Node.js
- yarn

You can check if you already have what you need:

```bash
$ node -v
# should be >= 14
$ npm -v
# should be >= 7
$ yarn -v
# should be >= 1.22
```

If you already have these installed, then skip ahead.

### `nvm`

**This is for macOS and Linux only. Windows users can just go to [nodejs.org](https://nodejs.org) and install there.**

You can install a single version of Node.js, but the more common practice is to install [`nvm` (Node Version Manager)](https://github.com/nvm-sh/nvm), which allows you manage multiple versions of node on the same system.

```
$ curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
```

Running this command downloads and runs the script in your shell.

Note the output: `nvm` will automatically update one of your profile files in your home directory (`~/.bash_profile`, `~/.zshrc`, `~/.profile`, or `~/.bashrc`, it tries to make a reasonable guess).
 
**Open a fresh shell** and verify you can access `nvm` now:

```shell
$ nvm --version
0.39.1 # or something higher

$ echo $NVM_DIR
/some/path/to/.nvm
```

(In case you're curious and noticed it, `$ which nvm` doesn't work because `nvm` is a function sourced from a shell script and is not an executable binary.)

### Node.js

Now you can download a recent version of Node.js. Node.js goes through lots of iterations, but it releases Long-Term Support (LTS) versions that are promised to be stable and maintained for a long time. The easiest way to get a version:

```shell
$ nvm install 14
``` 

Use `$ nvm ls` to look at all the LTS Node.js versions.

### `npm`

It comes with your Node.js install. Verify the installation with:

```bash
$ npm --version
```

**NB: Avoid `sudo` with `npm`**: If you ever install packages with `npm` and you are prompted to use `sudo`, something has gone wrong. Don't do it, as it will all end in tears and your system can get very messed up. Ask for help.

### `yarn`

`npm` is nice and all, but `yarn` (a competitor to `npm`) is better. Install it this way:

```bash
$ npm install --global yarn
$ yarn -v
```

### Install local dependencies

```bash
$ cd src
$ yarn
```

Now you have all the dependencies!

### Text Editor

You can use your favorite text editor to follow along.

I'm a fan of the [WebStorm](https://www.jetbrains.com/webstorm/) IDE by JetBrains. Free trial, not too expensive, definitely worth the money in my book.

[VS Code](https://code.visualstudio.com/) is the most popular open-source editor.

**What should I choose??** 😧

I think WebStorm is hands down way better.

### Local JS Environment

You can always open a console in Firefox or Chrome and get to a JS REPL.

There's an app called [RunJS](https://runjs.dev/) that allows you to write and evaluate JS, which I'll be using a lot of demonstrations.

### React DevTools (for React class only)

We'll install an extension that makes it easier to debug React apps.

* [Chrome](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
* [Firefox](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)

## Folder Structure

### Slides

Follow along using the links in `/slides` to view the latest version of the slides for this course.

(GitHub isn't the best at version-controlling binary files, so I keep the slides in Google Drive to keep the repo smaller.)

### Exercises

Most of the action lives inside `/src`, that's where you'll be doing most of your exercises. There's a webserver you'll want to run.

```shell
$ cd src
$ yarn start
```

> If you're a Windows user, you may also run into other security blocks like Windows Defender, just go ahead and cancel/ignore/permit any warnings.

Then visit <http://localhost:3000/js/> (the trailing slash matters). This will lead you to various interactive pages and test suites that will be used throughout the course.

Other exercises will have you work with tests. In those cases, open one (or both) files for instructions. You can run the tests by running the commands in the prompt from the `/src` folder.

### For React class

You will build out a project called RMDb. Set up the project by visiting `/projects/rmdb` and installing the dependencies, then running the project:

```shell
$ cd projects/rmdb
$ yarn
$ yarn start
```

The exercises are under [/projects/rmdb/exercises](/projects/rmdb/exercises). Your instructor will inform you of which one to work on next.

Each exercise is cumulative, building on the previous one. There is a reference solution provided at the top of each exercise in case you were unable to complete the previous lab.

### Sandbox (optional)

There's a JS sandbox under `/sandbox`, with a skeleton JS starter project. Go into that directory and follow the `README.md` to get it running.

For React, use `/sandbox_react` which has some additional libraries and setup.
