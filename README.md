# SavethePycket_IoT_project
Programming for IoT applications project, year 2022/23

In Programming for IoT Applications course, we set out to revolutionize package delivery in the modern world. Our project, SaveThePycket, represents an opportunity for convenience and security in online shopping.

SaveThePycket is a revolutionary service that facilitates safe delivery of packages, even when recipients are far from home.

HOW IT WORKS:

Through the use of mqtt and Rest protocols, it was possible to manage specially designed boxes installed in common areas of buildings, where postmans can safely deposit packages. Through an easy-to-use Telegram application, recipients receive instant notifications containing the order number, allowing them to choose whether to remotely open the building entrance and the box or wait until they are available to retrieve packages

The SaveThePycket dashboard is a powerful tool that allows both users and administrators to easily monitor the status of the secure boxes in real-time.


HOW TO RUN THE PROJECT:

1. Open the Docker Desktop application
2. Open a prompt inside the project folder and run:
	docker compose build
	docker compose up -d

See the requirements file, where all the required libraries are explained.

DISCLAIMER:

The code provided involves creating one box and only one building. This is because the broker test.mosquitto.org cannot handle all the sensors in multiple boxes at once.
Despite this, the project is perfectly scalable. 

In order to add the sensors related to a new building/box, we need to add a json file for each sensor with the settings related to the box/building of interest

Next add the name of the json file inside the related docker file.

Finally add in the docker_compose.yml file inside "services" the related sensor indicating the name of the container  
