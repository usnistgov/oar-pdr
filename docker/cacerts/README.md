This directory contains non-standard CA certificates needed to build the docker
images. 

Failures building the Docker containers defined in ../ due to SSL certificate
verification errors may be a consequence of your local network's firewall.  In
particular, the firewall may be substituting external site certificates with
its own signed by a non-standard CA certficate (chain).  If so, you can place 
the necessary certificates into this directory; they will be passed into the
containers, allowing them to safely connect to those external sites.

Be sure the certificates are in PEM format and include a .crt file extension.

Do not remove this README file; doing so may cause a Docker build faiure.
