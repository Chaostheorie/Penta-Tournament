# Frontend

- The Frontend is buildt with PyQt5 as main GUI Libary and handles via the requests libary the communication with the "Backend" via http(s)
- It doesn't contain any of the direct logic and acts as pure Frontend
- With `fbs` you can create installers e.g. .deb, .exe

## fbs

fbs provides the libary around resource, icon and packaging managment and is via the ApplicationContext as the core part of he frontend to PyQt5 integrated

The python files are located in `src/main/python`. With `fbs run` will a development run be started and the application is ready to be used. With `fbs freeze` an exeutable will be created at `target`. Eventually `fbs installer` will to the packaging and create the installers.
