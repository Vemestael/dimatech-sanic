# dimatech-sanic
## About

Test assignment for DimaTech Ltd.

Developed using the asynchronous Sanic framework and the SQLAlchemy ORM.

## Installation and using

This project provides you a working sanic environment without requiring you to install Python/Sanic, a web server, and any other server software on your local machine. For this, it requires Docker and Docker Compose.

1. Install [Docker](https://docs.docker.com/engine/installation/) and [Docker-compose](https://docs.docker.com/compose/install/);

2. Clone this project and then cd to the project folder;

3. Create your own .env file by copying .env.example:
    ```sh
    $ cp src/.env.default src/.env
    ```

4. Update the environment variables in the docker-compose.yml and .env files.

5. Build the images and run the containers:
     ```sh
    $ docker-compose -f docker-compose.yml up -d --build
    ```

6. You've done! Main page is available on http://localhost, pgAdmin on http://localhost:2345 (login: admin@admin.com, password: postgres)

7. After finishing work, you can stop running containers:
    ```sh
    $ docker-compose down
    ```

## Site with ssl certificate

To use it, you must have a server and a domain configured

1. Create a nginx configuration file to handle ssl:
    ```sh
    $ mkdir conf.d
    $ cp ./Docker/nginx/nginx.prod.conf ./conf.d/nginx.conf
    ```

2. Update the environment variables:

    2.1.  In the docker-compose.yml variable "CERTBOT_EMAIL"

    2.2. In the conf.d/nginx.conf variable "server_name"

3. Build the images and run the containers:
     ```sh
    $ docker-compose -f docker-compose.prod.yml up -d --build
    ```

4. You've done! Main page is available on https://your_web_site

## Testing

To use the site, you have access to the main addresses:


*/v1/api/products/* - for viewing and editing products

   ```
   Required request fields for POST method
   title: text
   description: text
   price: float
   ```

*/v1/api/bills/* - to view and edit customer bills

   ```
   Required request fields for POST method
   user_id: int
   bill_balance: float
   ```

*/v1/api/transactions/* - to view and edit transactions

   ```
   Required request fields for POST method
   user_id: int
   bill_id: int
   amount: float
   ```

*/v1/api/purchases/* - to view and edit purchases

   ```
   Required request fields for POST method
   product_id: int
   user_id: int
   bill_id: int
   ```

GET */v1/auth/users/* - for viewing users

POST */v1/auth/users/* - for creating users

   ```
   Required request fields for POST method
   username: text
   password: text
   ```

PATCH */v1/auth/users/{id}/* - for editing users
   ```
   Request fields
   password: text
   email: int
   is_active: bool - to enable/disable the user
   is_admin: bool - to enable/disable admin role
   ```

GET */v1/auth/activate/{token}/* - for activating users

POST */v1/auth/login/* - to create a jwt token

   ```
   Required request fields for POST method
   username: text
   password: text
   ```

POST */v1/payment/webhook* - for sending webhook of transactions

   ```
   Required request fields for POST method
   signature: text
   transaction_id: int
   user_id: int
   bill_id: int
   amount: float
   ```

*host:2345/* - pgAdmin for interaction with the database tables (login: admin@admin.com, password: postgres)

**Note**: default users can view accounts, transactions and purchases associated with them. Administrators can view the data of all users

The initial administrator is assigned in the database, subsequent ones in the database or by changing the is_admin field of a certain user

## License

This project is licensed under the [MIT license](LICENSE).
