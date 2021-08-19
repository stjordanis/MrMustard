# MrMustard

[![Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue)](https://opensource.org/licenses/Apache-2.0)

MrMustard is a differentiable bridge between phase space and Fock space with rich functionality in both representations.

MrMustard supports:
- Phase space representation on an arbitrary number of modes and Fock representation (with mode-wise dimensionality cutoffs)
- Beam splitter, MZ interferometer, squeezer, displacement, phase rotation, general Gaussian N-mode gate, bosonic lossy channel, thermal channel, [more to come...]
- Photon number moments
- PNR detectors and threshold detectors with trainable quantum efficiency and dark counts
- Homodyne, Heterodyne and General-dyne measurements
- Symplectic optimization (with a spiffy progress bar)


## Basic API Reference

### 1: States
States in MrMustard are very powerful objects. They have differentiable methods to return a ket or density matrix in Fock space, covariance matrix and means vector in phase space, as well as photon number covariance and photon number means vector:
```python
from mrmustard import Vacuum, Coherent, SqueezedVacuum, DisplacedSqueezed, Thermal

vac = Vacuum(num_modes=2, hbar = 2.0)
coh = Coherent(x=[0.1, 0.2], y=[-0.4, 0.9], hbar=2.0)  # 2-mode coherent state
sq  = SqueezedVacuum(r = 0.5, phi = 0.3)
dsq = DisplacedSqueezed(r = 0.5, phi = 0.3, x = 0.3, y = 0.9, hbar=2.0)

# e.g. with coherent state
coh.ket(cutoffs=[4,5])
coh.dm(cutoffs=[4,5])

coh.cov   # phase space covariance matrix
coh.means # phase space means

coh.number_cov    # photon number covariance matrix
coh.number_means  # photon number means
```


### 2. Gates
Gates are callable objects. We have a variety of unitary Gaussian gates and non-unitary Gaussian channels.
Note that if a parameter of a single-mode gate is a float or a list of length 1 its value is shared across all the modes the gate is operating on.

```python
from mrmustard import Vacuum
from mrmustard import Dgate, Sgate, Rgate, LossChannel  # 1-mode gates / parallelizable
from mrmustard import BSgate, MZgate, S2gate  # 2-mode gates
from mrmustard import Ggate, Interferometer  # N-mode gates

# a single-mode squeezer with bounded squeezing magnitude
S = Sgate(modes = [0], r = 0.1, phi = 0.9, r_bounds=(0.0, 1.0))

# two single-mode displacements in parallel, with independent parameters:
D = Dgate(modes = [0, 1], x = [0.1, 0.2], y = [-0.5, 0.4])

# two single-mode displacements in parallel, with shared parameters:
D = Dgate(modes = [0, 1], x = 0.1, y = -0.5)

# a mix of shared and independent parameters is allowed
D = Dgate(modes = [0,1], x=0.2, y=[0.9, 1.9]))

# a lossy bosonic channel with constant transmissivity
L = LossChannel(modes = [0], transmissivity = 0.9, transmissivity_trainable = False)

# a generic gaussian transformation on 4 modes
G = Ggate(modes = [0,1,2,3])

G(Vacuum(4))  # output after Gaussian transformation
```


### 3: Circuits

In order to build a circuit we create an empty circuit object `circ = Circuit()` and append gates to it. 
Circuits are mutable sequences, which means they support all of the `list` methods (e.g. `circ.append(gate)`, `for gate in circ`, `some_gates = circ[1:4]`, `circ[6] = this_gate`, `circ.pop()`, etc...)

The circuit is callable as well: it takes a state object representing the input and it returns the output state:

```python
from mrmustard import Circuit, Vacuum, Sgate, Interferometer, LossChannel

modes = [0,1,2,3,4,5,6,7]

X8 = Circuit()
X8.append(Sgate(modes, r = 0.1, phi = np.random.normal(size=8)))  # shared squeezing magnitude and different phase
X8.append(LossChannel(modes, transmissivity=0.8))  # shared over all modes
X8.append(Interferometer(modes))
X8.append(LossChannel(modes, transmissivity=0.9))  # shared over all modes

X8(Vacuum(8))  # output state
```


### 4. Detectors
Even though the output of a detector is a probability distribution over the outcomes, even this operation is differentiable:

```python
from mrmustard.tools import Circuit
from mrmustard.states import Vacuum
from mrmustard.gates import Sgate, BSgate, LossChannel
from mrmustard.measurements import PNRDetector


circ = Circuit()
circ.append(Sgate(modes = [0,1], r=0.2, phi=[0.9,1.9]))  # a mix of shared and independent parameters is allowed
circ.append(BSgate(modes = [0,1], theta=1.4, phi=-0.1))
circ.append(LossChannel(modes=[0,1], transmissivity=0.5))

detector = PNRDetector(modes = [0,1], efficiency=0.9, dark_counts=0.01)

state_out = circ(Vacuum(num_modes=2))
detection_probs = detector(state_out, cutoffs=[2,3])
```

### 5. Optimization
The optimizer in MrMustard is a convenience class, which means that other optimizers can be used as all the transformations are differentiable with respect to the parameters of the gates. The only reason where you may want to use the optimizer is becasue it supports symplectic optimization for generic Gaussian transformations (`Ggate`), and it kicks-in automatically if there are `Ggate`s in the circuit.

Here we use a default TensorFlow optimizer (no `Ggate`s):
```python
import tensorflow as tf
from mrmustard.gates import Dgate, LossChannel
from mrmustard.states import Vacuum

displacement = Dgate(modes = [0], x = 0.1, y = -0.5, x_bounds=(0.0, 1.0), x_trainable=True, y_trainable=False)
loss = LossChannel(modes=[0], transmissivity=0.5, transmissivity_trainable=False)

def cost_fn():
    state_out = loss(displacement(Vacuum(num_modes=1)))
    return tf.abs(state_out.means[0] - 0.2)**2

adam = tf.optimizers.Adam(learning_rate=0.001)

from tqdm import trange
for i in trange(100):
    adam.minimize(cost_fn, displacement.euclidean_parameters)
```

Here we use MrMustard's optimizer because we have a `Ggate`:
```python
import tensorflow as tf
from mrmustard.tools import Circuit, Optimizer
from mrmustard.gates import Ggate, LossChannel
from mrmustard.states import Vacuum

circ = Circuit()

displacement = Ggate(modes = [0])  # Ggate and Interferometer are the only gates which automate parameter initialization
loss = LossChannel(modes=[0], transmissivity=0.5, transmissivity_trainable=False)
circ.append(displacement)
circ.append(loss)

def cost_fn():
    state_out = circ(Vacuum(num_modes=1))
    return tf.abs(state_out.means[1] - 0.1)**2

opt = Optimizer()
opt.minimize(cost_fn, by_optimizing=circ, max_steps=500) # the optimizer stops earlier if the loss is stable
```
