"""pytest config for dockerspawner tests"""

from unittest import mock

from docker import from_env as docker_from_env
from docker.errors import APIError
import pytest

from jupyterhub.tests.mocking import MockHub

# import base jupyterhub fixtures
from jupyterhub.tests.conftest import app, io_loop, event_loop, ssl_tmpdir  # noqa
from dockerspawner import DockerSpawner, SwarmSpawner, SystemUserSpawner

# make Hub connectable from docker by default
MockHub.hub_ip = "0.0.0.0"


@pytest.fixture
def dockerspawner_configured_app(app):
    """Configure JupyterHub to use DockerSpawner"""
    app.config.DockerSpawner.prefix = "dockerspawner-test"
    # app.config.DockerSpawner.remove = True
    with mock.patch.dict(app.tornado_settings, {"spawner_class": DockerSpawner}):
        yield app

@pytest.fixture
def swarmspawner_configured_app(app):
    """Configure JupyterHub to use DockerSpawner"""
    app.config.SwarmSpawner.prefix = "dockerspawner-test"
    with mock.patch.dict(
        app.tornado_settings, {"spawner_class": SwarmSpawner}
    ), mock.patch.dict(
        app.config.SwarmSpawner, {"network_name": "bridge"}
    ):
        yield app


@pytest.fixture
def systemuserspawner_configured_app(app):
    """Configure JupyterHub to use DockerSpawner"""
    app.config.SwarmSpawner.prefix = "dockerspawner-test"
    with mock.patch.dict(
        app.tornado_settings, {"spawner_class": SystemUserSpawner}
    ):
        yield app


@pytest.fixture(autouse=True, scope="session")
def docker():
    """Fixture to return a connected docker client

    cleans up any containers we leave in docker
    """
    d = docker_from_env()
    try:
        yield d

    finally:
        # cleanup our containers
        for c in d.containers.list(all=True):
            if c.name.startswith("dockerspawner-test"):
                c.stop()
                c.remove()
        try:
            services = d.services.list()
        except APIError:
            # e.g. services not available
            return
        else:
            for s in services:
                if s.name.startswith("dockerspawner-test"):
                    s.remove()
