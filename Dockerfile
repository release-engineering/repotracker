FROM fedora:28
LABEL \
    name="repotracker" \
    vendor="Factory 2.0" \
    license="GPLv3"
CMD ["/usr/bin/repotracker"]
COPY repos/ /etc/yum.repos.d/
RUN dnf -y install python3-pip python3-rhmsg skopeo && dnf -y clean all
WORKDIR /src
COPY . .
RUN python3 setup.py install --prefix /usr
USER 1001
