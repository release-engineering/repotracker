FROM fedora:28
LABEL \
    name="repotracker" \
    vendor="Factory 2.0" \
    license="GPLv3"
CMD ["/usr/bin/repotracker"]
RUN curl https://password.corp.redhat.com/RH-IT-Root-CA.crt > /etc/pki/ca-trust/source/RH-IT-Root-CA.crt && update-ca-trust 
COPY eng-fedora-28.repo /etc/yum.repos.d/
RUN dnf -y install python3-pip python3-rhmsg skopeo && dnf -y clean all
WORKDIR /src
COPY . .
RUN python3 setup.py install
USER 1001
