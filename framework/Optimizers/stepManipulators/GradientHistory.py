# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
  Step size manipulations based on gradient history

  Created 2020-01
  @author: talbpaul
"""
#for future compatibility with Python 3--------------------------------------------------------------
from __future__ import division, print_function, unicode_literals, absolute_import
#End compatibility block for Python 3----------------------------------------------------------------

#External Modules------------------------------------------------------------------------------------
import abc
import numpy as np
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
from utils import InputData, InputTypes, mathUtils, randomUtils
from .StepManipulator import StepManipulator
from . import NoConstraintResolutionFound
#Internal Modules End--------------------------------------------------------------------------------

class GradientHistory(StepManipulator):
  """
    Changes step size depending on history of gradients
  """
  requiredInformation = ['gradientHist', 'prevStepSize']
  optionalInformation = ['recommend']

  ##########################
  # Initialization Methods #
  ##########################
  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, inputSpecification, InputData.ParameterInput, class to use for specifying input of cls.
    """
    specs = super(GradientHistory, cls).getInputSpecification()
    specs.addSub(InputData.parameterInputFactory('growthFactor', contentType=InputTypes.FloatType))
    specs.addSub(InputData.parameterInputFactory('shrinkFactor', contentType=InputTypes.FloatType))
    return specs

  def __init__(self):
    """
      Constructor.
      @ In, None
      @ Out, None
    """
    StepManipulator.__init__(self)
    # TODO
    ## Instance Variable Initialization
    # public
    # _protected
    self._optVars = None
    self._growth = 1.25
    self._shrink = 1.15
    self._minRotationAngle = 2.0 # how close to perpendicular should we try rotating towards?
    self._numRandomPerp = 10     # how many random perpendiculars should we try rotating towards?
    # __private
    # additional methods

  def handleInput(self, specs):
    """
      Read input specs
      @ In, specs, InputData.ParameterInput, parameter specs interpreted
      @ Out, None
    """
    #specs = specs
    growth = specs.findFirst('growthFactor')
    if growth is not None:
      self._growth = growth.value
    shrink = specs.findFirst('shrinkFactor')
    if shrink is not None:
      self._shrink = shrink.value

  def initialize(self, optVars, **kwargs):
    """ TODO """
    self._optVars = optVars
    StepManipulator.initialize(self, optVars, **kwargs)


  ###############
  # Run Methods #
  ###############
  def initialStepSize(self, numOptVars=None, scaling=0.05, **kwargs):
    """
      Provides an initial step size
      @ In, numOptVars, int, number of optimization variables
      @ In, scaling, float, optional, scaling factor
    """
    return mathUtils.hyperdiagonal(np.ones(numOptVars) * scaling)

  def step(self, prevOpt, gradientHist=None, prevStepSize=None, recommend=None, **kwargs):
    """
      calculates the step size and direction to take
      @ In, prevOpt, dict, previous opt point
      @ In, gradientHist, deque, list of gradient dictionaries with 0 being oldest; versors
      @ In, prevStepSize, deque, list of float step sizes
      @ In, recommend, str, optional, override to 'grow' or 'shrink' step size
      @ In, kwargs, dict, keyword-based specifics as required by individual step sizers
      @ Out, newOpt, dict, new opt point
      @ Out, stepSize, float, new step size
    """
    stepSize = self._stepSize(gradientHist=gradientHist, prevStepSize=prevStepSize,
                              recommend=recommend, **kwargs)
    gradient = gradientHist[-1][1]
    # use gradient, prev point, and step size to choose new point
    newOpt = {}
    for var in self._optVars:
      newOpt[var] = prevOpt[var] - stepSize * gradient[var]
    return newOpt, stepSize

  def fixConstraintViolations(self, proposed, previous, fixInfo):
    """
      Given constraint violations, update the desired optimal point to consider.
      @ In, proposed, dict, proposed new optimal point
      @ In, previous, dict, previous optimal point
      @ In, fixInfo, dict, contains record of progress in fixing search
      @ Out, proposed, new proposed point
      @ Out, stepSize, new step size taken # TODO need?
      @ Out, fixInfo, updated fixing info
    """
    # DESIGN
    # While not okay:
    # 1. See if cutting the step will fix it.
    # 2. If not, try rotating towards a random perpendicular. Repeat 1.
    # 3. If not, try a new random perpendicular. Repeat 1. Repeat N times.
    # TODO should this be specific to step manipulators, or something else?
    # TODO updating opt point in place! Is this safe?
    minStepSize = fixInfo['minStepSize']
    stepVector = dict((var, proposed[var] - previous[var]) for var in self._optVars)
    stepDistance, stepDirection, _ = mathUtils.calculateMagnitudeAndVersor(list(stepVector.values()))
    if 'originalStepSize' not in fixInfo:
      fixInfo['originalStepSize'] = stepDistance
    if 'perpDir' in fixInfo:
      perpDir = fixInfo['perpDir']
    # if not done cutting step, start cutting
    if stepDistance > minStepSize:
      # cut step again
      stepSize = 0.5 * stepDistance # TODO user option?
      for v, var in enumerate(stepVector):
        proposed[var] = previous[var] + stepSize * stepDirection[v]
      print(' ... cutting step ...') # norm step to {}, new norm opt {}'.format(stepSize, proposed))
      return proposed, stepSize, fixInfo
    else:
      ### rotate vector and restore full step size
      stepSize = fixInfo['originalStepSize']
      # store original direction
      if 'originalDirection' not in fixInfo:
        fixInfo['originalDirection'] = np.atleast_1d(stepDirection)
      # if this isn't the first time, check if there's angle left to rotate through; reset if not
      if 'perpDir' in fixInfo:
        ang = mathUtils.angleBetweenVectors(stepDirection, fixInfo['perpDir'])
        print(' ... trying angle:', ang)
        if ang < self._minRotationAngle:
          del fixInfo['perpDir']

      if 'perpDir' not in fixInfo:
        # find perpendicular vector
        perp = randomUtils.randomPerpendicularVector(fixInfo['originalDirection'])
        # NOTE we could return to point format, but no reason to
        # normalize perpendicular to versor and resize
        rotations = fixInfo.get('numRotations', 0)
        if rotations > self._numRandomPerp:
          raise NoConstraintResolutionFound
        _, perpDir, _ = mathUtils.calculateMagnitudeAndVersor(perp)
        fixInfo['perpDir'] = perpDir
        fixInfo['numRotations'] = rotations + 1
      # END fixing perpendicular direction
      # rotate vector halfway towards perpendicular
      perpDir = fixInfo['perpDir']

      # rotate towards selected perpendicular
      splitVector = {} # vector that evenly divides stepDirection and perp
      for v, var in enumerate(self._optVars):
        splitVector[var] = stepDirection[v] + perpDir[v]
        #splitVector[var] = - stepDirection[v] + perpDir[v]
      _, splitDir, _ = mathUtils.calculateMagnitudeAndVersor(list(splitVector.values()))
      for v, var in enumerate(self._optVars):
        proposed[var] = previous[var] + stepSize * splitDir[v]
      print(' ... rotating step ...') #ed norm direction to {}, new norm opt {}'.format(splitDir, proposed))
    return proposed, stepSize, fixInfo

  ###################
  # Utility Methods #
  ###################
  def _stepSize(self, gradientHist=None, prevStepSize=None, recommend=None, **kwargs):
    """
      Calculates a new step size to use in the optimization path.
      @ In, gradientHist, deque, list of gradient dictionaries with 0 being oldest; versors
      @ In, prevStepSize, deque, list of float step sizes
      @ In, recommend, str, optional, override to 'grow' or 'shrink' step size
      @ In, kwargs, dict, keyword-based specifics as required by individual step sizers
      @ Out, stepSize, float, new step size
    """
    # grad0 = gradientHist[-1][1]
    # grad1 = gradientHist[-2][1] if len(gradientHist) > 1 else None
    # FIXME try using the step directions instead
    step0 = prevStepSize[-1]['versor']
    if step0 is None:
      step0 = gradientHist[-1][1]
    step1 = prevStepSize[-2]['versor'] if len(prevStepSize) > 1 else None
    gainFactor = self._fractionalStepChange(step0, step1, recommend=recommend)
    # gainFactor = self._fractionalStepChange(grad0, grad1, recommend=recommend)
    stepSize = gainFactor * prevStepSize[-1]['magnitude']
    return stepSize

  def _fractionalStepChange(self, grad0, grad1, recommend=None):
    """
      Calculates fractional step change based on gradient history
      @ In, grad0, dict, most recent gradient direction (versor)
      @ In, grad1, dict, next recent gradient direction (versor)
      @ In, recommend, str, optional, can override gradient-based suggestion to either cut or grow
      @ Out, factor, multiplicitave factor to use on step size
    """
    assert grad0 is not None
    # grad1 can be None if only one point has been taken
    assert recommend in [None, 'shrink', 'grow']
    if recommend:
      if recommend == 'shrink':
        factor = 1. / self._shrink
      else:
        factor = self._growth
      return factor
    # if history is only a single gradient, then keep step size the same for now
    if grad1 is None:
      return 1.0
    # otherwise, figure it out based on the gradient history
    # scalar product
    prod = np.dot(grad0, grad1)
    # prod = np.sum([np.sum(grad0 * grad1) for v in grad0.keys()])
    if prod > 0:
      factor = self._growth ** prod
    else:
      # NOTE prod is negative, so this is like 1 / (shrink ^ abs(prod))
      factor = self._shrink ** prod
    return factor

