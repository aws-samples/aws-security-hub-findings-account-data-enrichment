# coding: utf-8
import pprint
import re  # noqa: F401

import six
from enum import Enum

class SecurityHubFindingsImported(object):


    _types = {
        'findings': 'object'
    }

    _attribute_map = {
        'findings': 'findings'
    }

    def __init__(self, findings=None):  # noqa: E501
        self._findings = None
        self.discriminator = None
        self.findings = findings


    @property
    def findings(self):

        return self._findings

    @findings.setter
    def findings(self, findings):


        self._findings = findings

    def to_dict(self):
        result = {}

        for attr, _ in six.iteritems(self._types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(SecurityHubFindingsImported, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, SecurityHubFindingsImported):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

