import json
import os
import textwrap

from conan.api.conan_api import ConanAPI
from conans.model.conf import BUILT_IN_CONFS
from conans.test.utils.test_files import temp_folder
from conans.test.utils.tools import TestClient
from conans.util.env import environment_update


def test_missing_subarguments():
    """ config MUST run  with a subcommand. Otherwise, it MUST exits with error.
    """
    client = TestClient()
    client.run("config", assert_error=True)
    assert "ERROR: Exiting with code: 2" in client.out


class TestConfigHome:
    """ The test framework cannot test the CONAN_HOME env-var because it is not using it
    (it will break tests for maintainers that have the env-var defined)
    """
    def test_config_home_default(self):
        client = TestClient()
        client.run("config home")
        assert f"{client.cache.cache_folder}\n" == client.stdout

        client.run("config home --format=text")
        assert f"{client.cache.cache_folder}\n" == client.stdout

    def test_api_uses_env_var_home(self):
        cache_folder = os.path.join(temp_folder(), "custom")
        with environment_update({"CONAN_HOME": cache_folder}):
            api = ConanAPI()
            assert api.cache_folder == cache_folder


def test_config_list():
    """
    'conan config list' shows all the built-in Conan configurations
    """
    client = TestClient()
    client.run("config list")
    for k, v in BUILT_IN_CONFS.items():
        assert f"{k}: {v}" in client.out
    client.run("config list --format=json")
    assert f"{json.dumps(BUILT_IN_CONFS, indent=4)}\n" == client.stdout


def test_config_install():
    tc = TestClient()
    tc.save({'config/foo': ''})
    # This should not fail (insecure flag exists)
    tc.run("config install config --insecure")
    assert "foo" in os.listdir(tc.cache_folder)
    # Negative test, ensure we would be catching a missing arg if it did not exist
    tc.run("config install config --superinsecure", assert_error=True)


def test_config_install_conanignore():
    tc = TestClient()
    conanignore = textwrap.dedent("""
    a/*
    b/c/*
    d/*
    """)
    tc.save({
        'config_folder/.conanignore': conanignore,
        "config_folder/a/test": '',
        'config_folder/abracadabra': '',
        'config_folder/b/bison': '',
        'config_folder/b/a/test2': '',
        'config_folder/b/c/helmet': '',
        'config_folder/d/prix': '',
        'config_folder/d/foo/bar': '',
        'config_folder/foo': ''
    })
    def _assert_config_exists(path):
        assert os.path.exists(os.path.join(tc.cache_folder, path))

    def _assert_config_not_exists(path):
        assert not os.path.exists(os.path.join(tc.cache_folder, path))

    tc.run('config install config_folder')

    _assert_config_not_exists(".conanignore")

    _assert_config_not_exists("a")
    _assert_config_not_exists("a/test")

    _assert_config_exists("abracadabra")

    _assert_config_exists("b")
    _assert_config_exists("b/bison")
    _assert_config_exists("b/a/test2")
    _assert_config_not_exists("b/c/helmet")
    _assert_config_not_exists("b/c")

    _assert_config_not_exists("d/prix")
    _assert_config_not_exists("d/foo/bar")
    _assert_config_not_exists("d")

    _assert_config_exists("foo")

    os.listdir(tc.current_folder)
