# Penta-Tournament

Web app for managing of Penta Game tournaments

## Feature List

- Managing of tournaments by using switzer system
- Log results of players by account system
- Organizing evemts and making announcments over rules (rulesets) for events
- Getting Intel about the next event in the Penta Game world

## GUI app

- Python 3.6+
- PyQt5 gui applicatin (through fbs) for Linux/ MacOS and Windows
- RESTful API backend with User authentification and token based session implementation

## WebAPI

- RESTful web API with Role based Authorization

![](https://github.com/Chaostheorie/Penta-Tournament/blob/master/diagram.svg)

- Allows the client (and everyone else) to access te full data

For everything else like License etc. See credits.txt in frontend/src/main/resources/base

# Installation

Penta Tournament consists of two different parts. At the moment the `Frontend` points all of the requests to `http://localhost/api` e.g. the `Backend` Flask server should be running on the same machine. This will be changed in the future

First clone/ download the repository:

```bash
git clone https://github.com/Chaostheorie/Penta-Tournament.git && cd Penta-Tournament
```

For installation of the dependencies for the RESTful API start with:

```bash
pip3 install -r Backend/requirements.txt
```

Now you can run a local development Flask server:

```bash
cd Backend && python3 main.py
```

Now open a new bash/ shell and go to the the `Penta-Tournament/Frontend` and execute:

```bash
pip3 install -r Backend/requirements.txt
```

Now you need to start the application with:

```bash
fbs run
```

IMPORTANT NOTICE: if the build is broken or throws errors please don't email me and instead create a issue. It could happen that the application throws debug at you.
