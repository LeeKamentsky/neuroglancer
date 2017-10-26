# @license
# Copyright 2017 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import collections
import numbers
import traceback

import numpy as np
import six

from . import viewer_state
from .json_utils import decode_json, encode_json, json_encoder_default
from .json_wrappers import (JsonObjectWrapper, array_wrapper, optional, text_type, typed_set,
                            typed_string_map, wrapped_property)

_uint64_keys = frozenset(['t', 'v'])
_map_entry_keys = frozenset(['key', 'value'])

MapEntry = collections.namedtuple('MapEntry', ['key', 'value'])

def layer_selected_value(x):
    if isinstance(x, numbers.Number):
        return x
    if isinstance(x, dict):
        if six.viewkeys(x) == _uint64_keys and x.get('t') == 'u64':
            return int(x['v'])
        if six.viewkeys(x) == _map_entry_keys:
            return MapEntry(int(x['key']), int(x['value']))

LayerSelectedValues = typed_string_map(layer_selected_value)

class ActionState(JsonObjectWrapper):
    __slots__ = ()
    viewer_state = viewerState = wrapped_property('viewerState', viewer_state.ViewerState)
    selected_values = selectedValues = wrapped_property('selectedValues', LayerSelectedValues)
    mouse_spatial_coordinates = mouseSpatialCoordinates = wrapped_property(
        'mouseSpatialCoordinates', optional(array_wrapper(np.float32, 3)))
    mouse_voxel_coordinates = mouseVoxelCoordinates = wrapped_property(
        'mouseVoxelCoordinates', optional(array_wrapper(np.float32, 3)))


class Actions(object):
    def __init__(self, set_config):
        self._action_handlers = dict()
        self._set_config = set_config

    def add(self, name, handler):
        self._action_handlers.setdefault(name, set()).add(handler)
        self._update_config()

    def clear(self):
        self._action_handlers.clear()
        self._update_config()

    def remove(self, name, handler):
        handlers = self._action_handlers.get(name)
        if handlers is None:
            return
        handlers.remove(handler)
        if not handlers:
            del self._action_handlers[name]
        self._update_config()

    def _update_config(self):
        self._set_config(six.viewkeys(self._action_handlers))

    def invoke(self, name, state):
        state = ActionState(state)
        handlers = self._action_handlers.get(name)
        if handlers is not None:
            for handler in handlers:
                try:
                    handler(state)
                except:
                    traceback.print_exc()

EventActionMap = typed_string_map(text_type)

class InputEventBindings(JsonObjectWrapper):
    __slots__ = ()
    viewer = wrapped_property('viewer', EventActionMap)
    slice_view = sliceView = wrapped_property('sliceView', EventActionMap)
    perspective_view = perspectiveView = wrapped_property('perspectiveView', EventActionMap)
    data_view = dataView = wrapped_property('dataView', EventActionMap)

class ConfigState(JsonObjectWrapper):
    __slots__ = ()
    credentials = wrapped_property('credentials', typed_string_map(dict))
    actions = wrapped_property('actions', typed_set(text_type))
    input_event_bindings = inputEventBindings = wrapped_property('inputEventBindings', InputEventBindings)
    status_messages = statusMessages = wrapped_property('statusMessages', typed_string_map(text_type))

class PrivateState(JsonObjectWrapper):
    __slots__ = ()
    credentials = wrapped_property('credentials', typed_string_map(optional(int)))