"""
    :codeauthor: Gareth J. Greenaway <ggreenaway@vmware.com>
"""


import os

import pytest
import salt.modules.pkg_resource as pkg_resource
import salt.modules.zypperpkg as zypper
from salt.exceptions import SaltInvocationError
from tests.support.mock import MagicMock, mock_open, patch


@pytest.fixture
def configure_loader_modules():
    return {zypper: {"rpm": None}, pkg_resource: {}}


def test_list_pkgs_no_context():
    """
    Test packages listing.

    :return:
    """

    def _add_data(data, key, value):
        data.setdefault(key, []).append(value)

    rpm_out = [
        "protobuf-java_|-(none)_|-2.6.1_|-3.1.develHead_|-noarch_|-(none)_|-1499257756",
        "yast2-ftp-server_|-(none)_|-3.1.8_|-8.1_|-x86_64_|-(none)_|-1499257798",
        "jose4j_|-(none)_|-0.4.4_|-2.1.develHead_|-noarch_|-(none)_|-1499257756",
        "apache-commons-cli_|-(none)_|-1.2_|-1.233_|-noarch_|-(none)_|-1498636510",
        "jakarta-commons-discovery_|-(none)_|-0.4_|-129.686_|-noarch_|-(none)_|-1498636511",
        "susemanager-build-keys-web_|-(none)_|-12.0_|-5.1.develHead_|-noarch_|-(none)_|-1498636510",
        "gpg-pubkey_|-(none)_|-39db7c82_|-5847eb1f_|-(none)_|-(none)_|-1519203802",
        "gpg-pubkey_|-(none)_|-8a7c64f9_|-5aaa93ca_|-(none)_|-(none)_|-1529925595",
        "kernel-default_|-(none)_|-4.4.138_|-94.39.1_|-x86_64_|-(none)_|-1529936067",
        "kernel-default_|-(none)_|-4.4.73_|-5.1_|-x86_64_|-(none)_|-1503572639",
        "perseus-dummy_|-(none)_|-1.1_|-1.1_|-i586_|-(none)_|-1529936062",
    ]
    with patch.dict(zypper.__grains__, {"osarch": "x86_64"}), patch.dict(
        zypper.__salt__, {"cmd.run": MagicMock(return_value=os.linesep.join(rpm_out))},
    ), patch.dict(zypper.__salt__, {"pkg_resource.add_pkg": _add_data}), patch.dict(
        zypper.__salt__, {"pkg_resource.format_pkg_list": pkg_resource.format_pkg_list},
    ), patch.dict(
        zypper.__salt__, {"pkg_resource.stringify": MagicMock()}
    ), patch.object(
        zypper, "_list_pkgs_from_context"
    ) as list_pkgs_context_mock:
        pkgs = zypper.list_pkgs(versions_as_list=True, use_context=False)
        list_pkgs_context_mock.assert_not_called()
        list_pkgs_context_mock.reset_mock()

        pkgs = zypper.list_pkgs(versions_as_list=True, use_context=False)
        list_pkgs_context_mock.assert_not_called()
        list_pkgs_context_mock.reset_mock()


def test_normalize_name():
    """
    Test that package is normalized only when it should be
    """
    with patch.dict(zypper.__grains__, {"osarch": "x86_64"}):
        result = zypper.normalize_name("foo")
        assert result == "foo", result
        result = zypper.normalize_name("foo.x86_64")
        assert result == "foo", result
        result = zypper.normalize_name("foo.noarch")
        assert result == "foo", result

    with patch.dict(zypper.__grains__, {"osarch": "aarch64"}):
        result = zypper.normalize_name("foo")
        assert result == "foo", result
        result = zypper.normalize_name("foo.aarch64")
        assert result == "foo", result
        result = zypper.normalize_name("foo.noarch")
        assert result == "foo", result


def test_get_repo_keys():
    salt_mock = {"lowpkg.list_gpg_keys": MagicMock(return_value=True)}
    with patch.dict(zypper.__salt__, salt_mock):
        assert zypper.get_repo_keys(info=True, root="/mnt")
        salt_mock["lowpkg.list_gpg_keys"].assert_called_once_with(True, "/mnt")


def test_add_repo_key_fail():
    with pytest.raises(SaltInvocationError):
        zypper.add_repo_key()

    with pytest.raises(SaltInvocationError):
        zypper.add_repo_key(path="path", text="text")


def test_add_repo_key_path():
    salt_mock = {
        "cp.cache_file": MagicMock(return_value="path"),
        "lowpkg.import_gpg_key": MagicMock(return_value=True),
    }
    with patch("salt.utils.files.fopen", mock_open(read_data="text")), patch.dict(
        zypper.__salt__, salt_mock
    ):
        assert zypper.add_repo_key(path="path", root="/mnt")
        salt_mock["cp.cache_file"].assert_called_once_with("path", "base")
        salt_mock["lowpkg.import_gpg_key"].assert_called_once_with("text", "/mnt")


def test_add_repo_key_text():
    salt_mock = {"lowpkg.import_gpg_key": MagicMock(return_value=True)}
    with patch.dict(zypper.__salt__, salt_mock):
        assert zypper.add_repo_key(text="text", root="/mnt")
        salt_mock["lowpkg.import_gpg_key"].assert_called_once_with("text", "/mnt")


def test_del_repo_key():
    salt_mock = {"lowpkg.remove_gpg_key": MagicMock(return_value=True)}
    with patch.dict(zypper.__salt__, salt_mock):
        assert zypper.del_repo_key(keyid="keyid", root="/mnt")
        salt_mock["lowpkg.remove_gpg_key"].assert_called_once_with("keyid", "/mnt")
