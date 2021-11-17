# Copyright 2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import pytest
from hypothesis import given, strategies as st, assume
from hypothesis.extra.numpy import arrays
from mrmustard.physics import gaussian
from mrmustard.lab.states import *
from mrmustard.lab.abstract import State
from mrmustard.lab.gates import *
from mrmustard import settings
from mrmustard.tests import random


@given(state=random.pure_state(num_modes=1), xy=random.vector(2))
def test_Dgate_1mode(state, xy):
    x, y = xy
    state_out = Dgate(x=x, y=y)(state)
    state_out = Dgate(x=-x, y=-y)(state_out)
    assert state_out == state


@given(state=random.pure_state(num_modes=2), xxyy=random.vector(4))
def test_Dgate_2mode(state, xxyy):
    x1, x2, y1, y2 = xxyy
    state_out = Dgate(x=[x1, x2], y=[y1, y2])(state)
    state_out = Dgate(x=[-x1, -x2], y=[-y1, -y2])(state_out)
    assert state_out == state


def test_1mode_fock_equals_gaussian():
    pass  # TODO: implement with weak states and gates
    # gate = Ggate(num_modes=1)  # too much squeezing probably
    # gstate = Gaussian(num_modes=1)  # too much squeezing probably
    # fstate = State(fock=gstate.ket(cutoffs=[40]), is_mixed=False)
    # via_phase_space = gate(gstate)
    # via_fock_space = gate(fstate)
    # assert via_phase_space == via_fock_space
