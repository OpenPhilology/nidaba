Installing Iris
===
This guide will assume that you have cloned Iris into your `/opt` directory and are running Ubuntu 12.04. If you choose to install Iris elsewhere on your system, you will have to modify paths in several places.


Cloning the Iris Repository
---
Navigate to `/opt` and clone the Iris repository. 

    git clone git@github.com:OpenPhilology/Iris.git
    
***

Backend Dependencies
---
*Coming Soon*


***

Apache Configuration
---
To install Apache2, run:

    apt-get install apache2

Next we'll use a symbolic link to Iris' Apache conf file:

    ln -s /opt/Iris/iris/extras/apache/iris.conf /etc/apache2/sites-available/iris.conf
    a2ensite iris.conf

Finally, enable the mod_rewrite module and restart Apache:

    a2enmod rewrite
    service apache2 restart


***

Frontend Dependencies
---
Apart from the included files, alterations to Iris' CSS require SASS to be installed. This can be installed with:

    gem install sass
    
Any changes to SASS CSS file, located in `Iris/iris/templates/static/css/style.scss` will require the main CSS to be recompiled. To automate this, run:

    cd /opt/Iris/iris/static/css
    sass --watch style.scss:style.css
