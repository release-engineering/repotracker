FROM registry.fedoraproject.org/fedora:latest

LABEL \
    name="repotracker" \
    vendor="Red Hat Software Production" \
    maintainer="C3I Guild <exd-guild-c3i@redhat.com>" \
    license="GPLv3" \
    description="A microservice for tracking container repositories, and publishing a message when they change." \
    usage="https://github.com/release-engineering/repotracker"

ARG DNF_CMD="dnf -y --repo=fedora,updates --setopt=deltarpm=False --setopt=install_weak_deps=False --setopt=tsflags=nodocs"
ARG PIP_CMD="python3 -m pip install -v --no-build-isolation --no-cache-dir --prefix=/usr --compile"

ARG RHMSG_REPO="https://gitlab.cee.redhat.com/exd-guild-messaging/rhmsg.git"
ARG RHMSG_REF="refs/heads/master"
ARG RHMSG_COMMIT="FETCH_HEAD"
ARG RHMSG_DEPTH="10"

ENV \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    REQUESTS_CA_BUNDLE=/etc/pki/tls/cert.pem

CMD ["/usr/bin/repotracker"]

ADD https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem \
    /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust

RUN $DNF_CMD install python3-pip \
                     python3-qpid-proton git-core skopeo && \
    $DNF_CMD clean all
RUN $PIP_CMD --upgrade setuptools setuptools_scm wheel

WORKDIR /src/repotracker
COPY . .
RUN $PIP_CMD -r requirements.txt
RUN $PIP_CMD --no-deps .

WORKDIR /src/rhmsg
RUN git init . && \
    git fetch --depth=$RHMSG_DEPTH $RHMSG_REPO \
        "${RHMSG_REF}:refs/remotes/origin/${RHMSG_REF##*/}" && \
    git checkout "$RHMSG_COMMIT"
RUN $PIP_CMD .

WORKDIR /
USER 1001
