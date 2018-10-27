# AlexaHome
Personal Python app for Alexa, currently only LEAF related

# Usage
You need to create a folder called "private" within the container folder that contains a certificate.pem and private-key.pem to use a self-signed SSL certificate. That info also needs to be set within the custom Alexa application on Amazon's servers.

Additionally, a config.ini must be made in the private folder containing the login info for the LEAF website/app, structured like this:

```
[get-leaf-info]
username = your-email
password = your-password

```