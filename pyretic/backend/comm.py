
################################################################################
# The Pyretic Project                                                          #
# frenetic-lang.org/pyretic                                                    #
# author: Joshua Reich (jreich@cs.princeton.edu)                               #
################################################################################
# Licensed to the Pyretic Project by one or more contributors. See the         #
# NOTICES file distributed with this work for additional information           #
# regarding copyright and ownership. The Pyretic Project licenses this         #
# file to you under the following license.                                     #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided the following conditions are met:       #
# - Redistributions of source code must retain the above copyright             #
#   notice, this list of conditions and the following disclaimer.              #
# - Redistributions in binary form must reproduce the above copyright          #
#   notice, this list of conditions and the following disclaimer in            #
#   the documentation or other materials provided with the distribution.       #
# - The names of the copyright holds and contributors may not be used to       #
#   endorse or promote products derived from this work without specific        #
#   prior written permission.                                                  #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT    #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the     #
# LICENSE file distributed with this work for specific language governing      #
# permissions and limitations under the License.                               #
################################################################################

import asynchat
import asyncore
import socket

import json
import sys

py2 = False

if sys.version_info[0] == 2:
    py2 = True

BACKEND_PORT=41414
TERM_CHAR=b'\n'

def serialize(msg):
    jsonable_msg = to_jsonable_format(msg)
    jsoned_msg = json.dumps(jsonable_msg)
    serialized_msg = jsoned_msg.encode('latin') + TERM_CHAR
    return serialized_msg

def deserialize(serialized_msgs):
    def json2python(item):
        if isinstance(item, str):
            return item
        elif isinstance(item, bytes):
            return item.decode('latin')
        elif isinstance(item, dict):
            ret = {}
            for k, v in item.items():
                if k in ['srcmac','dstmac','srcip','dstip']:
                    ret[k] = ''.join([chr(d) for d in v])
                elif k in ['raw']:
                    if py2:
                        ret[k] = ''.join([chr(d) for d in v])
                    else:
                        ret[k] = bytes(v)
                else:
                    ret[json2python(k)] = json2python(v)
            return ret
        elif isinstance(item, list):
            return [json2python(l) for l in item]
        else:
            return item

    serialized_msg = serialized_msgs.pop(0)
    jsoned_msg = serialized_msg.rstrip(TERM_CHAR).decode('latin')
    msg = None
    while True:
        try:
            msg = json.loads(jsoned_msg)
            msg = json2python(msg)
            break
        except:
            if len(serialized_msgs) == 0:
                break
            next_part = serialized_msgs.pop(0).rstrip(TERM_CHAR).decode('latin')
            jsoned_msg += next_part
    return msg


def dict_to_ascii(d):
    def convert(h,v):
        if (isinstance(v,str) or
            isinstance(v,int)):
            return v
        elif isinstance(v, bytes):
            return list(v)
        else:
            return repr(v)
    return { h : convert(h,v) for (h,v) in list(d.items()) }


def ascii2bytelist(packet_dict):
    def convert(h,val):
        if h in ['srcmac','dstmac','srcip','dstip']:
            return [ord(c) for c in val]
        elif h in ['raw'] and py2:
            if py2:
                return [ord(c) for c in val]
            else:
                return val
        else:
            return val
    return { h : convert(h,val) for (h, val) in list(packet_dict.items())}


def to_jsonable_format(item):
    if isinstance(item, dict):
        ascii_item = dict_to_ascii(item)
        bytelist_item = ascii2bytelist(ascii_item)
        return bytelist_item
    elif isinstance(item, list):
        return list(map(to_jsonable_format,item))
    else:
        return item
