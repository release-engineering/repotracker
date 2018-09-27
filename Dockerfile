FROM fedora:28
LABEL \
    name="repotracker" \
    vendor="Factory 2.0" \
    license="GPLv3"
CMD ["/usr/bin/repotracker"]
COPY eng-fedora-28.repo /etc/yum.repos.d/
RUN dnf -y install python3-pip python3-rhmsg skopeo && dnf -y clean all
WORKDIR /src
COPY . .
RUN python3 setup.py install
RUN mkdir -p /var/lib/repotracker/containers
USER 1001
