FROM registry.fedoraproject.org/fedora:36

LABEL \
    name="repotracker" \
    vendor="EXD SP" \
    maintainer="C3I Guild <exd-guild-c3i@redhat.com>" \
    license="GPLv3" \
    description="A microservice for tracking container repositories, and publishing a message when they change." \
    usage="https://github.com/release-engineering/repotracker"

ARG DNF_CMD="dnf -y --setopt=deltarpm=0 --setopt=install_weak_deps=false --setopt=tsflags=nodocs"

CMD ["/usr/bin/repotracker"]

COPY repos/ /etc/yum.repos.d/
RUN ${DNF_CMD} install python3-pip python3-requests python3-service-identity python3-rhmsg skopeo && dnf -y clean all
WORKDIR /src
COPY . .
RUN python3 setup.py install --prefix /usr

USER 1001
