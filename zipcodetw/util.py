#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

class Address(object):

    TOKEN_RE = re.compile(u'''
        (?:
            (?P<no>\d+)
            (?:[之-](?P<subno>\d+))?
            |
            (?P<name>.+?)
        )
        (?:
            [,，]
            |
            (?P<unit>[縣市鄉鎮市區村里路段街巷弄號樓])[,，]?
        )
    ''', re.X)

    NO    = 0
    SUBNO = 1
    NAME  = 2
    UNIT  = 3

    @staticmethod
    def normalize(s):
        if isinstance(s, str):
            s = s.decode('utf-8')
        return s.replace(u' ', u'').replace(u'　', u'')

    @staticmethod
    def tokenize(addr_str):
        return tuple(Address.TOKEN_RE.findall(Address.normalize(addr_str)))

    def __init__(self, addr_str):

        self.addr_str = addr_str
        self.tokens = Address.tokenize(addr_str)

    def extract_no_pair(self, idx=-1):
        return (
            int(self.tokens[idx][Address.NO]    or 0),
            int(self.tokens[idx][Address.SUBNO] or 0)
        )

    def __repr__(self):
        return 'Address(%r)' % self.addr_str

class AddressRule(Address):

    RULE_TOKEN_RE = re.compile(u'''
        及以上附號|含附號以下|含附號全|含附號
        |
        以下|以上
        |
        附號全
        |
        [連至](?=\d)
        |
        [單雙](?=[\d全])
        |
        全(?=$)
    ''', re.X)

    @staticmethod
    def extract_tokens(addr_rule_str):

        addr_rule_str = Address.normalize(addr_rule_str)

        rule_tokens_list = []

        def extract_token(m):
            token = m.group()
            rule_tokens_list.append(token)
            if token == u'附號全':
                return u'號'
            return ''

        addr_str = AddressRule.RULE_TOKEN_RE.sub(extract_token, addr_rule_str)

        return (tuple(rule_tokens_list), addr_str)

    def __init__(self, addr_rule_str):

        self.addr_rule_str = addr_rule_str
        self.rule_tokens, addr_str = AddressRule.extract_tokens(addr_rule_str)
        Address.__init__(self, addr_str)

    def __repr__(self):
        return 'AddressRule(%r)' % self.addr_rule_str

    def match(self, addr):

        his_no_pair = addr.extract_no_pair()

        if self.tokens:

            start_unit = self.tokens[0][Address.UNIT]
            for i, his_token in enumerate(addr.tokens):
                if his_token[Address.UNIT] == start_unit:
                    break

            j = -1-(u'至' in self.rule_tokens)
            for my_token, his_token in zip(self.tokens[:j], addr.tokens[i:]):
                if my_token != his_token:
                    return False

            my_no_pair = self.extract_no_pair()
            if not self.rule_tokens:
                return his_no_pair == my_no_pair

        for rule_token in self.rule_tokens:

            if rule_token == u'單' and not his_no_pair[0] & 1 == 1:
                return False
            if rule_token == u'雙' and not his_no_pair[0] & 1 == 0:
                return False
            if u'以上' in rule_token and not his_no_pair >= my_no_pair:
                return False
            if u'以下' in rule_token and not his_no_pair <= my_no_pair:
                return False
            if rule_token == u'至' and not self.extract_no_pair(-2) <= his_no_pair <= my_no_pair:
                return False
            if rule_token == u'附號全' and not his_no_pair[1] > 0:
                return False

        return True
