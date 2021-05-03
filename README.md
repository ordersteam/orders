[![Build Status](https://travis-ci.com/ordersteam/orders.svg?branch=main)](https://travis-ci.com/ordersteam/orders)
[![codecov](https://codecov.io/gh/ordersteam/orders/branch/main/graph/badge.svg?token=L9IGNC3ISH)](https://codecov.io/gh/ordersteam/orders)

# orders
- Repo for Orders microservice (A collection of order items created from products and quantity)
- Part of NYU DevOps Spring 2021
## Introduction
 This repository contains the code for the Orders squad. This is part of the larger effort to design the back end of an ecommerce website
 as a Collection of RESTful services to the client

 ## Prerequisite Installation using Vagrant VM

The easiest way to use this lab is with **Vagrant** and **VirtualBox**. if you don't have this software the first step is down download and install it.

Download [VirtualBox](https://www.virtualbox.org/)

Download [Vagrant](https://www.vagrantup.com/)

Then all you have to do is clone this repo and invoke vagrant:

```bash
    git clone https://github.com/ordersteam/orders.git
    cd orders
    vagrant up
    vagrant ssh
    cd /vagrant
    FLASK_APP=service:app flask run -h 0.0.0.0
```

You can also automatically set the environment variable FLASK_APP using a `.env` file as is done in the code
There is an example in this repo called `dot-env-example` that you can simply copy.

```sh
    cp dot-env-example .env
```

The `.env` file will be loaded when you do `flask run` so that you don't have to specify
any environment variables.

You can also use Docker as a provider instead of VirtualBox. This is useful for owners of Apple M1 Silicon Macs which cannot run VirtualBox because they have a CPU based on ARM architecture instead of Intel.

Just add `--provider docker` to the `vagrant up` command like this:

```sh
vagrant up --provider docker
```

This will use a Docker container instead of a Virtual Machine (VM).

## Alternate install using VSCode and Docker

You can also develop in Docker containers using VSCode. This project contains a `.devcontainer` folder that will set up a Docker environment in VSCode for you. You will need the following:

- Docker Desktop for [Mac](https://docs.docker.com/docker-for-mac/install/) or [Windows](https://docs.docker.com/docker-for-windows/install/)
- Microsoft Visual Studio Code ([VSCode](https://code.visualstudio.com/download))
- [Remote Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) VSCode Extension

It is a good idea to add VSCode to your path so that you can invoke it from the command line. To do this, open VSCode and type `Shift+Command+P` on Mac or `Shift+Ctrl+P` on Windows to open the command palete and then search for "shell" and select the option **Shell Command: Install 'code' command in Path**. This will install VSCode in your path.

Then you can start your development environment up with:

```bash
    git clone https://github.com/ordersteam/orders.git
    cd orders
    code .
```

The first time it will build the Docker image but after that it will just create a container and place you inside of it in your `/workspace` folder which actually contains the repo shared from your computer. It will also install all of the VSCode extensions needed for Python development.

If it does not automatically prompt you to open the project in a container, you can select the green icon at the bottom left of your VSCode UI and select: **Remote Containers: Reopen in Container**.

## Alternate manual install using local Python

If you have Python 3 installed on your computer you can make a virtual environment and run the code locally with:

```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    FLASK_APP=service:app flask run
```
## Manually running the Tests

Run the tests using `nosetests`

```bash
  $ nosetests --with-spec --spec-color
```

**Notes:** the parameter flags `--with-spec --spec-color` add color so that red-green-refactor is meaningful. If you are in a command shell that supports colors, passing tests will be green while failing tests will be red. The flag `--with-coverage` is automatically specified in the `setup.cfg` file so that code coverage is included in the tests.

The Code Coverage tool runs with `nosetests` so to see how well your test cases exercise your code just run the report:

```bash
  $ coverage report -m
```

This is particularly useful because it reports the line numbers for the code that is not covered so that you can write more test cases.

To run the service use `flask run` (Press Ctrl+C to exit):

```bash
  $ FLASK_APP=service:app flask run -h 0.0.0.0
```

You must pass the parameters `-h 0.0.0.0` to have it listed on all network adapters to that the post can be forwarded by `vagrant` to your host computer so that you can open the web page in a local browser at: http://localhost:5000

Alternatively, honcho start can be used to start the service.

The BDD tests can be run manually by 
```bash
  $ behave
```
assuming the service is up and running.

## Vagrant shutdown

If you are using Vagrant and VirtualBox, when you are done, you should exit the virtual machine and shut down the vm with:

```bash
 $ exit
 $ vagrant halt
```

If the VM is no longer needed you can remove it with:

```bash
  $ vagrant destroy
```

### IBM Cloud deployment
The code has been deployed to IBM Cloud using the details in the mainfest.yml file.  An automated workflow has been set up to trigger deployment to dev and run BDD tests followed by deployment to prod if the tests pass.

### Database Schema

Database Used: PostgreSQL 

### Order:

|  Column  |  Type  | Constraints  |
| :---------: | :---------: | :------------: | 
| id | Integer | Primary Key |
| customer_id | Integer | |
| creation_date | Datetime | |
| order_total | Float | |

### Item:

|  Column  |  Type  | Constraints  |
| :----------: | :---------: | :------------: | 
| item_id | Integer | Primary Key |
| product_id | Integer | |
| price | Float | |
| quantity | Integer | |
| status   |  String || PLACED, SHIPPED, DELIVERED, CANCELLED ||
| order_id | Integer | Foreign Key |
| item_total | Float | |


### APIs Supported

Order related APIs
| Endpoint       |    Method  | Path          |                      Description
|----------------|-------|-------------|     -------------------------
| index        |      GET    |  /          |                List all the available URLs  
| create_orders | POST   |   /orders  |  Create an order with the data posted 
| list_orders   |  GET     |  /orders            |             Return list  of the Orders with relevant information
| get_orders    | GET    |  /orders/\<int:order_id>       |   Retrieve information about an Order
| get_customer_orders| GET | /orders?customer_id=<int:customer_id >| Retrieve orders of customer
| sort_orders |  GET  | /orders?sort=<int: criteria>&sort_by=<int: sort_type>'   | Retrieve orders based on criteria after sorting
| update_orders | PUT    | /orders/\<int:order_id>      |   Update an Order based on the info posted.
| delete_orders   |   DELETE | /orders/\<int:order_id>   |    Delete a specific order
| cancel_order    |   PUT    | /orders/\<int:order_id>/cancel |   Cancel items in the order

Item related APIs
| Endpoint       |    Method  | Path          |                      Description
|----------------|-------|-------------|     -------------------------
| get_item  | GET | /orders/\<int:order_id>/items/\<int:item_id>  | Retrieve information on specific item in an order
| add_order_item  |  POST | /orders/\<int:order_id>/items/  | Add a specific item in an order
| update_order_item  | PUT | /orders/\<int:order_id>/items/\<int:item_id>  | Update a specific item in an order
| delete_order_item  | DELETE | /orders/\<int:order_id>/items/\<int:item_id>  | Delete a specific item in an order
| cancel_order_item  | PUT | /orders/\<int:order_id>/items/\<int:item_id>/cancel  | Cancel a specific item in an order






