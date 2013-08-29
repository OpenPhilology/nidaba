Installing Iris
===
Pull from Github
---
Navigate to `/opt` and `git glone` the Iris repository. 

*(Back-end to come)*

Apache Configuration
---
To install Apache2, run:
`apt-get install apache2`

Next we'll use a symbolic link to Iris' Apache conf file:
`ln -s /opt/Iris/iris/extras/apache/iris.conf /etc/apache2/sites-available/iris.conf`
`a2ensite iris.conf`

Finally, enable the mod_rewrite module and restart Apache:
`a2enmod rewrite`
`service apache2 restart`

Frontend Dependencies
---
Apart from the included files, alterations to Iris' CSS require SASS to be installed. This can be installed with `gem install sass`. 
